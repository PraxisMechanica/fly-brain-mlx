import json
from dataclasses import asdict
from functools import partial
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.bucketed import Layout
from fly_brain.simulation.backend.engines import Execution
from fly_brain.simulation.models import Connectome, Stimulus

from .brian_jobs import BrianJob
from .causal_artifacts import write_context
from .causal_capture import CausalCapture
from .causal_reduction import reduction_inputs


def write(
    capture: CausalCapture,
    job: BrianJob,
    execution: Execution,
    connectome: Connectome,
    stimulus: Stimulus,
    output: Path,
) -> None:
    contexts: dict[str, object] = {}
    for label, context in (('budget', capture.budget), ('spike', capture.spike)):
        if context is None:
            contexts[label] = None
            continue
        layout = cast(
            Layout,
            cast(partial[tuple[core.State, core.StepTrace]], execution.advance).args[1],
        )
        weights = (
            cast(
                NDArray[np.float64],
                np.memmap(
                    output / 'reference-results' / job.files['weights'],
                    dtype=np.float64,
                    mode='r',
                ),
            )
            if len(connectome.sources)
            else np.empty(0, dtype=np.float64)
        )
        arrays = reduction_inputs(layout, context.neurons, weights)
        arrays['stimulus_targets'] = np.asarray(stimulus.targets, dtype=np.int32)
        arrays['affected_neuron_ids'] = connectome.neuron_ids[
            list(context.neurons)
        ].copy()
        for position, observed in (
            ('current', context.current),
            ('previous', context.previous),
        ):
            if observed is not None:
                arrays[position + '_stimulus_bits'] = stimulus.events[
                    0, observed.snapshot.step
                ].copy()
        record = write_context(output / (label + '-context.npz'), context, arrays)
        record['threshold_margins_mv'] = [
            {
                'neuron': neuron,
                'reference': (float(context.current.reference['pre_v'][neuron]) + 0.045)
                * 1000,
                'mlx': float(context.current.mlx['pre_v'][neuron]) + 45,
            }
            for neuron in context.neurons
        ]
        contexts[label] = record
    violation = capture.audit.first_budget_violation
    with (output / 'causal.json').open('x') as artifact:
        json.dump(
            {
                'steps': capture.audit.step,
                'first_budget_violation': asdict(violation)
                if violation is not None
                else None,
                'first_spike_step': capture.audit.first_spike_step,
                'first_spike_neurons': list(capture.audit.first_spike_neurons),
                'contexts': contexts,
                'reduction_order': 'Actual padded leaf order; adjacent-pair compensated integer-count tree; four high/low scale products; 16-leaf compensated final tree.',
            },
            artifact,
            indent=2,
            allow_nan=False,
        )
