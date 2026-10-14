import hashlib
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
    root = Path(__file__).resolve().parents[2]
    package = ModuleType('preserved_torch_reference')
    package.__path__ = []
    loaded: dict[str, ModuleType] = {}
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, package.__name__, package)
        for name in (
            'brian_reference',
            'torch_reference',
            'torch_setup',
            'schedule_probe',
        ):
            identity = (
                ORIGINAL_COMMIT
                + ':src/fly_brain/qualification/adapters/'
                + name
                + '.py'
            )
            source = subprocess.check_output(
                [
                    'git',
                    '-C',
                    str(root),
                    'show',
                    identity,
                ]
            )
            if name == 'torch_reference':
                assert hashlib.sha256(source).hexdigest() == ORIGINAL_SHA256
            module = ModuleType(package.__name__ + '.' + name)
            module.__file__ = identity
            patch.setitem(sys.modules, module.__name__, module)
            setattr(package, name, module)
            exec(compile(source, identity, 'exec'), module.__dict__)
            loaded[name] = module
        yield loaded['torch_reference'], loaded['torch_setup']
