import numpy as np
import pytest

from fly_brain.simulation.models import Stimulus
from tests.qualification.test_mlx_observer import fixture
from tests.support.session_pinned import (
    BlockProof,
    NativeValue,
    TrialProof,
    record_mode,
    require_same_trial,
    value_signature,
)
from tests.support.session_proof_values import proof_root


def native_control() -> BlockProof:
    queue = np.array([True, False], dtype=np.bool_)
    trial = TrialProof(
        fields={'spikes': value_signature(queue.reshape(1, 1, 2))},
        due_edges=(value_signature(np.array([0], dtype=np.int32)),),
        due_sha256=('actual-due',),
        queue=value_signature(np.broadcast_to(queue, (19, 1, 2))),
        queue_slot_sha256=('actual-slot',) * 19,
    )
    return BlockProof(
        begin=0,
        rows=1,
        trials=(0,),
        units={'spikes': 'Boolean'},
        by_trial={'0': trial},
        measured_checks=True,
        checks_all=True,
        artifact_sha256='actual-file',
        queue_artifact_sha256='actual-queue-file',
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    'fault',
    ('bytes', 'dtype', 'shape', 'field', 'due', 'slot', 'trial', 'order', 'checks'),
)
def test_artifact_integrity_rejects_incomplete_or_corrupt_native_evidence(
    fault: str,
) -> None:
    original = native_control()
    require_same_trial(original, original, 0)
    changed = original.model_dump()
    if fault == 'trial':
        changed['by_trial'] = {}
    elif fault == 'order':
        changed['begin'] = 1
    elif fault == 'checks':
        changed['checks_all'] = False
    else:
        trial = original.by_trial['0']
        if fault == 'due':
            updated = trial.model_copy(update={'due_sha256': ('omitted',)})
        elif fault == 'slot':
            updated = trial.model_copy(update={'queue_slot_sha256': ('wrong',) * 19})
        elif fault == 'field':
            updated = trial.model_copy(update={'fields': {}})
        else:
            value = trial.fields['spikes']
            altered = NativeValue(
                dtype='|u1' if fault == 'dtype' else value.dtype,
                shape=(1, 2, 1) if fault == 'shape' else value.shape,
                sha256='wrong-bytes' if fault == 'bytes' else value.sha256,
            )
            updated = trial.model_copy(update={'fields': {'spikes': altered}})
        changed['by_trial'] = {'0': updated.model_dump()}
    with pytest.raises(ValueError, match='Native|native|independent'):
        require_same_trial(original, BlockProof.model_validate(changed), 0)


@pytest.mark.integration
@pytest.mark.metal
def test_probe_records_actual_small_network_blocks_without_changing_native_bytes(
    precision: str, request: pytest.FixtureRequest
) -> None:
    case = fixture()
    stimulus = Stimulus(case.events, case.targets, (), (0, 1, 2, 3), 0, 0, '')
    root = proof_root(request)
    ordinary = record_mode(
        'ordinary', case.connectome, stimulus, root / 'small-ordinary', precision
    )
    observed = record_mode(
        'session', case.connectome, stimulus, root / 'small-session', precision
    )
    assert sum(proof.rows for proof in observed.proofs) == 101
    for before, after in zip(ordinary.proofs, observed.proofs, strict=True):
        for trial in range(4):
            require_same_trial(before, after, trial)
