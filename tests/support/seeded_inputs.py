import numpy as np
from numpy.typing import NDArray

from fly_brain.infrastructure.seeded_random import permutation, uniforms
from fly_brain.qualification.fan_in import FanInCases
from fly_brain.qualification.fan_in_service import prepare_masks
from fly_brain.qualification.module import build_fan_in_cases
from fly_brain.simulation.models import Connectome, Experiment, Stimulus
from fly_brain.simulation.module import build_stimulus


def generate(
    connectome: Connectome,
    experiment: Experiment,
    steps: int,
    trials: tuple[int, ...],
    seed: int = 20261004,
) -> Stimulus:
    operation = build_stimulus(uniforms)
    return operation(connectome, experiment, steps, trials, seed)


def build_cases(
    target: int,
    sources: NDArray[np.int32],
    counts: NDArray[np.int32],
    weights: NDArray[np.float64],
) -> FanInCases:
    operation = build_fan_in_cases(uniforms, permutation)
    return operation(target, sources, counts, weights)


def source_masks(
    target: int, sources: NDArray[np.int32], weights: NDArray[np.float64]
) -> dict[str, NDArray[np.bool_]]:
    return prepare_masks(target, sources, weights, draw_uniforms=uniforms)
