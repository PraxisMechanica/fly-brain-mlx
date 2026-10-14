from pathlib import Path

import pytest

from tests.quality.support import PROJECT, run

pytestmark = pytest.mark.unit
SOURCES = (
    'fly_brain.qualification.service',
    'fly_brain.qualification.adapters.parity_case',
    'fly_brain.qualification.adapters.case_report',
)
TARGETS = (
    'fly_brain.simulation.experiments',
    'fly_brain.simulation.stimuli',
    'fly_brain.simulation.storage',
)
CONTRACT = 'Parity uses owned stimulus services'
CONFIG = f'''[tool.importlinter]
root_package = "fly_brain"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "{CONTRACT}"
type = "forbidden"
source_modules = {list(SOURCES)!r}
forbidden_modules = {list(TARGETS)!r}
allow_indirect_imports = false
'''


def lint(root: Path, config: Path) -> tuple[int, str]:
    result = run(
        [
            str(PROJECT / '.venv/bin/lint-imports'),
            '--config',
            str(config),
            '--no-cache',
        ],
        root,
        {'PYTHONPATH': str(root / 'src') + ':' + str(root) + ':' + str(PROJECT)},
    )
    return result.returncode, result.stdout + result.stderr


def sources(root: Path, code: str) -> Path:
    files = {name: 'VALUE = 1\n' for name in (*SOURCES, *TARGETS)}
    files[SOURCES[0]] = code
    files['fly_brain.simulation.models'] = 'VALUE = 1\n'
    files['fly_brain.qualification.input_helper'] = (
        'from fly_brain.simulation.storage import VALUE\n'
    )
    for name, content in files.items():
        path = root / 'src' / Path(*name.split('.')).with_suffix('.py')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    for path in (root / 'src').rglob('*'):
        if path.is_dir():
            (path / '__init__.py').write_text('')
    config = root / 'boundary.toml'
    config.write_text(CONFIG)
    return config


@pytest.mark.parametrize('target', TARGETS)
@pytest.mark.parametrize(
    'form',
    ('direct', 'alias', 'type-only', 'wrapped'),
)
def test_private_stimulus_imports_reject_native_paths_and_accept_neutral_values(
    tmp_path: Path, target: str, form: str
) -> None:
    code = {
        'direct': f'from {target} import VALUE\n',
        'alias': f'import {target} as hidden\n',
        'type-only': f'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from {target} import VALUE\n',
        'wrapped': f'def hidden():\n    from {target} import VALUE\n    return VALUE\n',
    }[form]
    config = sources(tmp_path, code)
    result, output = lint(tmp_path, config)
    assert result != 0 and CONTRACT in output
    assert SOURCES[0] in output and target in output and '(l.' in output
    (tmp_path / 'src/fly_brain/qualification/service.py').write_text(
        'from fly_brain.simulation.models import VALUE\n'
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output


@pytest.mark.checker
def test_transitive_reexport_rejection_and_independent_weakening(
    tmp_path: Path,
) -> None:
    config = sources(
        tmp_path, 'from fly_brain.qualification.input_helper import VALUE as public\n'
    )
    result, output = lint(tmp_path, config)
    assert result != 0
    assert 'fly_brain.qualification.input_helper' in output
    assert 'fly_brain.simulation.storage' in output and '(l.1)' in output
    config.write_text(
        CONFIG.replace(
            'allow_indirect_imports = false', 'allow_indirect_imports = true'
        )
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output


def test_missing_native_scope_is_an_error_and_close_source_stays_clean(
    tmp_path: Path,
) -> None:
    config = sources(
        tmp_path,
        '# from fly_brain.simulation.storage import VALUE\nTEXT = "simulation.stimuli"\n',
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output
    config.write_text(CONFIG.replace(SOURCES[0], 'fly_brain.qualification.absent'))
    result, output = lint(tmp_path, config)
    assert result != 0 and 'does not exist' in output


def test_actual_parity_sources_have_no_path_to_private_stimulus_modules(
    tmp_path: Path,
) -> None:
    config = tmp_path / 'actual-boundary.toml'
    config.write_text(CONFIG)
    result, output = lint(PROJECT, config)
    assert result == 0, output
