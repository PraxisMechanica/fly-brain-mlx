from grimp import ImportGraph


def source_scope(
    graph: ImportGraph,
    source_root: str,
    foreign_roots: tuple[str, ...],
    neutral_modules: tuple[str, ...],
    affected: set[str] | None,
) -> tuple[list[str], list[str]]:
    required = {source_root, *foreign_roots[:2], *neutral_modules}
    if not required <= graph.modules:
        raise ValueError('COV002: missing comparison/foreign/neutral scope')
    descendants: set[str] = (
        graph.find_descendants(source_root)
        if not graph.is_module_squashed(source_root)
        else set()
    )
    source = sorted({source_root, *descendants})
    if len(source) < 2:
        raise ValueError('COV002: empty comparison scope')
    foreign: set[str] = set()
    for root in set(foreign_roots) & graph.modules:
        foreign.add(root)
        if not graph.is_module_squashed(root):
            foreign.update(graph.find_descendants(root))
    internal = foreign - set(foreign_roots[2:])
    if any(graph.is_module_squashed(m) for m in (*source, *internal)):
        raise ValueError('COV002: squashed internal module inventory')
    if affected is not None:
        source = sorted(set(source) & affected)
    forbidden = sorted(foreign - set(neutral_modules))
    return source, forbidden
