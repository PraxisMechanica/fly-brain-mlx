from pathlib import Path

import pytest

from tests.quality.hook_fixture import commit_document, hook_repository
from tests.quality.support import git

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'module,implementation,neutral',
    (
        ('simulation.ports', 'simulation.inputs', 'simulation.models'),
        ('simulation.input_service', 'simulation.inputs', 'simulation.models'),
        ('comparison.ports', 'comparison.storage', 'comparison.models'),
        ('comparison.reporting', 'comparison.storage', 'comparison.models'),
        (
            'simulation.stimulus_service',
            'infrastructure.seeded_random',
            'simulation.models',
        ),
        (
            'qualification.fan_in_service',
            'infrastructure.seeded_random',
            'qualification.models',
        ),
        (
            'qualification.fan_in_ports',
            'infrastructure.seeded_random',
            'qualification.models',
        ),
        (
            'qualification.stimulus_ports',
            'infrastructure.seeded_random',
            'simulation.models',
        ),
        ('simulation.stimuli', 'infrastructure.seeded_random', 'simulation.models'),
        (
            'qualification.input_patterns',
            'infrastructure.seeded_random',
            'qualification.models',
        ),
    ),
)
def test_new_composition_contracts_reject_implementations_then_accept_neutral_values(
    tmp_path: Path, module: str, implementation: str, neutral: str
) -> None:
    repo, environment = hook_repository(tmp_path)
    source = repo / ('src/fly_brain/' + module.replace('.', '/') + '.py')
    source.write_text('from fly_brain.' + implementation + ' import VALUE\n')
    git(repo, 'add', 'src')
    rejected = commit_document(repo, environment)
    evidence = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert 'DEP001/DEP004' in evidence and '(l.' in evidence
    assert 'fly_brain.' + module in evidence
    assert 'fly_brain.' + implementation in evidence
    source.write_text('from fly_brain.' + neutral + ' import VALUE\n')
    git(repo, 'add', 'src')
    accepted = commit_document(repo, environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    source.write_text('from fly_brain.' + implementation + ' import VALUE\n')
    git(repo, 'add', 'src')
    assert commit_document(repo, environment).returncode != 0
    policy = repo / 'pyproject.toml'
    entry = '    "fly_brain.' + module + '",\n'
    marker = '[[tool.importlinter.contracts]]'
    header, contract, remaining = policy.read_text().split(marker, 2)
    assert contract.count(entry) == 1
    policy.write_text(marker.join((header, contract.replace(entry, '', 1), remaining)))
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr
