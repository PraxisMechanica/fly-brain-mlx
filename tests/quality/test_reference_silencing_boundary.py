from pathlib import Path

import pytest

from tests.quality.support import PROJECT, run
from tests.quality.test_parity_stimulus_boundary import lint

pytestmark = pytest.mark.unit
RULE = 'DEP003/ROLE005: PyTorch reference uses injected connectome silencing'
SOURCES = (
    'fly_brain.qualification.adapters.torch_setup',
    'fly_brain.qualification.adapters.parity_case',
)
TARGETS = (
    'fly_brain.simulation.mapping',
    'fly_brain.simulation.input_service',
    'fly_brain.simulation.module',
)
NATIVE_TYPES = """from fly_brain.qualification.ports import ConnectomeSilencer as Consumer
from fly_brain.simulation.ports import ConnectomeSilencer as Provider
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.models import Connectome
def provided(connectome: Connectome, silenced: tuple[NeuronRow, ...]) -> Connectome:
    return connectome
provider: Provider = provided
consumer: Consumer = provider
"""


def contract() -> str:
    blocks = (
        (PROJECT / 'pyproject.toml')
        .read_text()
        .split('[[tool.importlinter.contracts]]')
    )
    selected = next(block for block in blocks if 'name = "' + RULE + '"' in block)
    return (
        '[tool.importlinter]\nroot_package = "fly_brain"\n\n[[tool.importlinter.contracts]]'
        + selected
    )


def sources(root: Path, target: str, code: str) -> Path:
    files = {name: 'VALUE = 1\n' for name in (*SOURCES, *TARGETS)}
    files[SOURCES[0]] = code
    files['fly_brain.qualification.silencing_helper'] = f'from {target} import VALUE\n'
    files['fly_brain.qualification.ports'] = 'VALUE = 1\n'
    for name, content in files.items():
        path = root / 'src' / Path(*name.split('.')).with_suffix('.py')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    for directory in (root / 'src').rglob('*'):
        if directory.is_dir():
            (directory / '__init__.py').touch()
    config = root / 'boundary.toml'
    config.write_text(contract())
    return config


@pytest.mark.parametrize('target', TARGETS)
@pytest.mark.parametrize(
    'form',
    (
        'from {target} import VALUE\n',
        'import {target} as hidden\ndef capture():\n    return hidden.VALUE\n',
        'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from {target} import VALUE\n',
        'from fly_brain.qualification.silencing_helper import VALUE as neutral\n',
    ),
)
def test_actual_contract_rejects_native_private_paths_and_accepts_injected_port(
    tmp_path: Path, target: str, form: str
) -> None:
    config = sources(tmp_path, target, form.format(target=target))
    result, output = lint(tmp_path, config)
    assert (
        result != 0,
        RULE in output,
        SOURCES[0] in output,
        target in output,
        '(l.' in output,
    ) == (True,) * 5
    (tmp_path / 'src/fly_brain/qualification/adapters/torch_setup.py').write_text(
        'from fly_brain.qualification.ports import VALUE\n'
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output


def test_parity_reexport_rejects_and_transitivity_weakening_hides_same_path(
    tmp_path: Path,
) -> None:
    config = sources(tmp_path, TARGETS[0], 'VALUE = 1\n')
    (tmp_path / 'src/fly_brain/qualification/adapters/parity_case.py').write_text(
        'from fly_brain.qualification.silencing_helper import VALUE\n'
    )
    result, output = lint(tmp_path, config)
    assert (
        result != 0,
        SOURCES[1] in output,
        TARGETS[0] in output,
        'fly_brain.qualification.silencing_helper' in output,
        '(l.1)' in output,
    ) == (True,) * 5
    config.write_text(
        contract().replace(
            'allow_indirect_imports = false', 'allow_indirect_imports = true'
        )
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output


def test_close_literal_stays_clean_and_missing_source_is_a_native_error(
    tmp_path: Path,
) -> None:
    config = sources(
        tmp_path, TARGETS[0], '# import simulation.mapping\nVALUE = "silence_sources"\n'
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output
    config.write_text(contract().replace(SOURCES[0], 'fly_brain.missing'))
    result, output = lint(tmp_path, config)
    assert result != 0 and 'does not exist' in output


def test_missing_forbidden_target_exposes_native_inventory_limit(
    tmp_path: Path,
) -> None:
    config = sources(tmp_path, TARGETS[0], f'from {TARGETS[0]} import VALUE\n')
    result, output = lint(tmp_path, config)
    assert result != 0 and RULE in output
    config.write_text(contract().replace(TARGETS[0], 'fly_brain.missing'))
    result, output = lint(tmp_path, config)
    assert result == 0, output


def typed(root: Path, code: str) -> tuple[int, str]:
    source = root / 'consumer.py'
    source.write_text(code)
    result = run(
        [
            str(PROJECT / '.venv/bin/pyright'),
            '--project',
            str(PROJECT / 'pyproject.toml'),
            str(source),
        ],
        PROJECT,
    )
    return result.returncode, result.stdout + result.stderr


@pytest.mark.parametrize(
    'imports,rows',
    (
        ('', '(3,)'),
        ('from fly_brain.simulation.identifiers import TrialId\n', '(TrialId(3),)'),
    ),
)
def test_native_ports_reject_primitive_and_foreign_rows_then_accept_owner_type(
    tmp_path: Path, imports: str, rows: str
) -> None:
    body = 'def use(connectome: Connectome) -> Connectome:\n    return consumer(connectome, {rows})\n'
    result, output = typed(tmp_path, NATIVE_TYPES + imports + body.format(rows=rows))
    assert result == 1 and 'consumer.py:' in output and 'reportArgumentType' in output
    result, output = typed(tmp_path, NATIVE_TYPES + body.format(rows='(NeuronRow(3),)'))
    assert result == 0, output


def test_required_callback_shape_and_missing_injection_reject_then_repair(
    tmp_path: Path,
) -> None:
    bad = NATIVE_TYPES.replace(
        '-> Connectome:\n    return connectome', '-> int:\n    return 0'
    )
    result, output = typed(tmp_path, bad)
    assert result == 1 and 'consumer.py:' in output and 'reportAssignmentType' in output
    body = 'def create(connectome: Connectome) -> TorchModel:\n    return prepare(connectome, (), (), 1, reference_parameters={{}}{keyword})\n'
    imports = 'from fly_brain.qualification.adapters.torch_setup import prepare\nfrom fly_brain.qualification.adapters.torch_reference import TorchModel\n'
    result, output = typed(tmp_path, NATIVE_TYPES + imports + body.format(keyword=''))
    assert result == 1 and 'consumer.py:' in output and '"silence"' in output
    result, output = typed(
        tmp_path, NATIVE_TYPES + imports + body.format(keyword=', silence=consumer')
    )
    assert result == 0, output


def test_live_contract_has_no_private_path_and_native_syntax_errors_fail(
    tmp_path: Path,
) -> None:
    config = tmp_path / 'live.toml'
    config.write_text(contract())
    result, output = lint(PROJECT, config)
    assert result == 0, output
    result, output = typed(tmp_path, NATIVE_TYPES + 'def broken(\n')
    assert result == 1 and 'consumer.py:' in output and 'error:' in output
