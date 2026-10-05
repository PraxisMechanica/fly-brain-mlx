import hashlib
import json
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from fly_brain.comparison.acceptance import evaluate_case
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.models import Connectome, InputPin, Stimulus

from .case_spikes import load
from .pending_queues import verify as verify_pending
from .replay_evidence import cpu as verify_cpu
from .replay_evidence import paired as verify_paired


def encode(value: object) -> dict[str, int | float]:
    if isinstance(value, Fraction):
        return {
            'numerator': value.numerator,
            'denominator': value.denominator,
            'value': float(value),
        }
    raise TypeError(type(value).__name__)


def write(
    case: ParityCase,
    connectome: Connectome,
    pin: InputPin,
    stimulus: Stimulus,
    observations: Path,
    output: Path,
) -> dict[str, object]:
    paired, cpu = observations / 'paired-first', observations / 'cpu-first'
    verify_paired(paired, observations / 'paired-repeat')
    verify_cpu(cpu, observations / 'cpu-repeat')
    spikes, native = load(connectome, case.steps, paired, cpu)
    causal = json.loads((paired / 'causal.json').read_text())
    pending = (
        verify_pending(paired, case.steps, len(connectome.sources))
        if causal['first_spike_step'] is None
        else None
    )
    experiment = EXPERIMENTS[case.experiment]
    checks = {
        'required_frozen_case': case in required_cases(),
        'input_geometry_equals_pin': len(connectome.neuron_ids) == pin.neurons
        and len(connectome.sources) == pin.edges,
        'canonical_stimulus_hash': hashlib.sha256(stimulus.events.tobytes()).hexdigest()
        == stimulus.sha256,
        'single_case_horizon_and_trial': stimulus.events.shape
        == (1, case.steps, len(stimulus.targets))
        and stimulus.trial_indices == (case.trial,),
        'prescribed_seed_generator_targets_and_rates': stimulus.seed == 20261004
        and stimulus.generator_code == experiment.generator_code
        and stimulus.rates_hz == experiment.rates_hz
        and tuple(int(connectome.neuron_ids[index]) for index in stimulus.targets)
        == experiment.activated_ids,
        'complete_common_history_budget_check': causal['steps'] == case.steps
        and causal['first_budget_violation'] is None,
        'first_different_spike_explicitly_none': causal['first_spike_step'] is None,
        'actual_final_pending_events_equal_when_history_is_common': pending is not None
        or causal['first_spike_step'] is not None,
    }
    acceptance = evaluate_case(
        spikes['brian'], spikes['mlx'], spikes['torch'], case.steps * 0.0001
    )
    with (output / 'normalized-spikes.npz').open('xb') as artifact:
        np.savez_compressed(
            artifact,
            **{
                engine + '_' + name: getattr(value, name)
                for engine, value in spikes.items()
                for name in ('neurons', 'steps')
            },
        )
    report: dict[str, object] = {
        'case': asdict(case),
        'case_accepted': acceptance.accepted and all(checks.values()),
        'full_matrix_accepted': False,
        'case_checks': checks,
        'metric_acceptance': asdict(acceptance),
        'native_inputs_before_conversion': native,
        'stimulus_sha256': stimulus.sha256,
        'input_pins': asdict(pin),
        'neuron_mapping_sha256': hashlib.sha256(
            connectome.neuron_ids.tobytes()
        ).hexdigest(),
        'causal': causal,
        'final_pending_original_row_counts': pending,
        'scientific_review_required': causal['first_spike_step'] is not None
        or causal['first_budget_violation'] is not None,
        'scope': 'One prescribed three-engine case. Full matrix, batch checks, aggregate reports and performance remain separate gates.',
    }
    with (output / 'case.json').open('x') as artifact:
        json.dump(report, artifact, indent=2, default=encode, allow_nan=False)
    return report
