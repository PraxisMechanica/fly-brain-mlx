import re
from pathlib import Path

import pytest

from tests.quality.support import PROJECT
from tests.quality.test_parity_stimulus_boundary import lint


def source_project(root: Path, files: dict[str, str]) -> Path:
    policy = (
        '[tool.importlinter]'
        + (PROJECT / 'pyproject.toml').read_text().split('[tool.importlinter]', 1)[1]
    )
    names = set(re.findall(r'"(fly_brain(?:\.[a-z_]+)*)"', policy)) | files.keys()
    for name in sorted(names):
        relative = Path('src', *name.split('.'))
        path = (
            relative.with_suffix('.py')
            if (PROJECT / relative.with_suffix('.py')).is_file()
            else relative / '__init__.py'
        )
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(files.get(name, 'VALUE = 1\n'))
        for parent in relative.parents:
            if parent in (Path('src'), Path('.')):
                break
            (root / parent / '__init__.py').touch()
    config = root / 'boundaries.toml'
    config.write_text(policy)
    return config


@pytest.mark.parametrize(
    'source,target,contract',
    (
        (
            'simulation.service',
            'qualification.adapters',
            'MLX simulation has no reference or comparison framework',
        ),
        (
            'comparison.metrics',
            'simulation.backend',
            'Spike comparison has no execution framework',
        ),
        (
            'qualification.reference_parameters',
            'simulation.storage',
            'Scientific calculations avoid workflow and storage dependencies',
        ),
    ),
)
def test_project_boundaries_reject_cross_workflow_or_storage_dependencies(
    tmp_path: Path, source: str, target: str, contract: str
) -> None:
    config = source_project(
        tmp_path,
        {'fly_brain.' + source: 'from fly_brain.' + target + ' import VALUE\n'},
    )
    result, output = lint(tmp_path, config)
    assert result != 0, output
    assert contract in output and 'fly_brain.' + source in output
    assert 'fly_brain.' + target in output and '(l.1)' in output


@pytest.mark.parametrize(
    'source,code',
    (
        ('simulation.backend.engines', 'import mlx.core as mx\n'),
        (
            'qualification.adapters.torch_reference',
            'from torch import nn\nclass TorchModel(nn.Module):\n    pass\n',
        ),
        ('qualification.adapters.brian_reference', 'from brian2 import NeuronGroup\n'),
    ),
)
def test_framework_specific_scientific_implementations_are_permitted(
    tmp_path: Path, source: str, code: str
) -> None:
    config = source_project(tmp_path, {'fly_brain.' + source: code})
    result, output = lint(tmp_path, config)
    assert result == 0, output
