import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from grimp import ImportGraph
from grimp.exceptions import GrimpException
from importlinter import api
from importlinter.contracts.forbidden import ForbiddenContract
from pydantic import BaseModel, ConfigDict

from tools.architecture.neutral_import_contract import (
    NeutralImportContract,
    modules_option,
)

from .impact import current_graph, module_name


class Configuration(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    session_options: dict[str, str | list[str]]
    contracts_options: list[dict[str, str | list[str]]]


def modules(paths: Sequence[str]) -> set[str]:
    return {
        module_name(path)
        for path in paths
        if path.endswith('.py') and path.startswith('src/fly_brain/')
    }


def expanded(graph: ImportGraph, roots: Sequence[str], *, required: bool) -> set[str]:
    if required and not set(roots) <= graph.modules:
        raise ValueError('COV002: missing configured import-boundary source')
    return {
        name
        for name in graph.modules
        if any(name == root or name.startswith(root + '.') for root in roots)
    }


def review(configuration: Configuration, graph: ImportGraph, affected: set[str]) -> int:
    broken = 0
    evaluated = 0
    for options in configuration.contracts_options:
        name = options.get('name')
        if not isinstance(name, str):
            raise ValueError('COV002: unnamed import contract')
        if options.get('type') == 'neutral_imports':
            contract = NeutralImportContract(
                name, configuration.session_options, options
            )
            scope = expanded(graph, ('fly_brain.comparison',), required=True) & affected
            if not scope:
                continue
            result = contract.check(graph, verbose=False, affected=scope)
        elif options.get('type') == 'forbidden':
            source = expanded(
                graph, modules_option(options.get('source_modules')), required=True
            )
            scope = source & affected
            if not scope:
                continue
            forbidden = expanded(
                graph, modules_option(options.get('forbidden_modules')), required=False
            )
            native = ForbiddenContract(
                name,
                configuration.session_options,
                {
                    **options,
                    'source_modules': sorted(scope),
                    'forbidden_modules': sorted(forbidden),
                    'as_packages': 'false',
                },
            )
            result = native.check(graph, verbose=False)
            contract = native
        else:
            raise ValueError('COV002: unsupported import contract')
        evaluated += len(scope)
        if result.warnings or result.ignored_import_count:
            raise ValueError('COV002: ignored import or native warning')
        print(name + ': ' + ('kept' if result.kept else 'broken'))
        if not result.kept:
            contract.render_broken_contract(result)
            broken += 1
    print(
        f'Import boundaries: {evaluated} affected module/contract checks; {broken} broken.'
    )
    return int(bool(broken))


class Arguments(argparse.Namespace):
    tree: str | None
    paths: list[str]


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tree')
    parser.add_argument('paths', nargs='*')
    options = parser.parse_args(arguments, namespace=Arguments())
    try:
        reader: Callable[[str], object] = vars(api)['read_configuration']
        configuration = Configuration.model_validate(reader('pyproject.toml'))
        session = configuration.session_options
        if modules_option(session.get('root_packages')) != ('fly_brain',):
            raise ValueError('COV002: unexpected import root')
        if str(session.get('include_external_packages')).lower() != 'true':
            raise ValueError('COV002: external import context omitted')
        if (
            str(session.get('exclude_type_checking_imports', 'false')).lower()
            != 'false'
        ):
            raise ValueError('COV002: type-only import context omitted')
        return review(
            configuration,
            current_graph(Path.cwd().resolve(), options.tree),
            modules(options.paths),
        )
    except (OSError, ValueError, GrimpException) as error:
        print('ANALYSIS FAILED: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
