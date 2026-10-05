import gc
import subprocess
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, cast

import brian2 as b
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.models import Connectome

from .brian_observer import install
from .brian_reference import default_parameters, silence_neurons
from .observer_stream import (
    PHASE_FIELDS,
    FinalSnapshot,
    PhaseBlock,
    StepSnapshot,
    StreamShape,
    read_frames,
)

Frame = StepSnapshot | PhaseBlock | FinalSnapshot
ResultArrays = dict[str, NDArray[np.float64 | np.int32 | np.int64 | np.bool_]]


@dataclass(frozen=True)
class BrianJob:
    directory: Path
    shape: StreamShape
    observed: bool
    files: dict[str, str]


def build(
    connectome: Connectome,
    targets: tuple[int, ...],
    silenced: tuple[int, ...],
    events: NDArray[np.uint8],
    directory: Path,
    block_size: int | None = 32,
) -> BrianJob:
    if events.ndim != 2 or events.shape[1] != len(targets) or not len(events):
        raise ValueError('Reference replay needs nonempty steps and matching channels')
    if events.dtype != np.uint8 or np.any(events > 1):
        raise ValueError('Reference replay requires canonical uint8 event bits')
    if block_size is not None and not 1 <= block_size <= 32:
        raise ValueError('Reference observation blocks must contain 1 to 32 steps')
    if b.__version__ != '2.8.0':
        raise RuntimeError('Reference jobs require pinned Brian2 2.8.0')
    if b.prefs.devices.cpp_standalone.openmp_threads != 0:
        raise RuntimeError('Reference jobs require the pinned single-thread queue')
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    b.device.reinit()
    b.set_device('cpp_standalone', build_on_run=False)
    b.start_scope()
    gc.collect()
    try:
        b.defaultclock.dt = 0.1 * b.ms
        params = default_parameters()
        group = b.NeuronGroup(
            len(connectome.neuron_ids),
            params['eqs'],
            method='linear',
            threshold=params['eq_th'],
            reset=params['eq_rst'],
            refractory='rfc',
            namespace=params,
            name='default_neurons',
        )
        group.v = params['v_0']
        group.g = 0 * b.mV
        group.lastspike = -100000000 * 0.1 * b.ms
        refractory = np.full(len(connectome.neuron_ids), 2.2)
        refractory[list(targets)] = 0
        group.rfc = refractory * b.ms
        objects: list[b.BrianObject] = [group]
        pathways: list[b.Synapses] = []
        if len(connectome.sources):
            recurrent = b.Synapses(
                group,
                group,
                'w : volt',
                on_pre='g += w',
                delay=params['t_dly'],
                name='default_synapses',
            )
            recurrent.connect(i=connectome.sources, j=connectome.destinations)
            recurrent.w = connectome.counts * params['w_syn']
            silence_neurons(recurrent, silenced)
            pathways.append(recurrent)
            objects.append(recurrent)
        source = None
        if targets:
            steps, channels = np.nonzero(events)
            source = b.SpikeGeneratorGroup(
                len(targets), channels, steps * 0.1 * b.ms, name='replay_source'
            )
            inputs = b.Synapses(
                source, group, on_pre='v += 68.75*mV', name='replay_input'
            )
            inputs.connect(i=np.arange(len(targets)), j=np.asarray(targets))
            inputs.pre.order = 0
            pathways.append(inputs)
            objects.extend((source, inputs))
        monitors: tuple[b.StateMonitor, ...] = ()
        if block_size is not None:
            monitors = tuple(
                b.StateMonitor(
                    group,
                    names,
                    record=True,
                    when=when,
                    order=order,
                    name='reference_' + phase,
                )
                for (phase, names), (when, order) in zip(
                    PHASE_FIELDS,
                    (('thresholds', -1), ('resets', -1), ('end', 0)),
                    strict=True,
                )
            )
        spikes = b.SpikeMonitor(group, name='reference_spikes')
        network = b.Network(*objects, *monitors, spikes, name='reference_network')
        shape = StreamShape(
            len(connectome.neuron_ids),
            len(events),
            len(targets),
            tuple(size for size in (len(connectome.sources), len(targets)) if size),
            block_size or 0,
        )
        if block_size is not None:
            install(network, group, source, tuple(pathways), monitors, shape)
        network.run(len(events) * 0.1 * b.ms)
        variables = {
            **{
                name: group.variables[name]
                for name in ('v', 'g', 'lastspike', 'not_refractory')
            },
            'spike_i': spikes.variables['i'],
            'spike_t': spikes.variables['t'],
            'clock_step': b.defaultclock.variables['timestep'],
            'clock_t': b.defaultclock.variables['t'],
        }
        if source is not None:
            variables['source_cursor'] = source.variables['_lastindex']
        if len(connectome.sources):
            variables['weights'] = pathways[0].variables['w']
        for name in ('v', 'g', 'lastspike', 'spike_t', 'clock_t'):
            if variables[name].dtype != np.float64:
                raise RuntimeError(
                    'Reference jobs require native float64 state and time'
                )
        files = {
            name: b.device.get_array_filename(variable)
            for name, variable in variables.items()
        }
        b.prefs.devices.cpp_standalone.extra_make_args_unix = ['-j2']
        b.device.build(
            directory=str(directory), clean=False, with_output=False, run=False
        )
        if (
            '-O3 -ffast-math -fno-finite-math-only'
            not in (directory / 'makefile').read_text()
        ):
            raise RuntimeError(
                'Reference compiler flags differ from the frozen baseline'
            )
        return BrianJob(directory, shape, block_size is not None, files)
    finally:
        b.device.reinit()
        b.set_device('runtime')


def run(job: BrianJob, destination: Path) -> Generator[Frame, None, None]:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / 'stderr.log').open('xb') as errors:
        process = subprocess.Popen(
            [str(job.directory / 'main'), '--results_dir', str(destination) + '/'],
            cwd=job.directory,
            stdout=subprocess.PIPE,
            stderr=errors,
        )
        assert process.stdout is not None
        try:
            if job.observed:
                yield from read_frames(cast(BinaryIO, process.stdout), job.shape)
            elif process.stdout.read(1):
                raise ValueError('Ordinary reference execution wrote unexpected stdout')
            returncode = process.wait()
            if returncode:
                raise RuntimeError(
                    f'Reference execution exited {returncode}; see {destination / "stderr.log"}'
                )
        finally:
            process.stdout.close()
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def results(job: BrianJob, directory: Path) -> ResultArrays:
    values: ResultArrays = {}
    for name in ('v', 'g', 'lastspike', 'not_refractory'):
        data = np.fromfile(
            directory / job.files[name],
            dtype=np.bool_ if name == 'not_refractory' else np.float64,
        )
        if data.size != job.shape.neurons:
            raise ValueError('Reference final state has the wrong neuron count')
        values[name] = data
    values['spike_i'] = np.fromfile(directory / job.files['spike_i'], dtype=np.int32)
    values['spike_t'] = np.fromfile(directory / job.files['spike_t'], dtype=np.float64)
    values['clock_step'] = np.fromfile(
        directory / job.files['clock_step'], dtype=np.int64
    )
    values['clock_t'] = np.fromfile(directory / job.files['clock_t'], dtype=np.float64)
    if 'source_cursor' in job.files:
        values['source_cursor'] = np.fromfile(
            directory / job.files['source_cursor'], dtype=np.int32
        )
    return values
