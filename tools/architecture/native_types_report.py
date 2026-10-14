from dataclasses import dataclass

from tools.architecture.native_types_records import NativeType, TypedSite


@dataclass(frozen=True)
class NativeTypeReport:
    version: str
    artifacts: tuple[tuple[str, str], ...]
    node_version: str
    python_version: str
    sites: tuple[TypedSite, ...]
    types: tuple[NativeType, ...]
    inputs: tuple[tuple[str, str], ...]

    def type_at(self, site: TypedSite) -> NativeType:
        if site not in self.sites:
            raise ValueError('COV002: native typed site is outside this report')
        return self.types[site.type]

    def require_precise(self, site: TypedSite) -> None:
        """Reject dynamic/unknown effective surfaces; this is not an effect check."""
        self.type_at(site)
        pending = [site.type]
        seen: set[int] = set()
        while pending:
            index = pending.pop()
            if index in seen:
                continue
            seen.add(index)
            node = self.types[index]
            if node.category in ('any', 'unknown', 'unbound'):
                raise ValueError(
                    f'COV002: native {node.category} type at {site.path}:{site.line}:{site.column}'
                )
            if node.category == 'class' and node.unspecialized and node.type_parameters:
                raise ValueError(
                    f'COV002: native unspecialized generic type at {site.path}:{site.line}:{site.column}'
                )
            pending.extend(
                (*node.arguments, *node.members, *node.overloads, *node.constraints)
            )
            pending.extend(item.type for item in node.tuple_arguments)
            pending.extend(
                index
                for item in node.parameters
                for index in (item.type, item.default_type)
                if index is not None
            )
            if node.return_type is not None:
                pending.append(node.return_type)
            if node.bound is not None:
                pending.append(node.bound)
            if node.default_explicit and node.default_type is not None:
                pending.append(node.default_type)
