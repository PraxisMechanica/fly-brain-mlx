from pathlib import Path

import pytest

from tests.quality.support import git
from tests.quality.test_changed_checks import FACADE, USE, VALUES, write
from tests.quality.test_changed_checks import checkout as checkout
from tools.code_quality import changes
from tools.code_quality.changes import Stage, build_plan


@pytest.mark.parametrize('stage', ('push', 'ci'))
@pytest.mark.parametrize('merge_configuration', ('off', 'first-parent'))
def test_merge_parent_preserves_source_and_nul_safe_paths_at_unchanged_endpoint(
    checkout: Path, stage: Stage, merge_configuration: str
) -> None:
    git(checkout, 'config', 'log.diffMerges', merge_configuration)
    ancestor = git(checkout, 'rev-parse', 'HEAD')
    original_tree = git(checkout, 'rev-parse', 'HEAD^{tree}')
    note = 'notes/λ\nname.txt'
    write(checkout, VALUES, 'VALUE = 2\n')
    write(checkout, note, 'native path fixture\n')
    git(checkout, 'commit', '-qm', 'Declare first parent source')
    base = git(checkout, 'rev-parse', 'HEAD')
    current_tree = git(checkout, 'rev-parse', 'HEAD^{tree}')
    second = git(
        checkout, 'commit-tree', original_tree, '-p', ancestor, '-m', 'Second parent'
    )
    second = git(
        checkout, 'commit-tree', original_tree, '-p', second, '-m', 'Second lineage'
    )
    head = git(
        checkout,
        'commit-tree',
        current_tree,
        '-p',
        base,
        '-p',
        second,
        '-m',
        'Merge unchanged first parent',
    )
    git(checkout, 'update-ref', 'HEAD', head, base)
    plan = build_plan(
        checkout, stage, dict(zip(changes.RANGES[stage], (base, head), strict=True))
    )
    assert (
        git(checkout, 'diff', '--name-only', base, head),
        plan.changed,
        set(plan.python),
        plan.tree,
    ) == (
        '',
        tuple(sorted((VALUES, note))),
        {VALUES, FACADE, USE, 'main.py'},
        current_tree,
    )


@pytest.mark.parametrize('stage', ('push', 'ci'))
def test_distinct_refs_without_submitted_commits_fail_closed(
    checkout: Path, stage: Stage
) -> None:
    head = git(checkout, 'rev-parse', 'HEAD')
    tree = git(checkout, 'rev-parse', 'HEAD^{tree}')
    base = git(checkout, 'commit-tree', tree, '-p', head, '-m', 'Future descendant')
    with pytest.raises(ValueError, match='COV002: submitted range is empty'):
        build_plan(
            checkout,
            stage,
            dict(zip(changes.RANGES[stage], (base, head), strict=True)),
        )
