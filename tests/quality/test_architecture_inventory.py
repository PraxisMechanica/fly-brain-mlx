import ast
import inspect
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import cast

import pytest

from tools.architecture.inventory import Finding, Ownership, Source, discover, reconcile

pytestmark = pytest.mark.unit


def test_new_source_and_nested_declarations_cannot_escape_reviewed_ownership(
    tmp_path: Path,
) -> None:
    source = tmp_path / 'service.py'
    source.write_text('def run():\n    return 1\n')
    policy = {'service.py': Ownership('simulation', 'service', ('run',))}
    assert not reconcile(discover(tmp_path, ('service.py',)), policy)
    source.write_text(
        'def run():\n    def hidden():\n        return 1\n    return hidden()\n'
    )
    findings = reconcile(discover(tmp_path, ('service.py',)), policy)
    assert [(f.rule, f.path, f.line) for f in findings] == [('COV001', 'service.py', 2)]
    repaired = {'service.py': Ownership('simulation', 'service', ('run', 'run.hidden'))}
    assert not reconcile(discover(tmp_path, ('service.py',)), repaired)


def test_ignored_source_is_still_discovered_and_has_to_be_owned(tmp_path: Path) -> None:
    directory = tmp_path / 'src'
    directory.mkdir()
    (directory / 'owned.py').write_text('class Value:\n    pass\n')
    policy = {'src/owned.py': Ownership('simulation', 'value', ('Value',))}
    (directory / '.new.py').write_text('def action():\n    pass\n')
    findings = reconcile(discover(tmp_path, ('src',)), policy)
    assert [(f.rule, f.path) for f in findings] == [('COV001', 'src/.new.py')]


def test_frozen_evidence_source_cannot_change_behind_a_preserved_classification(
    tmp_path: Path,
) -> None:
    source = tmp_path / 'proof.py'
    source.write_text('def verify():\n    return True\n')
    before = discover(tmp_path, ('proof.py',))
    policy = {
        'proof.py': Ownership(
            'qualification', 'evidence', ('verify',), before[0].sha256
        )
    }
    assert not reconcile(before, policy)
    source.write_text('def verify():\n    return False\n')
    findings = reconcile(discover(tmp_path, ('proof.py',)), policy)
    assert [(f.rule, f.path) for f in findings] == [('COV001', 'proof.py')]
    assert 'provenance changed' in findings[0].message


@pytest.mark.parametrize('roots', ((), ('missing',)))
def test_missing_or_empty_scopes_are_analysis_failures(
    tmp_path: Path, roots: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError, match='COV002'):
        discover(tmp_path, roots)


def test_parser_failure_is_never_an_empty_clean_result(tmp_path: Path) -> None:
    (tmp_path / 'broken.py').write_text('def broken(')
    with pytest.raises(ValueError, match='COV002: broken.py:1: parse failed'):
        discover(tmp_path, ('broken.py',))


@pytest.mark.parametrize(
    'case,prefix',
    (
        ('unowned', 'Source has no reviewed owner/role'),
        ('declaration', 'Unclassified declaration:'),
        ('artifact', 'Frozen artifact provenance changed'),
        ('blank-owner', 'Source owner/role is empty'),
        ('missing-source', 'Mapped source is absent from discovery'),
        ('missing-declaration', 'Mapped declaration is absent:'),
    ),
)
def test_removing_each_diagnostic_hides_its_real_coverage_violation(
    tmp_path: Path, case: str, prefix: str
) -> None:
    (tmp_path / 'service.py').write_text('def run():\n    return 1\n')
    sources = discover(tmp_path, ('service.py',))
    policy = {
        'service.py': Ownership(
            '' if case == 'blank-owner' else 'simulation',
            'service',
            ()
            if case == 'declaration'
            else ('run', 'missing')
            if case == 'missing-declaration'
            else ('run',),
            'wrong-hash' if case == 'artifact' else None,
        )
    }
    if case == 'unowned':
        policy = {}
    elif case == 'missing-source':
        policy['missing.py'] = Ownership('simulation', 'rules', ('calculate',))
    assert reconcile(sources, policy)
    tree = ast.parse(inspect.getsource(reconcile))

    class RemoveDiagnostic(ast.NodeTransformer):
        def visit_Expr(self, node: ast.Expr) -> ast.AST:
            if any(
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and value.value.startswith(prefix)
                for value in ast.walk(node)
            ):
                return ast.copy_location(ast.Pass(), node)
            return node

    tree = ast.fix_missing_locations(RemoveDiagnostic().visit(tree))
    namespace = dict(reconcile.__globals__)
    exec(compile(tree, '<weakened-reconciliation>', 'exec'), namespace)
    weakened = cast(
        Callable[[Sequence[Source], Mapping[str, Ownership]], tuple[Finding, ...]],
        namespace['reconcile'],
    )
    assert not weakened(sources, policy)


def test_module_contracts_and_class_fields_are_declarations_not_just_functions(
    tmp_path: Path,
) -> None:
    (tmp_path / 'values.py').write_text(
        'Identifier = int\nclass Record:\n    identifier: Identifier\n'
        '    def build(self):\n        scratch = 1\n        return scratch\n'
    )
    source = discover(tmp_path, ('values.py',))[0]
    assert {item.name for item in source.declarations} == {
        'Identifier',
        'Record',
        'Record.identifier',
        'Record.build',
    }


def test_an_empty_second_root_cannot_hide_behind_a_populated_first_root(
    tmp_path: Path,
) -> None:
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src/value.py').write_text('value = 1\n')
    (tmp_path / 'typings').mkdir()
    with pytest.raises(
        ValueError, match='COV002: intended source scope is empty: typings'
    ):
        discover(tmp_path, ('src', 'typings'))
    (tmp_path / 'typings/contract.pyi').write_text('def operation() -> int: ...\n')
    assert {item.path for item in discover(tmp_path, ('src', 'typings'))} == {
        'src/value.py',
        'typings/contract.pyi',
    }


def test_source_root_cannot_reach_outside_the_reviewed_workspace(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'project'
    root.mkdir()
    (tmp_path / 'outside.py').write_text('value = 1\n')
    with pytest.raises(ValueError, match='COV002: source root escapes workspace'):
        discover(root, ('../outside.py',))
    (root / 'inside.py').write_text('value = 1\n')
    assert discover(root, ('inside.py',))[0].path == 'inside.py'


def test_nested_source_directory_symlink_cannot_silently_disappear(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'project'
    root.mkdir()
    (root / 'value.py').write_text('value = 1\n')
    outside = tmp_path / 'foreign'
    outside.mkdir()
    (outside / 'service.py').write_text('def execute(): pass\n')
    (root / 'alias').symlink_to(outside, target_is_directory=True)
    with pytest.raises(
        ValueError, match='COV002: unsupported source directory symlink'
    ):
        discover(root, ('.',))


@pytest.mark.parametrize(
    'owner,role', (('', 'service'), ('domain', ''), (' ', 'service'))
)
def test_blank_owner_or_role_is_unclassified_source(
    tmp_path: Path, owner: str, role: str
) -> None:
    (tmp_path / 'service.py').write_text('def run(): return 1\n')
    sources = discover(tmp_path, ('service.py',))
    findings = reconcile(sources, {'service.py': Ownership(owner, role, ('run',))})
    assert [(item.rule, item.path, item.line, item.message) for item in findings] == [
        ('COV001', 'service.py', 1, 'Source owner/role is empty')
    ]
    assert not reconcile(
        sources, {'service.py': Ownership('simulation', 'service', ('run',))}
    )


def test_mapped_but_absent_source_is_not_silently_dropped(tmp_path: Path) -> None:
    (tmp_path / 'service.py').write_text('def run(): return 1\n')
    sources = discover(tmp_path, ('service.py',))
    policy = {
        'service.py': Ownership('simulation', 'service', ('run',)),
        'missing.py': Ownership('simulation', 'rules', ('calculate',)),
    }
    findings = reconcile(sources, policy)
    assert [(item.rule, item.path, item.line) for item in findings] == [
        ('COV001', 'missing.py', 1)
    ]
    assert not reconcile(sources, {'service.py': policy['service.py']})


def test_empty_reconciliation_cannot_be_a_clean_owner_report() -> None:
    with pytest.raises(
        ValueError, match='COV002: ownership reconciliation scope is empty'
    ):
        reconcile((), {})
