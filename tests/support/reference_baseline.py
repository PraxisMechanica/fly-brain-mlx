import hashlib
import importlib.util
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

ORIGINAL_COMMIT = '79f62adee10b092fcaaaed0ea4043da3f5b9c415'
ORIGINAL_SHA256 = 'bf52258041a464156ce05b267601dbefceb893356fbf8401b358b036a29ba6cb'


@pytest.fixture(scope='module')
def original() -> Iterator[tuple[ModuleType, ModuleType]]:
    root = Path(os.environ['FLY_BRAIN_REFERENCE_BASELINE']).resolve()
    assert sys.dont_write_bytecode
    assert (
        subprocess.check_output(
            ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True
        ).strip()
        == ORIGINAL_COMMIT
    )
    directory = root / 'src/fly_brain/qualification/adapters'
    assert (
        hashlib.sha256((directory / 'torch_reference.py').read_bytes()).hexdigest()
        == ORIGINAL_SHA256
    )
    package = ModuleType('preserved_torch_reference')
    package.__path__ = [str(directory)]
    loaded: list[ModuleType] = []
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, package.__name__, package)
        for name in ('torch_reference', 'torch_setup'):
            path = directory / (name + '.py')
            expected = subprocess.check_output(
                [
                    'git',
                    '-C',
                    str(root),
                    'show',
                    ORIGINAL_COMMIT
                    + ':src/fly_brain/qualification/adapters/'
                    + name
                    + '.py',
                ]
            )
            assert path.read_bytes() == expected
            spec = importlib.util.spec_from_file_location(
                package.__name__ + '.' + name, path
            )
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            patch.setitem(sys.modules, spec.name, module)
            spec.loader.exec_module(module)
            loaded.append(module)
        yield loaded[0], loaded[1]
