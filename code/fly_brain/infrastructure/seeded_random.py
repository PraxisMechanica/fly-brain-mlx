import numpy as np
from numpy.typing import NDArray


def uniforms(seed: tuple[int, ...], size: int | tuple[int, int]) -> NDArray[np.float64]:
    generator = np.random.Generator(np.random.PCG64(np.random.SeedSequence(list(seed))))
    return generator.random(size)


def permutation(seed: tuple[int, ...], size: int) -> NDArray[np.int64]:
    generator = np.random.Generator(np.random.PCG64(np.random.SeedSequence(list(seed))))
    return generator.permutation(size)
