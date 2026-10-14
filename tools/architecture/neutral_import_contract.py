from collections.abc import Mapping

from grimp import ImportGraph
from importlinter.application import output
from importlinter.contracts.forbidden import ForbiddenContract
from importlinter.domain.contract import Contract, ContractCheck, InvalidContractOptions
from pydantic import TypeAdapter

SOURCE_ROOT = 'fly_brain.comparison'
FOREIGN_ROOTS = (
    'fly_brain.simulation',
    'fly_brain.qualification',
    'mlx',
    'brian2',
    'torch',
)
NEUTRAL_MODULES = ('fly_brain.simulation.identifiers',)


def modules_option(value: object) -> tuple[str, ...]:
    return tuple(TypeAdapter(list[str]).validate_python(value, strict=True))


class NeutralImportContract(Contract):
    type_name = 'neutral_imports'

    def validate(self) -> None:
        try:
            options: Mapping[str, object] = self.contract_options
            checks = (
                (
                    not set(options)
                    - {
                        'name',
                        'type',
                        'id',
                        'source_root',
                        'foreign_roots',
                        'neutral_modules',
                    },
                    'unknown contract field',
                ),
                (options.get('source_root') == SOURCE_ROOT, 'source root differs'),
                (
                    sorted(modules_option(options.get('foreign_roots')))
                    == sorted(FOREIGN_ROOTS),
                    'foreign root inventory differs',
                ),
                (
                    modules_option(options.get('neutral_modules')) == NEUTRAL_MODULES,
                    'neutral module inventory differs',
                ),
                (
                    modules_option(self.session_options.get('root_packages'))
                    == ('fly_brain',),
                    'native root package inventory differs',
                ),
                (
                    str(self.session_options.get('include_external_packages')).lower()
                    == 'true',
                    'external imports must be included',
                ),
                (
                    str(
                        self.session_options.get(
                            'exclude_type_checking_imports', 'false'
                        )
                    ).lower()
                    == 'false',
                    'type-only imports must be included',
                ),
            )
            for valid, message in checks:
                if not valid:
                    raise ValueError(message)
        except ValueError as error:
            raise InvalidContractOptions(
                {'boundary': 'COV002: ' + str(error)}
            ) from error

    def check(self, graph: ImportGraph, verbose: bool) -> ContractCheck:
        required = {SOURCE_ROOT, *FOREIGN_ROOTS[:2], *NEUTRAL_MODULES}
        if not required <= graph.modules:
            raise ValueError('COV002: missing comparison/foreign/neutral scope')
        descendants: set[str] = (
            graph.find_descendants(SOURCE_ROOT)
            if not graph.is_module_squashed(SOURCE_ROOT)
            else set()
        )
        source = sorted({SOURCE_ROOT, *descendants})
        if len(source) < 2:
            raise ValueError('COV002: empty comparison scope')
        foreign: set[str] = set()
        for root in set(FOREIGN_ROOTS) & graph.modules:
            foreign.add(root)
            if not graph.is_module_squashed(root):
                foreign.update(graph.find_descendants(root))
        internal = foreign - set(FOREIGN_ROOTS[2:])
        if any(graph.is_module_squashed(m) for m in (*source, *internal)):
            raise ValueError('COV002: squashed internal module inventory')
        forbidden = sorted(foreign - set(NEUTRAL_MODULES))
        native = ForbiddenContract(
            self.name,
            self.session_options,
            {
                'source_modules': source,
                'forbidden_modules': forbidden,
                'as_packages': 'false',
                'allow_indirect_imports': 'false',
            },
        )
        result = native.check(graph, verbose=verbose)
        if result.ignored_import_count or result.warnings:
            raise ValueError('COV002: native contract ignored imports or warned')
        return result

    def render_broken_contract(self, check: ContractCheck) -> None:
        output.print_error('DEP003: comparison reaches a foreign execution module.')
        ForbiddenContract(
            self.name,
            self.session_options,
            {'source_modules': [SOURCE_ROOT], 'forbidden_modules': list(FOREIGN_ROOTS)},
        ).render_broken_contract(check)
