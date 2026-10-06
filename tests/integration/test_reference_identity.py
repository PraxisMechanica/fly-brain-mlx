import subprocess
from dataclasses import replace
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from fly_brain.qualification.adapters.observer_stream import StreamShape
from fly_brain.qualification.adapters.reference_identity import create, file_record
from fly_brain.simulation.models import Connectome, Stimulus
from tests.quality.test_reference_digest import LegacyProducer, preserved_identity

pytestmark = pytest.mark.integration
BASE = 'e923c316342978e03a74c1455336e43a651ef6b0'


@pytest.fixture
def legacy_producer() -> LegacyProducer:
    source = subprocess.check_output(
        [
            'git',
            'show',
            BASE + ':src/fly_brain/qualification/adapters/reference_identity.py',
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
    )
    namespace = dict(create.__globals__)
    exec(compile(source, BASE + ':reference_identity.py', 'exec'), namespace)
    return cast(LegacyProducer, namespace['create'])


@pytest.mark.parametrize(
    'changed',
    [
        'neuron_ids',
        'sources',
        'destinations',
        'counts',
        'weights_mv',
        'events',
        'targets',
        'silenced',
        'coverage',
        'preferences',
        'dependencies',
        'compiler',
        'runtime',
        'generated',
        'static',
    ],
)
def test_reference_identity_binds_each_scientific_input_category(
    tmp_path: Path, changed: str, legacy_producer: LegacyProducer
) -> None:
    connectome = Connectome(
        np.arange(3, dtype=np.int64),
        np.asarray([0, 1], dtype=np.int32),
        np.asarray([1, 2], dtype=np.int32),
        np.asarray([1, -1], dtype=np.int32),
        np.asarray([0.275, -0.275], dtype=np.float64),
    )
    stimulus = Stimulus(np.zeros((1, 2, 1), np.uint8), (0,), (200,), (0,), 0, 0, '')
    shape = StreamShape(3, 2, 1, (2, 1), 2)
    context = {
        name: 'original'
        for name in ('preferences', 'dependencies', 'compiler', 'runtime')
    }
    (tmp_path / 'main.cpp').write_text('original code')
    (tmp_path / 'static_arrays').mkdir()
    (tmp_path / 'static_arrays/input').write_bytes(b'original input')
    original = preserved_identity(
        legacy_producer, connectome, stimulus, (), shape, tmp_path, context
    )
    silenced: tuple[int, ...] = ()
    if changed in ('neuron_ids', 'sources', 'destinations', 'counts', 'weights_mv'):
        values = getattr(connectome, changed).copy()
        values[0] += 1
        connectome = replace(connectome, **{changed: values})
    elif changed == 'events':
        stimulus.events[0, 0, 0] = 1
    elif changed == 'targets':
        stimulus = replace(stimulus, targets=(1,))
    elif changed == 'silenced':
        silenced = (1,)
    elif changed == 'coverage':
        shape = replace(shape, block_size=1)
    elif changed in context:
        context[changed] = 'changed'
    elif changed == 'generated':
        (tmp_path / 'main.cpp').write_text('changed code')
    else:
        (tmp_path / 'static_arrays/input').write_bytes(b'changed input')
    actual = preserved_identity(
        legacy_producer, connectome, stimulus, silenced, shape, tmp_path, context
    )
    assert actual != original


def test_unused_candidate_executable_is_separate_from_sealed_producer(
    tmp_path: Path,
    legacy_producer: LegacyProducer,
) -> None:
    connectome = Connectome(
        np.arange(1, dtype=np.int64),
        np.empty(0, np.int32),
        np.empty(0, np.int32),
        np.empty(0, np.int32),
        np.empty(0, np.float64),
    )
    stimulus = Stimulus(np.zeros((1, 2, 0), np.uint8), (), (), (0,), 0, 0, '')
    shape = StreamShape(1, 2, 0, (), 2)
    (tmp_path / 'main').write_bytes(b'original executable')
    before = file_record(tmp_path / 'main')
    original = preserved_identity(
        legacy_producer, connectome, stimulus, (), shape, tmp_path, {}
    )
    (tmp_path / 'main').write_bytes(b'changed executable')
    (tmp_path / 'unused-mlx.py').write_text('changed candidate')
    actual = preserved_identity(
        legacy_producer, connectome, stimulus, (), shape, tmp_path, {}
    )
    assert actual == original
    assert file_record(tmp_path / 'main') != before
