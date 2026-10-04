from collections.abc import Sequence
from dataclasses import dataclass

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.adapters.brian_replay import run_reference
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import as_host, boolean_input, evaluate
from fly_brain.simulation.backend.engines import Compiler
from fly_brain.simulation.models import NetworkCase as Case

from .artifacts import ArtifactRecorder, TraceArrays

BoolArray = NDArray[np.bool_]


def events_for(
    case: Case, steps: int, impulses: Sequence[tuple[int, int]] = (), trials: int = 1
) -> BoolArray:
    events = np.zeros((steps, trials, len(case.targets)), dtype=np.bool_)
    for step, channel in impulses:
        events[step, :, channel] = True
    return events


def replay_events(steps: int = 1000, trials: int = 1) -> BoolArray:
    return np.stack(
        [
            (
                np.random.Generator(
                    np.random.PCG64(np.random.SeedSequence([20261004, 2, trial]))
                ).random((steps, 3), dtype=np.float64)
                < np.array([200, 100, 0]) * 1e-4
            )
            for trial in range(trials)
        ],
        axis=1,
    )


@dataclass
class Harness:
    compile: Compiler
    recorder: ArtifactRecorder

    def network_for(self, case: Case) -> core.Network:
        return self.compile(case).network

    def run_candidate(
        self, case: Case, events: BoolArray, chunks: Sequence[int] | None = None
    ) -> TraceArrays:
        execution = self.compile(case)
        network = execution.network
        state = core.initial_state(
            network, events.shape[1], case.voltage, case.synaptic, case.last_spike
        )
        with mx.stream(mx.gpu):
            inputs = boolean_input(events)
        rows: dict[str, list[mx.array]] = {name: [] for name in core.StepTrace._fields}
        rows.update({name: [] for name in core.State._fields[:-1]})
        for length in chunks or [len(events)]:
            end = state.step + length
            while state.step < end:
                with mx.stream(mx.gpu):
                    state, trace = execution.advance(state, inputs[state.step])
                    evaluate(*state[:-1], *trace)
                for name, value in zip(core.StepTrace._fields, trace, strict=True):
                    rows[name].append(value)
                for name, value in zip(
                    core.State._fields[:-1], state[:-1], strict=True
                ):
                    rows[name].append(value)
        assert state.step == len(events)
        with mx.stream(mx.gpu):
            arrays = {name: mx.stack(values) for name, values in rows.items()}
            evaluate(*arrays.values())
        result = {name: as_host(value) for name, value in arrays.items()}
        result['queue'] = np.swapaxes(result['queue'], 1, 2)
        return result

    def qualify(self, name: str, case: Case, events: BoolArray) -> TraceArrays:
        expected = run_reference(case, events)
        observed = self.run_candidate(case, events)
        errors = {}
        for key, wanted in expected.items():
            actual = observed[key]
            if key.endswith('_mv'):
                assert np.all(np.isfinite(actual))
                error = np.abs(
                    np.asarray(actual, dtype=np.float64)
                    - np.asarray(wanted, dtype=np.float64)
                )
                budget = 1e-3 + 1e-5 * np.abs(wanted)
                assert np.all(error <= budget), (
                    name,
                    key,
                    np.unravel_index(error.argmax(), error.shape),
                )
                errors[key] = float(error.max(initial=0))
            else:
                np.testing.assert_array_equal(actual, wanted, err_msg=f'{name}: {key}')
        margin = np.abs(np.asarray(expected['pre_voltage_mv'], dtype=np.float64) + 45)
        budget = 1e-3 + 1e-5 * np.abs(expected['pre_voltage_mv'])
        assert np.all(
            margin[expected['available'].astype(np.bool_)]
            > budget[expected['available'].astype(np.bool_)]
        )
        assert np.max(np.abs(expected['voltage_mv'])) <= 256
        assert np.max(np.abs(expected['synaptic_mv'])) <= 1024
        for neuron in range(case.neurons):
            assert sum(destination == neuron for destination in case.destinations) <= 32
        repeat = self.run_candidate(case, events)
        for key, value in observed.items():
            np.testing.assert_array_equal(
                value, repeat[key], err_msg=f'{name}: repeat {key}'
            )
        self.recorder.record(
            name,
            {
                **{f'reference_{key}': value for key, value in expected.items()},
                **{f'mlx_{key}': value for key, value in observed.items()},
                'events': events,
            },
            {
                'steps': len(events),
                'trials': events.shape[1],
                'spikes': int(observed['spikes'].sum()),
                'max_abs_error_mv': errors,
                'exact_discrete_parity': True,
                'repeat_bit_identical': True,
                'minimum_available_threshold_margin_mv': float(
                    margin[expected['available'].astype(np.bool_)].min(initial=np.inf)
                ),
            },
        )
        return observed
