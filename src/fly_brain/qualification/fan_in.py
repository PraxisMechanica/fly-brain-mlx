import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class FanInCases:
    mask_names: tuple[str, ...]
    masks: NDArray[np.bool_]
    orders: NDArray[np.int32]
    mask_indices: NDArray[np.int32]
    order_indices: NDArray[np.int32]
    state_names: tuple[str, ...]
    initial64: NDArray[np.float64]
    leaves32: NDArray[np.float32]
    original64: NDArray[np.float64]
    stored64: NDArray[np.float64]
    cast_input64: NDArray[np.float64]
    exact_counts: NDArray[np.int64]
    absolute_counts: NDArray[np.int64]
    absolute_weights64: NDArray[np.float64]


@dataclass(frozen=True)
class FanInChecks:
    stored_error64: NDArray[np.float64]
    original_error64: NDArray[np.float64]
    one_step_budget64: NDArray[np.float64]
    trajectory_budget64: NDArray[np.float64]
    one_step_pass: NDArray[np.bool_]
    trajectory_pass: NDArray[np.bool_]
    original_one_step_pass: NDArray[np.bool_]


def build_cases(
    counts: NDArray[np.int32],
    weights: NDArray[np.float64],
    *,
    masks: Mapping[str, NDArray[np.bool_]],
    permutation: NDArray[np.int64],
) -> FanInCases:
    if (permutation.dtype, permutation.shape) != (np.int64, (counts.size,)):
        raise ValueError('Fan-in permutation has the wrong native shape or dtype')
    orders = np.stack(
        (
            np.arange(counts.size, dtype=np.int32),
            np.arange(counts.size, dtype=np.int32)[::-1],
            permutation.astype(np.int32),
        )
    )
    width = 1 << (max(1, counts.size) - 1).bit_length()
    mask_indices: list[int] = []
    order_indices: list[int] = []
    names: list[str] = []
    initials: list[float] = []
    leaves: list[NDArray[np.float32]] = []
    original: list[tuple[float, float]] = []
    stored: list[tuple[float, float]] = []
    cast: list[float] = []
    exact: list[int] = []
    absolute_counts: list[int] = []
    absolute_weights: list[float] = []
    for mask_index, mask in enumerate(masks.values()):
        active_weights = np.where(mask, weights, 0)
        active_counts = np.where(mask, counts, 0).astype(np.int64)
        cancel = -math.fsum(active_weights)
        states = [('zero', 0.0), ('positive', 1024.0), ('negative', -1024.0)]
        if abs(cancel) <= 1024:
            states.append(('cancellation', cancel))
        for state_name, initial in states:
            initial32 = float(np.float32(initial))
            for order_index, order in enumerate(orders):
                ordered_weights = active_weights[order]
                original_terms = np.concatenate(([initial], ordered_weights))
                stored_terms = np.concatenate(([initial32], ordered_weights))
                padded = np.zeros(width, dtype=np.float32)
                padded[: counts.size] = active_counts[order]
                mask_indices.append(mask_index)
                order_indices.append(order_index)
                names.append(state_name)
                initials.append(initial)
                leaves.append(padded)
                original.append(
                    (
                        math.fsum(original_terms),
                        float(np.add.accumulate(original_terms, dtype=np.float64)[-1]),
                    )
                )
                stored.append(
                    (
                        math.fsum(stored_terms),
                        float(np.add.accumulate(stored_terms, dtype=np.float64)[-1]),
                    )
                )
                cast.append(
                    math.fsum(
                        np.concatenate(
                            (
                                [initial32],
                                ordered_weights.astype(np.float32).astype(np.float64),
                            )
                        )
                    )
                )
                exact.append(int(active_counts.sum(dtype=np.int64)))
                absolute_counts.append(int(np.abs(active_counts).sum(dtype=np.int64)))
                absolute_weights.append(math.fsum(np.abs(active_weights)))
    return FanInCases(
        tuple(masks),
        np.stack(tuple(masks.values())),
        orders,
        np.array(mask_indices, dtype=np.int32),
        np.array(order_indices, dtype=np.int32),
        tuple(names),
        np.array(initials, dtype=np.float64),
        np.stack(leaves),
        np.array(original, dtype=np.float64),
        np.array(stored, dtype=np.float64),
        np.array(cast, dtype=np.float64),
        np.array(exact, dtype=np.int64),
        np.array(absolute_counts, dtype=np.int64),
        np.array(absolute_weights, dtype=np.float64),
    )


def compare_cases(cases: FanInCases, result: NDArray[np.float32]) -> FanInChecks:
    finite = np.isfinite(result)
    stored_error = np.abs(result.astype(np.float64)[:, None] - cases.stored64)
    original_error = np.abs(result.astype(np.float64)[:, None] - cases.original64)
    one_step_budget = 2e-5 + 2e-6 * np.abs(cases.stored64)
    trajectory_budget = 1e-3 + 1e-5 * np.abs(cases.original64)
    return FanInChecks(
        stored_error,
        original_error,
        one_step_budget,
        trajectory_budget,
        finite & np.all(stored_error <= one_step_budget, axis=1),
        finite & np.all(original_error <= trajectory_budget, axis=1),
        finite
        & np.all(original_error <= 2e-5 + 2e-6 * np.abs(cases.original64), axis=1),
    )
