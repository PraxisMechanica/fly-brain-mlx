import re
from pathlib import Path

import pytest

from tests.quality.support import PROJECT, run

pytestmark = pytest.mark.unit
SOURCE = 'fly_brain.qualification.reference_parameters'
TARGET = 'fly_brain.qualification.adapters.torch_reference'
ENTRY = '    "' + SOURCE + '",\n'
RULE = 'Scientific calculations avoid workflow and storage dependencies'


def sources(root: Path, code: str) -> Path:
    policy = (
        '[tool.importlinter]'
        + (PROJECT / 'pyproject.toml').read_text().split('[tool.importlinter]', 1)[1]
    )
    marker = '[[tool.importlinter.contracts]]'
    header, first, _ = policy.split(marker, 2)
    assert first.count(ENTRY) == 1
    policy = header + marker + first
    names = set(re.findall(r'"(fly_brain(?:\.[a-z_]+)*)"', policy))
    names.update((TARGET, 'fly_brain.qualification.helper'))
    for name in sorted(names):
        relative = Path('src', *name.split('.'))
        path = (
            relative.with_suffix('.py')
            if (PROJECT / relative.with_suffix('.py')).is_file()
            else relative / '__init__.py'
        )
        if name in (TARGET, 'fly_brain.qualification.helper'):
            path = relative.with_suffix('.py')
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text('VALUE = 1\n')
        for parent in relative.parents:
            if parent in (Path('src'), Path('.')):
                break
            (root / parent / '__init__.py').touch()
    (root / 'src/fly_brain/qualification/reference_parameters.py').write_text(code)
    (root / 'src/fly_brain/qualification/helper.py').write_text(
        'from ' + TARGET + ' import VALUE\n'
    )
    config = root / 'boundary.toml'
    config.write_text(policy)
    return config


def lint(root: Path, config: Path) -> tuple[int, str]:
    result = run(
        [
            str(PROJECT / '.venv/bin/lint-imports'),
            '--config',
            str(config),
            '--no-cache',
        ],
        root,
        {'PYTHONPATH': str(root / 'src') + ':' + str(PROJECT)},
    )
    return result.returncode, result.stdout + result.stderr


@pytest.mark.parametrize(
    'code',
    (
        'from ' + TARGET + ' import VALUE\n',
        'import ' + TARGET + ' as hidden\ndef create():\n    return hidden.VALUE\n',
        'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from '
        + TARGET
        + ' import VALUE\n',
        'from fly_brain.qualification.helper import VALUE\n',
    ),
)
def test_pure_defaults_reject_implementation_paths_then_accept_neutral_values(
    tmp_path: Path,
    code: str,
) -> None:
    config = sources(tmp_path, code)
    result, evidence = lint(tmp_path, config)
    assert result != 0 and RULE in evidence
    assert SOURCE in evidence and TARGET in evidence and '(l.' in evidence
    (tmp_path / 'src/fly_brain/qualification/reference_parameters.py').write_text(
        'from fly_brain.qualification.models import VALUE\n'
    )
    result, evidence = lint(tmp_path, config)
    assert result == 0, evidence


@pytest.mark.checker
def test_omitting_new_module_scope_hides_its_same_dependency(tmp_path: Path) -> None:
    config = sources(tmp_path, 'from ' + TARGET + ' import VALUE\n')
    result, evidence = lint(tmp_path, config)
    assert result != 0 and RULE in evidence
    config.write_text(config.read_text().replace(ENTRY, '', 1))
    result, evidence = lint(tmp_path, config)
    assert result == 0, evidence


def test_nearby_literal_stays_clean_and_missing_native_source_is_an_error(
    tmp_path: Path,
) -> None:
    config = sources(tmp_path, '# import ' + TARGET + '\nVALUE = "torch_reference"\n')
    result, evidence = lint(tmp_path, config)
    assert result == 0, evidence
    (tmp_path / 'src/fly_brain/qualification/reference_parameters.py').unlink()
    result, evidence = lint(tmp_path, config)
    assert result != 0 and 'does not exist' in evidence
