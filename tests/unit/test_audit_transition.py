import subprocess
import sys
from collections.abc import Callable
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.causal_capture import CausalCapture
from fly_brain.qualification.adapters.observer_stream import (
    ObservationArray,
    PhaseBlock,
    StepSnapshot,
)
from fly_brain.qualification.adapters.paired_observer import PairedBlock
from fly_brain.qualification.causality import (
    BudgetViolation,
    CausalAudit,
    StateFields,
    advance_audit,
)
from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.simulation.observations import HostArray
from tests.support.session_block_values import replace_block

pytestmark = pytest.mark.unit
BASE = 'b8d490a35b75d7b4fea9f8799a7554bae1888e49'
ROOT = Path(__file__).resolve().parents[2]


class Legacy(Protocol):
    step: int
    first_budget_violation: BudgetViolation | None
    first_spike_step: int | None
    first_spike_neurons: tuple[int, ...]

    def check(
        self,
        step: int,
        reference: StateFields,
        mlx: StateFields,
        reference_spikes: NDArray[np.bool_],
        mlx_spikes: NDArray[np.bool_],
    ) -> None: ...


@pytest.fixture
def legacy(monkeypatch: pytest.MonkeyPatch) -> Legacy:
    module = ModuleType('tests._legacy_audit')
    monkeypatch.setitem(sys.modules, module.__name__, module)
    source = subprocess.check_output(
        ['git', 'show', BASE + ':src/fly_brain/qualification/causality.py'],
        cwd=ROOT,
        text=True,
    )
    exec(compile(source, BASE + ':causality.py', 'exec'), module.__dict__)
    return cast(Callable[[], Legacy], module.__dict__['CausalAudit'])()


def state_fields() -> dict[str, NDArray[np.float64]]:
    return {
        phase + '_' + field: np.zeros(4, dtype=np.float64)
        for phase in ('pre', 'before', 'end')
        for field in ('v', 'g')
    }


def payload(audit: Legacy | CausalAudit) -> tuple[object, ...]:
    return (
        audit.step,
        asdict(audit.first_budget_violation)
        if audit.first_budget_violation is not None
        else None,
        audit.first_spike_step,
        audit.first_spike_neurons,
    )


@pytest.mark.parametrize('fork', (None, 0, 17, 33))
@pytest.mark.parametrize('violation', (None, 0, 16, 17))
def test_every_successful_prefix_matches_frozen_source_without_mutating_inputs(
    legacy: Legacy, fork: int | None, violation: int | None
) -> None:
    current = CausalAudit()
    for step in range(36):
        reference, mlx = state_fields(), state_fields()
        quiet, actual = np.zeros(4, dtype=np.bool_), np.zeros(4, dtype=np.bool_)
        if step == violation:
            mlx['pre_g'][2] = 0.002
            mlx['before_v'][0] = 100
        if step == fork:
            actual[[1, 3]] = True
        before = {
            name: value.tobytes()
            for name, value in {
                **reference,
                **{'mlx_' + k: v for k, v in mlx.items()},
            }.items()
        }
        prior, saved = current, payload(current)
        legacy.check(step, reference, mlx, quiet, actual)
        current = advance_audit(current, step, reference, mlx, quiet, actual)
        assert payload(current) == payload(legacy)
        assert payload(prior) == saved and current is not prior
        assert before == {
            name: value.tobytes()
            for name, value in {
                **reference,
                **{'mlx_' + k: v for k, v in mlx.items()},
            }.items()
        }
        assert not quiet.any() and np.array_equal(
            actual, np.isin(np.arange(4), [1, 3]) if step == fork else quiet
        )


def block(
    begin: int, rows: int, fork: int | None = None, violation: int | None = None
) -> PairedBlock:
    reference: dict[str, ObservationArray] = {}
    actual: dict[str, HostArray] = {}
    times = np.arange(begin, begin + rows) * 0.0001
    for phase in ('pre', 'before', 'end'):
        reference[phase + '_t'] = times.copy()
        reference[phase + '_not_refractory'] = np.ones((rows, 4), dtype=np.bool_)
        actual[phase + '_not_refractory'] = np.ones((rows, 1, 4), dtype=np.bool_)
        for field in ('v', 'g'):
            reference[phase + '_' + field] = np.zeros((rows, 4), dtype=np.float64)
            actual[phase + '_' + field] = np.zeros((rows, 1, 4), dtype=np.float32)
    reference['end_lastspike'] = np.full((rows, 4), -10000, dtype=np.float64)
    actual['end_last_spike_step'] = np.full((rows, 1, 4), -100000000, dtype=np.int32)
    spikes = np.zeros((rows, 1, 4), dtype=np.bool_)
    if fork is not None:
        spikes[fork - begin, 0, [1, 3]] = True
    if violation is not None:
        cast(NDArray[np.float32], actual['pre_g'])[violation - begin, 0, 2] = 0.002
    actual['spikes'] = spikes
    snapshots = tuple(
        StepSnapshot(
            step,
            step,
            step * 0.0001,
            -1,
            np.array([], dtype=np.int32),
            np.array([], dtype=np.int32),
            (),
        )
        for step in range(begin, begin + rows)
    )
    mlx = SessionBlock(
        begin,
        rows,
        (0,),
        actual,
        np.ones((rows, 1, 30), dtype=np.bool_),
        ('queue',),
        (('slot',) * 19,),
        None,
        tuple((np.array([], dtype=np.int32),) for _ in range(rows)),
        tuple(('due',) for _ in range(rows)),
    )
    return PairedBlock(
        PhaseBlock(begin, rows, reference),
        mlx,
        snapshots,
        ('reference', 'actual'),
    )


def test_fold_and_capture_rebind_before_first_row_boundary_context() -> None:
    capture = CausalCapture()
    capture.check(block(0, 17))
    prior = capture.audit
    capture.check(block(17, 17, fork=17, violation=17))
    assert prior == CausalAudit(step=17)
    assert capture.audit.step == 34 and capture.audit.first_spike_neurons == (1, 3)
    assert capture.budget is not None and capture.spike is not None
    assert (
        capture.budget.current.snapshot.step
        == capture.spike.current.snapshot.step
        == 17
    )
    assert capture.budget.previous is not None and capture.spike.previous is not None
    assert (
        capture.budget.previous.snapshot.step
        == capture.spike.previous.snapshot.step
        == 16
    )
    capture.check(block(34, 2))
    assert capture.audit.step == 36 and capture.spike.current.snapshot.step == 17


def test_wrong_step_precedes_nonfinite_and_state_can_retry() -> None:
    reference, actual = state_fields(), state_fields()
    actual['pre_v'][0] = np.nan
    initial = CausalAudit()
    quiet = np.zeros(4, dtype=np.bool_)
    with pytest.raises(ValueError, match='consecutive'):
        advance_audit(initial, 1, reference, actual, quiet, quiet)
    with pytest.raises(ValueError, match='finite'):
        advance_audit(initial, 0, reference, actual, quiet, quiet)
    actual['pre_v'][0] = 0
    assert advance_audit(initial, 0, reference, actual, quiet, quiet) == CausalAudit(
        step=1
    )
    assert initial == CausalAudit()


def test_missing_field_exposes_old_partial_mutation_but_new_retry_is_clean(
    legacy: Legacy,
) -> None:
    reference, actual = state_fields(), state_fields()
    actual['pre_v'][1] = 0.002
    del reference['pre_g']
    quiet = np.zeros(4, dtype=np.bool_)
    initial = CausalAudit()
    with pytest.raises(KeyError, match='pre_g'):
        legacy.check(0, reference, actual, quiet, quiet)
    with pytest.raises(KeyError, match='pre_g'):
        advance_audit(initial, 0, reference, actual, quiet, quiet)
    assert legacy.step == 0 and legacy.first_budget_violation is not None
    assert initial == CausalAudit()
    actual['pre_v'][1] = 0
    reference['pre_g'] = np.zeros(4, dtype=np.float64)
    assert advance_audit(initial, 0, reference, actual, quiet, quiet) == CausalAudit(
        step=1
    )


def test_failed_block_does_not_publish_partial_audit_or_capture_context() -> None:
    capture = CausalCapture()
    broken = block(0, 2)
    fields = dict(broken.mlx.fields)
    fields['pre_g'] = fields['pre_g'].copy()
    cast(NDArray[np.float32], fields['pre_g'])[1, 0, 0] = np.nan
    broken = replace(broken, mlx=replace_block(broken.mlx, fields=fields))
    with pytest.raises(ValueError, match='finite'):
        capture.check(broken)
    assert capture.audit == CausalAudit() and capture.previous is None
    assert capture.budget is None and capture.spike is None
    capture.check(block(0, 2))
    assert capture.audit == CausalAudit(step=2)


def test_scalar_state_is_frozen_detached_and_has_no_mutating_facade() -> None:
    reference, actual = state_fields(), state_fields()
    actual['pre_v'][1] = 0.002
    quiet = np.zeros(4, dtype=np.bool_)
    value = advance_audit(CausalAudit(), 0, reference, actual, quiet, ~quiet)
    saved = payload(value)
    actual['pre_v'][:] = 100
    reference['pre_v'][:] = 100
    assert payload(value) == saved
    assert not hasattr(value, 'check')
    with pytest.raises(FrozenInstanceError):
        value.__setattr__('step', 100)
    assert replace(value, step=1) == value
