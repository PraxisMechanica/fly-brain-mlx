"""Fresh canonical singleton trial for the bounded statistical campaign."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter, time_ns
from typing import Literal, cast

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.models import ExperimentName

Engine = Literal['brian', 'mlx']


@dataclass(frozen=True)
class Job:
    engine: Engine
    experiment: ExperimentName
    trial: int
    steps: int = 10000

    def __post_init__(self) -> None:
        if (
            self.engine not in ('brian', 'mlx')
            or type(self.trial) is not int
            or type(self.steps) is not int
            or self.trial < 0
            or self.steps < 1
        ):
            raise ValueError(
                'Trial requires a supported engine and integer horizon/seed'
            )

    @property
    def name(self) -> str:
        return f'{self.engine}-{self.experiment}-{self.steps}-{self.trial}'


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as source:
        while block := source.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def package_versions(engine: Engine) -> dict[str, str]:
    names = ('numpy', 'pyarrow') + (
        ('brian2', 'cython', 'sympy') if engine == 'brian' else ('mlx', 'mlx-metal')
    )
    return {name: importlib.metadata.version(name) for name in names}


def require_loaded_sources(project: Path, identity: dict[str, str]) -> None:
    for name, module in tuple(sys.modules.items()):
        if not (
            name == 'fly_brain'
            or name.startswith('fly_brain.')
            or name
            in (
                'tools.tiered_trial',
                'tools.campaign_resources',
                'tools.run_tiered_campaign',
            )
        ):
            continue
        filename = getattr(module, '__file__', None)
        if filename is None:
            raise ValueError('Loaded project module has no source identity: ' + name)
        path = Path(filename).resolve()
        if not path.is_relative_to(project) or identity.get(
            str(path.relative_to(project))
        ) != digest(path):
            raise ValueError('Loaded code differs from the requested checkout: ' + name)


def sources(project: Path) -> dict[str, str]:
    paths = sorted((project / 'src').rglob('*.py'))
    paths.extend(
        project / name
        for name in (
            'uv.lock',
            'pyproject.toml',
            'tools/campaign_resources.py',
            'tools/tiered_trial.py',
            'tools/run_tiered_campaign.py',
        )
    )
    return {str(path.relative_to(project)): digest(path) for path in paths}


def run(job: Job, project: Path, output: Path) -> dict[str, object]:
    started = perf_counter()
    import pyarrow as pa

    from fly_brain.bootstrap import pinned_inputs
    from fly_brain.comparison.acceptance import (
        steps_from_reference_clock,
        validate_coordinates,
    )
    from fly_brain.comparison.models import SpikeSteps
    from fly_brain.infrastructure.output_paths import require_retained_output
    from fly_brain.infrastructure.seeded_random import uniforms
    from fly_brain.qualification.adapters.batch_stimulus import load
    from fly_brain.simulation.identifiers import NeuronRows64, TrialId
    from fly_brain.simulation.stimuli import neuron_indices
    from fly_brain.simulation.stimulus_service import read_experiment, schedule
    from fly_brain.simulation.storage import persist_stimulus

    require_retained_output(output.resolve(), project)
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    if job.steps < 1 or job.trial < 0 or np.__version__ != '1.26.4':
        raise ValueError('Trial requires positive steps and pinned NumPy')
    identity = sources(project)
    if Path(__file__).resolve() != project / 'tools/tiered_trial.py':
        raise ValueError('Worker was imported from a different checkout')
    require_loaded_sources(project, identity)
    connectome, pin = pinned_inputs()(project)
    experiment = read_experiment(job.experiment)
    stimulus = schedule(
        connectome,
        experiment,
        job.steps,
        (TrialId(job.trial),),
        20261004,
        draw_uniforms=uniforms,
    )
    persist_stimulus(output, experiment, pin, stimulus)
    stimulus = load(output, experiment, pin)
    silenced = neuron_indices(connectome, experiment.silenced_ids)
    prepared = perf_counter()
    device_peak = 0
    execution_identity = {
        'python_executable': digest(Path(sys.executable).resolve()),
        'python': sys.version,
        'platform': platform.platform(),
        'versions': json.dumps(package_versions(job.engine), sort_keys=True),
        'threads': json.dumps(
            {
                name: os.environ.get(name)
                for name in (
                    'OMP_NUM_THREADS',
                    'OPENBLAS_NUM_THREADS',
                    'MKL_NUM_THREADS',
                    'VECLIB_MAXIMUM_THREADS',
                    'NUMEXPR_NUM_THREADS',
                    'MLX_ENABLE_TF32',
                )
            },
            sort_keys=True,
        ),
        'os_build': subprocess.check_output(
            ('sw_vers', '-buildVersion'), text=True
        ).strip(),
    }
    extra: dict[str, object] = {}
    if job.engine == 'brian':
        from fly_brain.qualification.adapters import brian_jobs
        from fly_brain.qualification.adapters.reference_build import (
            command,
            consumed_dependencies,
        )
        from fly_brain.qualification.adapters.reference_identity import (
            create,
            installed_packages,
        )

        reference_packages = installed_packages()
        build_started_ns = time_ns()
        reference = brian_jobs.build(
            connectome,
            stimulus.targets,
            silenced,
            stimulus.events[0],
            output / 'reference-build',
            block_size=None,
        )
        built = perf_counter()
        if tuple(brian_jobs.run(reference, output / 'reference-native')):
            raise ValueError('Unobserved reference unexpectedly emitted phase frames')
        simulated = perf_counter()
        native = brian_jobs.results(reference, output / 'reference-native')
        if native['clock_step'].tolist() != [job.steps]:
            raise ValueError('Reference did not finish the prescribed horizon')
        rows = native['spike_i'].astype(np.int64)
        steps = steps_from_reference_clock(
            cast(NDArray[np.float64], native['spike_t']), job.steps
        )
        np.savez_compressed(output / 'native-final.npz', **native)
        extra['reference_files'] = reference.files
        dependencies = consumed_dependencies(reference.directory, build_started_ns)
        if installed_packages() != reference_packages:
            raise ValueError(
                'Installed reference dependencies changed during execution'
            )
        producer, binding = create(
            connectome,
            stimulus,
            silenced,
            reference.shape,
            reference.files,
            reference.directory,
            {
                'dependencies': dependencies,
                'packages': reference_packages,
                'python': sys.version,
                'python_executable_sha256': digest(Path(sys.executable).resolve()),
                'platform': platform.platform(),
                'os_build': command('sw_vers', '-buildVersion'),
                'scope': 'Actual generated/static inputs, executable, compiler, headers and runtime bindings; supports framework and standalone uv interpreters.',
            },
        )
        with (output / 'reference-job.json').open('x') as destination:
            destination.write(json.dumps(binding, indent=2, allow_nan=False) + '\n')
        extra['reference_producer_digest'] = str(producer)
        extra['reference_executable_sha256'] = digest(reference.directory / 'main')
        execution_identity['reference_packages'] = hashlib.sha256(
            json.dumps(reference_packages, sort_keys=True).encode()
        ).hexdigest()
        execution_identity['reference_toolchain'] = hashlib.sha256(
            json.dumps(
                {
                    name: value
                    for name, value in dependencies.items()
                    if name != 'consumed_headers' and name != 'resolved_commands'
                },
                sort_keys=True,
            ).encode()
            + json.dumps(
                {
                    name: cast(dict[str, str], dependencies['resolved_commands'])[name]
                    for name in ('COMPILE', 'LINK')
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        execution_identity['os_build'] = command('sw_vers', '-buildVersion')
        timings = {'setup_s': built - prepared, 'simulation_s': simulated - built}
    else:
        from fly_brain.bootstrap import configure_mlx

        precision = configure_mlx()
        from fly_brain.simulation.backend.runner import run as execute

        result = execute(connectome, stimulus, silenced, precision=precision)
        simulated = perf_counter()
        rows, steps = result.spikes.neurons, result.spikes.steps
        device_peak = result.peak_device_bytes
        if np.any(result.spikes.trials != job.trial):
            raise ValueError('GPU result contains a different trial identity')
        extra['device'] = result.device_name
        extra['MLX_ENABLE_TF32'] = precision
        extra['compilation'] = 'disabled'
        import mlx.core as mx

        execution_identity['device'] = json.dumps(mx.device_info(), sort_keys=True)
        timings = {**result.timings, 'engine_wall_s': simulated - prepared}
    validate_coordinates(
        SpikeSteps(NeuronRows64(rows), steps), len(connectome.neuron_ids), job.steps
    )
    if len(set(zip(map(int, rows), map(int, steps), strict=True))) != len(rows):
        raise ValueError('Duplicate trial spike coordinates')
    if job.experiment == 'silent' and len(rows):
        raise ValueError('Silent configuration emitted spikes')
    counts = np.bincount(rows, minlength=len(connectome.neuron_ids)).astype(np.int64)
    np.savez_compressed(
        output / 'spikes.npz',
        neuron_ids=connectome.neuron_ids,
        neuron_rows=rows,
        steps=steps,
        counts=counts,
    )
    if identity != sources(project):
        raise ValueError('Campaign sources changed during the trial')
    require_loaded_sources(project, identity)
    self_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    child_peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    report: dict[str, object] = {
        'completed': True,
        'job': asdict(job),
        'input_pin': asdict(pin),
        'stimulus_sha256': stimulus.sha256,
        'seed': 20261004,
        'source_sha256': identity,
        'python': sys.version,
        'platform': platform.platform(),
        'effective_thread_environment': {
            name: os.environ.get(name)
            for name in (
                'OMP_NUM_THREADS',
                'OPENBLAS_NUM_THREADS',
                'MKL_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS',
                'NUMEXPR_NUM_THREADS',
                'MLX_ENABLE_TF32',
            )
        },
        'arrow_cpu_threads': pa.cpu_count(),
        'arrow_io_threads': pa.io_thread_count(),
        'python_executable_sha256': digest(Path(sys.executable).resolve()),
        'versions': package_versions(job.engine),
        'execution_identity': execution_identity,
        'commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=project, text=True
        ).strip(),
        'timings': {'input_s': prepared - started, **timings},
        'elapsed_s': perf_counter() - started,
        'spikes': len(rows),
        'active_neurons': int(np.count_nonzero(counts)),
        'self_peak_rss_bytes': self_peak,
        'children_peak_rss_bytes': child_peak,
        'mlx_peak_allocation_bytes': device_peak,
        'memory_envelope_bytes': self_peak + 2 * child_peak + device_peak,
        'memory_scope': 'Conservative summed RSS/child/compiler/device envelope; shared pages may be counted twice. Not simultaneous process-tree RSS.',
        'artifact_sha256': {
            str(path.relative_to(output)): digest(path)
            for path in output.rglob('*')
            if path.is_file()
        },
        'scope': 'Unobserved statistical singleton, not full state/queue/causal or matrix acceptance.',
        **extra,
    }
    with (output / 'trial.json').open('x') as destination:
        destination.write(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--job', required=True)
    args = parser.parse_args()
    run(Job(**json.loads(args.job)), args.project.resolve(), args.output.resolve())
