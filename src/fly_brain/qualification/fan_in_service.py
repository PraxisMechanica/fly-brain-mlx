import numpy as np
from numpy.typing import NDArray

from .fan_in import FanInCases, build_cases
from .fan_in_ports import PermutationDraws, UniformDraws
from .input_patterns import MASK_PROBABILITIES, source_masks, threshold_uniforms


def prepare_masks(
    target: int,
    sources: NDArray[np.int32],
    weights: NDArray[np.float64],
    *,
    draw_uniforms: UniformDraws,
) -> dict[str, NDArray[np.bool_]]:
    size = np.unique(sources).size
    prepared = tuple(
        threshold_uniforms(
            draw_uniforms((20261004, 783, target, index, replicate), size), probability
        )
        for index, probability in enumerate(MASK_PROBABILITIES)
        for replicate in range(16)
    )
    return source_masks(sources, weights, random_source_masks=prepared)


def prepare_cases(
    target: int,
    sources: NDArray[np.int32],
    counts: NDArray[np.int32],
    weights: NDArray[np.float64],
    *,
    draw_uniforms: UniformDraws,
    permute: PermutationDraws,
) -> FanInCases:
    masks = prepare_masks(target, sources, weights, draw_uniforms=draw_uniforms)
    order = permute((20261004, 784, target), counts.size)
    return build_cases(counts, weights, masks=masks, permutation=order)
