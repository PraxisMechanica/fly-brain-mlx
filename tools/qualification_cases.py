"""Validate original case evidence before matrix reuse or batch consumption."""

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from fly_brain.comparison.acceptance import (
    evaluate_case,
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.qualification.adapters.batch_environment import read_environment
from fly_brain.qualification.adapters.batch_stimulus import load as load_stimulus
from fly_brain.qualification.adapters.case_binding import (
    require_bound_files,
    require_cause_binding,
    scientific_files,
)
from fly_brain.qualification.adapters.case_replay import require_complete_replay
from fly_brain.qualification.adapters.case_spikes import load as load_spikes
from fly_brain.qualification.adapters.pending_queues import verify as verify_pending
from fly_brain.qualification.adjudication import CASE_CHECKS, require_reviewable
from fly_brain.qualification.causality import CausalAudit
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.matrix_diagnostics import CaseRasters
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.rounding_review import require_rounding_prerequisites
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.models import Connectome, InputPin
from fly_brain.simulation.stimulus_service import read_experiment


def case_name(case: ParityCase) -> str:
    return f'{case.experiment}-{case.steps}-{case.trial}'


@dataclass(frozen=True)
class CaseEntry:
    directory: Path
    exit_code: int
    artifact_sha256: dict[str, str] | None
    review: Path | None
    review_sha256: dict[str, str]


def read_index(path: Path) -> dict[ParityCase, CaseEntry]:
    report = json.loads(path.read_text())
    rows = report['cases']
    required = required_cases()
    if report['required_cases'] != len(required) or [row['case'] for row in rows] != [
        asdict(case) for case in required[: len(rows)]
    ]:
        raise ValueError('Case index must contain a unique prescribed matrix prefix')
    result: dict[ParityCase, CaseEntry] = {}
    for case, row in zip(required, rows, strict=False):
        result[case] = CaseEntry(
            Path(row['directory']).resolve()
            if row.get('directory')
            else path.parent.resolve() / 'cases' / case_name(case),
            row['exit_code'],
            row.get('artifact_sha256'),
            Path(row['review_directory']).resolve()
            if row.get('review_directory')
            else None,
            row.get('review_artifact_sha256', {}),
        )
    return result


@dataclass(frozen=True)
class VerifiedCase:
    directory: Path
    launch: str
    rasters: CaseRasters
    accepted: bool
    artifact_sha256: dict[str, str]
    review: Path | None
    review_sha256: dict[str, str]

    def record(self) -> dict[str, object]:
        return {
            'case': asdict(self.rasters.case),
            'directory': str(self.directory),
            'launch_commit': self.launch,
            'accepted': self.accepted,
            'artifact_sha256': self.artifact_sha256,
            'review_directory': str(self.review) if self.review is not None else None,
            'review_artifact_sha256': self.review_sha256,
        }


def verify_case(
    project: Path,
    directory: Path,
    case: ParityCase,
    connectome: Connectome,
    pin: InputPin,
    *,
    canonical_sha256: str,
    review: Path | None = None,
    bound_files: dict[str, str] | None = None,
) -> VerifiedCase:
    directory = directory.resolve()
    report = json.loads((directory / 'case.json').read_text())
    if case not in required_cases() or report['case'] != asdict(case):
        raise ValueError('Recorded case identity differs from its prescribed case')
    checks = report['case_checks']
    if frozenset(checks) != CASE_CHECKS or any(
        type(value) is not bool for value in checks.values()
    ):
        raise ValueError('Case requires every explicit scientific check')
    if (
        report['input_pins'] != asdict(pin)
        or report['neuron_mapping_sha256']
        != hashlib.sha256(connectome.neuron_ids.tobytes()).hexdigest()
    ):
        raise ValueError('Case input pins or neuron mapping differ')
    stimulus = load_stimulus(directory, read_experiment(case.experiment), pin)
    if (
        stimulus.sha256 != canonical_sha256
        or report['stimulus_sha256'] != canonical_sha256
        or stimulus.seed != 20261004
        or stimulus.trial_indices != (case.trial,)
        or stimulus.events.shape != (1, case.steps, len(stimulus.targets))
        or tuple(int(connectome.neuron_ids[index]) for index in stimulus.targets)
        != read_experiment(case.experiment).activated_ids
    ):
        raise ValueError('Engine case input differs from canonical preflight')
    launch = json.loads((directory / 'launch.json').read_text())['commit']

    def read_launch(commit: str, path: str) -> bytes:
        return subprocess.check_output(
            ['git', '-C', str(project), 'show', commit + ':' + path]
        )

    read_environment(project, (directory, launch), read_launch)
    require_complete_replay(directory, case.steps)
    paired = directory / 'observations/paired-first'
    causal = json.loads((paired / 'causal.json').read_text())
    if report['causal'] != causal or (
        checks['complete_common_history_budget_check']
        is not (
            causal['steps'] == case.steps and causal['first_budget_violation'] is None
        )
        or checks['first_different_spike_explicitly_none']
        is not (causal['first_spike_step'] is None)
    ):
        raise ValueError('Case gates differ from original native causal evidence')
    if causal['first_spike_step'] is None and (
        causal['first_spike_neurons']
        or report['final_pending_original_row_counts']
        != list(verify_pending(paired, case.steps, len(connectome.sources)))
    ):
        raise ValueError('Case final pending events differ from native evidence')
    spikes, _ = load_spikes(
        connectome,
        case.steps,
        paired,
        directory / 'observations/cpu-first',
        validate=validate_coordinates,
        convert_clock=steps_from_reference_clock,
    )
    with np.load(directory / 'normalized-spikes.npz', allow_pickle=False) as saved:
        expected = {
            engine + '_' + field: getattr(value, field)
            for engine, value in spikes.items()
            for field in ('neurons', 'steps')
        }
        if set(saved.files) != set(expected) or any(
            saved[name].dtype != value.dtype or not np.array_equal(saved[name], value)
            for name, value in expected.items()
        ):
            raise ValueError('Normalized spikes differ from native rescoring inputs')
    measured = evaluate_case(
        spikes['brian'], spikes['mlx'], spikes['torch'], case.steps * 0.0001
    )
    if measured.checks != report['metric_acceptance']['checks']:
        raise ValueError('Recorded metric gates differ from native rescoring')
    raw_accepted = measured.accepted and all(checks.values())
    if report['case_accepted'] is not raw_accepted:
        raise ValueError('Raw case acceptance differs from its scientific gates')
    manifest = (
        bound_files
        if bound_files is not None
        else {
            str(path.relative_to(directory)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in scientific_files(directory)
        }
    )
    require_bound_files(
        directory, manifest, has_spike_context=causal['first_spike_step'] is not None
    )
    review_hashes: dict[str, str] = {}
    if (
        not raw_accepted
        and review is not None
        and (review / 'review-decision.json').is_file()
    ):
        if causal['first_budget_violation'] is not None:
            raise ValueError('A causal review cannot waive a state-budget violation')
        audit = CausalAudit(
            step=causal['steps'],
            first_spike_step=causal['first_spike_step'],
            first_spike_neurons=tuple(map(NeuronRow, causal['first_spike_neurons'])),
        )
        require_reviewable(case, checks, measured.checks, audit)
        with np.load(paired / 'spike-context.npz', allow_pickle=False) as context:
            available = context['current_reference_pre_not_refractory']
            reference_spikes = np.zeros(available.shape, dtype=np.bool_)
            indices = context['current_reference_spikes']
            if (
                indices.dtype != np.int32
                or indices.ndim != 1
                or np.any(indices < 0)
                or np.any(indices >= len(available))
            ):
                raise ValueError(
                    'Cause requires native in-range reference spike indices'
                )
            reference_spikes[indices] = True
            require_rounding_prerequisites(
                context['current_reference_pre_v'],
                context['current_mlx_pre_v'],
                available,
                context['current_mlx_pre_not_refractory'],
                reference_spikes,
                context['current_mlx_spikes'],
                audit.first_spike_neurons,
            )
        review_hashes = require_cause_binding(directory, review, case, audit, launch)
    return VerifiedCase(
        directory,
        launch,
        CaseRasters(case, spikes['brian'], spikes['mlx'], spikes['torch']),
        raw_accepted or bool(review_hashes),
        manifest,
        review,
        review_hashes,
    )
