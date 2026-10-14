import pytest
from grimp import ImportGraph

from tools.code_quality.boundaries import Configuration, modules, review


def graph() -> ImportGraph:
    result = ImportGraph()
    for module in (
        'project',
        'project.changed',
        'project.unchanged',
        'project.helper',
        'vendor',
    ):
        result.add_module(module)
    result.add_import(
        importer='project.unchanged',
        imported='vendor',
        line_number=1,
        line_contents='import vendor',
    )
    return result


def configuration() -> Configuration:
    return Configuration(
        session_options={
            'root_packages': ['project'],
            'include_external_packages': 'True',
        },
        contracts_options=[
            {
                'name': 'Owned source boundary',
                'type': 'forbidden',
                'source_modules': ['project'],
                'forbidden_modules': ['vendor'],
            }
        ],
    )


def test_unchanged_debt_is_not_evaluated_when_only_an_independent_module_changes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert review(configuration(), graph(), {'project.changed'}) == 0
    assert '1 affected module/contract checks' in capsys.readouterr().out


def test_affected_transitive_consumer_still_rejects_foreign_dependency() -> None:
    imports = graph()
    imports.add_import(
        importer='project.changed',
        imported='project.helper',
        line_number=1,
        line_contents='from project.helper import VALUE',
    )
    imports.add_import(
        importer='project.helper',
        imported='vendor',
        line_number=1,
        line_contents='import vendor',
    )
    assert review(configuration(), imports, {'project.changed'}) == 1


def test_missing_contract_source_fails_instead_of_producing_an_empty_pass() -> None:
    policy = configuration()
    policy.contracts_options[0]['source_modules'] = ['project.absent']
    with pytest.raises(ValueError, match='COV002'):
        review(policy, graph(), {'project.changed'})


def test_source_modules_preserve_package_initializers_and_exclude_other_files() -> None:
    assert modules(
        (
            'src/fly_brain/example/__init__.py',
            'src/fly_brain/example/rules.py',
            'tests/unit/test_example.py',
            'README.md',
        )
    ) == {'fly_brain.example', 'fly_brain.example.rules'}
