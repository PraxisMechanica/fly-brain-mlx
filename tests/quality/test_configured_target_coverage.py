from collections.abc import Sequence
from pathlib import Path

import pytest
from grimp import ImportGraph

from tests.quality.test_incremental_boundary import configuration, graph
from tools.code_quality import boundaries
from tools.code_quality.boundaries import review


@pytest.mark.parametrize('target', ('project.absent', 'tests.absent', 'tools.absent'))
@pytest.mark.parametrize('affected', ({'project.changed'}, set[str]()))
def test_first_party_targets_require_exact_context_even_for_inactive_sources(
    target: str, affected: set[str]
) -> None:
    policy = configuration()
    policy.session_options['root_packages'] = ['project', 'tests', 'tools']
    policy.contracts_options[0]['forbidden_modules'] = [target]
    imports = graph()
    imports.add_module(target + '.child')
    with pytest.raises(ValueError, match='COV002:.*target: ' + target):
        review(policy, imports, affected)
    imports.add_module(target)
    assert review(policy, imports, affected) == 0


@pytest.mark.parametrize(
    'target',
    ('vendor.absent', 'projectish.absent', 'testsuite.absent', 'toolshed.absent'),
)
def test_absent_external_targets_and_similar_first_party_prefixes_stay_optional(
    target: str,
) -> None:
    policy = configuration()
    policy.contracts_options[0]['forbidden_modules'] = [target]
    assert review(policy, graph(), {'project.changed'}) == 0


@pytest.mark.parametrize(
    'imported,expected',
    (
        ('project.target', 1),
        ('project.target.child', 1),
        ('project.targetish', 0),
        ('project.targetish.child', 0),
    ),
)
def test_forbidden_target_expansion_keeps_exact_roots_and_descendants_only(
    imported: str, expected: int
) -> None:
    policy = configuration()
    policy.contracts_options[0]['forbidden_modules'] = ['project.target']
    imports = graph()
    for name in ('project.target', 'project.target.child', imported):
        imports.add_module(name)
    imports.add_import(
        importer='project.changed',
        imported=imported,
        line_number=1,
        line_contents='import ' + imported,
    )
    assert review(policy, imports, {'project.changed'}) == expected


def test_removing_only_target_presence_guard_restores_the_same_false_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = configuration()
    policy.contracts_options[0]['forbidden_modules'] = ['project.absent']
    with pytest.raises(ValueError, match='COV002:.*target: project.absent'):
        review(policy, graph(), {'project.changed'})

    def ignored(targets: Sequence[str], first_party: Sequence[str]) -> tuple[str, ...]:
        return ()

    monkeypatch.setattr(boundaries, 'required_targets', ignored)
    assert review(policy, graph(), {'project.changed'}) == 0
    policy.contracts_options[0]['source_modules'] = ['project.absent_source']
    with pytest.raises(ValueError, match='COV002:.*source'):
        review(policy, graph(), {'project.changed'})


def test_native_configuration_target_change_fails_runner_with_analysis_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    policy = tmp_path / 'pyproject.toml'
    policy.write_text(
        '[tool.importlinter]\nroot_package="fly_brain"\ninclude_external_packages=true\n'
        '[[tool.importlinter.contracts]]\nname="Coverage boundary"\ntype="forbidden"\n'
        'source_modules=["fly_brain.changed"]\nforbidden_modules=["vendor.absent"]\n'
    )
    imports = ImportGraph()
    imports.add_module('fly_brain')
    imports.add_module('fly_brain.changed')

    def current(root: Path, tree: str | None) -> ImportGraph:
        return imports

    monkeypatch.setattr(boundaries, 'current_graph', current)
    assert boundaries.main(['src/fly_brain/changed.py']) == 0
    policy.write_text(policy.read_text().replace('vendor.absent', 'fly_brain.absent'))
    assert boundaries.main(['src/fly_brain/changed.py']) == 2
    assert (
        'COV002: missing configured first-party import-boundary target: fly_brain.absent'
        in capsys.readouterr().err
    )
