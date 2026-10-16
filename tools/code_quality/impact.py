"""Current native import context; no historical graph or runtime-dispatch proof."""

from dataclasses import dataclass
from pathlib import Path

import grimp
from grimp.adaptors.caching import Cache
from grimp.adaptors.filesystem import FileSystem
from grimp.adaptors.modulefinder import ModuleFinder
from grimp.application.config import settings
from grimp.application.ports.filesystem import AbstractFileSystem
from grimp.application.ports.packagefinder import AbstractPackageFinder

PACKAGES = {'fly_brain': 'src/fly_brain', 'tests': 'tests', 'tools': 'tools'}


@dataclass(frozen=True)
class SourceFinder(AbstractPackageFinder):
    root: Path

    def determine_package_directories(
        self, package_name: str, file_system: AbstractFileSystem
    ) -> set[str]:
        directory = self.root / PACKAGES[package_name]
        if not directory.is_dir() or directory.resolve() != directory:
            raise ValueError('COV002: missing or linked canonical package')
        return {str(directory)}


def module_name(path: str) -> str:
    return (
        path.removeprefix('src/')
        .removesuffix('.py')
        .replace('/', '.')
        .removesuffix('.__init__')
    )


def current_graph(root: Path, tree: str | None) -> grimp.ImportGraph:
    """Use explicit directories, never editable package or sys.modules discovery.

    The cache consumer is current-plan dependency traversal. Its tree-keyed output
    lives under executions/quality-cache/imports and survives routine log cleanup.
    Manual/unindexed working inputs use a fresh scan. No previous-context claim.
    """
    previous: object = settings.PACKAGE_FINDER
    filesystem: object = settings.FILE_SYSTEM
    modulefinder: object = settings.MODULE_FINDER
    native: tuple[object, ...] = (
        grimp.__version__,
        type(filesystem),
        type(modulefinder),
        settings.CACHE_CLASS,
        settings.IMPORT_GRAPH_CLASS,
    )
    if native != (
        '3.17',
        FileSystem,
        ModuleFinder,
        Cache,
        grimp.ImportGraph,
    ) or not isinstance(previous, AbstractPackageFinder):
        raise ValueError('COV002: unsupported native import context')
    settings.configure(PACKAGE_FINDER=SourceFinder(root))
    try:
        return grimp.build_graph(
            *PACKAGES,
            include_external_packages=True,
            exclude_type_checking_imports=False,
            cache_dir=str(
                root / 'executions/quality-cache/imports' / ('grimp-3.17-' + tree)
            )
            if tree
            else None,
        )
    finally:
        settings.configure(PACKAGE_FINDER=previous)
