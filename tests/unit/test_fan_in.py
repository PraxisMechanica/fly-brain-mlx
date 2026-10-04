import numpy as np
import pytest

from fly_brain.qualification.fan_in import build_cases, compare_cases

pytestmark = pytest.mark.unit


def test_initial_conversion_is_visible_without_changing_the_trajectory_gate() -> None:
    counts = np.array([2405, 466], dtype=np.int32)
    cases = build_cases(11645, np.array([0, 1], dtype=np.int32), counts, counts * 0.275)
    result = cases.stored64[:, 0].astype(np.float32)
    checks = compare_cases(cases, result)
    selected = np.array(cases.state_names) == 'cancellation'
    selected &= cases.mask_indices == cases.mask_names.index('all')
    assert np.count_nonzero(selected) == 3
    assert checks.one_step_pass[selected].all()
    assert checks.trajectory_pass[selected].all()
    assert not checks.original_one_step_pass[selected].any()


def test_excess_original_state_error_still_fails_the_trajectory_gate() -> None:
    counts = np.array([2405, 466], dtype=np.int32)
    cases = build_cases(11645, np.array([0, 1], dtype=np.int32), counts, counts * 0.275)
    result = cases.original64[:, 0].astype(np.float32)
    selected = (np.array(cases.state_names) == 'cancellation') & (
        cases.mask_indices == cases.mask_names.index('all')
    )
    result[selected] = 0.002
    assert not compare_cases(cases, result).trajectory_pass[selected].any()


def test_empty_target_keeps_all_prescribed_masks_states_and_orders() -> None:
    cases = build_cases(
        102,
        np.zeros(0, dtype=np.int32),
        np.zeros(0, dtype=np.int32),
        np.zeros(0, dtype=np.float64),
    )
    assert len(cases.mask_names) == 70
    assert cases.leaves32.shape == (70 * 4 * 3, 1)
    assert np.signbit(
        cases.initial64[np.array(cases.state_names) == 'cancellation']
    ).all()


def test_all_orders_keep_masked_counts_and_both_reference_paths() -> None:
    counts = np.array([2405, -2404, -1], dtype=np.int32)
    cases = build_cases(19, np.array([0, 0, 1], dtype=np.int32), counts, counts * 0.275)
    for row, (mask_index, order_index) in enumerate(
        zip(cases.mask_indices, cases.order_indices, strict=True)
    ):
        mask, order = cases.masks[mask_index], cases.orders[order_index]
        expected = np.where(mask[order], counts[order], 0)
        np.testing.assert_array_equal(cases.leaves32[row, : counts.size], expected)
    selected = (np.array(cases.state_names) == 'zero') & (
        cases.mask_indices == cases.mask_names.index('all')
    )
    assert cases.original64.shape == cases.stored64.shape == (len(cases.initial64), 2)
    assert (
        np.abs(cases.cast_input64[selected] - cases.original64[selected, 0]).min()
        > 2e-5
    )
