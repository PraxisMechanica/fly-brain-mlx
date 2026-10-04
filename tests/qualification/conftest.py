import importlib.metadata
import os
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import mlx.core as mx
import numpy as np
import pytest

from fly_brain.simulation.backend.engines import Factory, factored, serial
from tests.support.artifacts import ArtifactRecorder
from tests.support.qualification import Harness


@pytest.fixture(scope='session')
def project() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def compiler() -> Factory:
    return serial


@pytest.fixture(scope='module')
def harness(
    request: pytest.FixtureRequest, compiler: Factory, precision: str
) -> Iterator[Harness]:
    assert importlib.metadata.version('mlx') == '0.32.3'
    assert importlib.metadata.version('mlx-metal') == '0.32.3'
    assert np.__version__ == '1.26.4'
    assert mx.metal.is_available()
    mx.disable_compile()
    path = cast(str | None, request.config.getoption('--artifact-output'))
    output = Path(path) if path is not None else None
    is_factored = compiler is factored
    recorder = ArtifactRecorder(output, 'factored-' if is_factored else '')
    yield Harness(lambda case: compiler(case, precision), recorder)
    recorder.finish(
        'factored-networks.json' if is_factored else 'measurements.json',
        'Uncompiled factored recurrent-input adapter over unchanged qualified core'
        if is_factored
        else 'uncompiled, explicit Metal stream, ordered edge/channel additions',
    )


@pytest.fixture(scope='session')
def precision() -> str:
    value = os.environ.get('MLX_ENABLE_TF32')
    assert value == '0'
    return value
