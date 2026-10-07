from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import cast

from .semantic_policy_inputs import exact_path
from .semantic_policy_records import Binding, Record, SymbolKey
from .semantic_policy_schema import SemanticPolicyDocument, require, unique


def index(items: Sequence[Record], label: str) -> dict[str, Record]:
    result: dict[str, Record] = {}
    for item in items:
        identifier = item.__dict__['id']
        require(isinstance(identifier, str), 'invalid ' + label + ' identity')
        require(identifier not in result, 'duplicate ' + label + ': ' + identifier)
        result[identifier] = item
    return result


def symbol_references(value: object) -> tuple[SymbolKey, ...]:
    pending = [value]
    result: list[SymbolKey] = []
    while pending:
        child = pending.pop()
        if isinstance(child, SymbolKey):
            result.append(child)
        elif isinstance(child, Record):
            pending.extend(reversed(tuple(child.__dict__.values())))
        elif isinstance(child, (tuple, list)):
            pending.extend(reversed(cast(Sequence[object], child)))
        elif isinstance(child, dict):
            pending.extend(
                reversed(tuple(cast(Mapping[object, object], child).values()))
            )
    return tuple(result)


def validate_relationships(
    document: SemanticPolicyDocument,
    bindings: Mapping[SymbolKey, Binding],
    tables: Mapping[str, Mapping[str, Record]],
) -> None:
    reference_fields = {
        'Port': {
            'owner': 'owner',
            'public_types': 'export',
            'neutral_errors': 'error',
            'factory_lifetime': 'owner',
        },
        'Slot': {
            'port': 'port',
            'factory': 'constructor',
            'resource': 'resource',
            'lifetime_owner': 'owner',
            'value_owner': 'owner',
            'alias_region': 'region',
        },
        'PublicContract': {
            'owner': 'owner',
            'foreign_types': 'export',
            'identifier_fields': 'identifier',
        },
        'Effect': {
            'artifact': 'artifact',
            'reads': 'region',
            'writes': 'region',
            'aliases': 'region',
            'escapes': 'region',
            'returns': 'region',
            'callbacks': 'port',
            'raises': 'error',
        },
        'Constructor': {
            'port': 'port',
            'factory_slot': 'slot',
            'lifetime_owner': 'owner',
            'initialization_regions': 'region',
        },
        'Resource': {
            'owner': 'owner',
            'lifetime_owner': 'owner',
            'parent': 'resource',
            'public_contracts': 'export',
        },
        'Identifier': {
            'owner': 'owner',
            'resource': 'resource',
            'boundary_slots': 'slot',
        },
        'UseCase': {
            'owner': 'owner',
            'request_contract': 'export',
            'result_contract': 'export',
            'operation_port': 'port',
        },
        'ExternalProvenance': {'summaries': 'effect'},
        'Placement': {'owner': 'owner'},
    }
    records = (
        *document.placement,
        *document.ports,
        *document.consumer_slots,
        *document.public_contracts,
        *document.effects,
        *document.constructors_and_factories,
        *document.resources_and_storage,
        *document.identifiers,
        *document.errors,
        *document.use_cases_and_handlers,
        *document.external_provenance,
    )
    region_ids = tuple(r.id for e in document.effects for r in e.regions)
    unique(region_ids, 'global alias region')
    valid_names = {
        **{key: set(value) for key, value in tables.items()},
        'owner': set(document.owners),
        'artifact': {a.id for a in document.external_provenance},
        'region': set(region_ids),
    }
    for item in records:
        for field, category in reference_fields.get(type(item).__name__, {}).items():
            value = item.__dict__[field]
            values = (value,) if isinstance(value, str) else value or ()
            require(
                set(values) <= valid_names[category],
                'unknown ' + category + ' reference: ' + field,
            )
    placements = {p.owner: p for p in document.placement}
    require(
        all(
            (
                len(placements) == len(document.placement),
                set(placements) == set(document.owners),
            )
        ),
        'owner placement inventory differs',
    )
    for placement in document.placement:
        for path in placement.roots:
            exact_path(Path('/'), path)
    compatible = {
        'neutral_value': 'types',
        'consumer_port': 'ports',
        'business_policy': 'rules',
        'business_service': 'service',
        'owned_repository': 'repository',
        'transport_mechanics': 'command_adapter',
        'provider_mechanics': 'external_adapter',
    }
    for binding in bindings.values():
        placement = placements[binding.owner]
        inside = all(
            (
                not Path(binding.symbol.path).is_absolute(),
                any(
                    PurePosixPath(binding.symbol.path).is_relative_to(p)
                    for p in placement.roots
                ),
            )
        )
        require(
            any((inside, binding.role == placement.outside_role)),
            'binding has no reviewed placement',
        )
        require(
            compatible.get(binding.semantic_kind, binding.role) == binding.role,
            'semantic kind and role differ',
        )
    for port in document.ports:
        require(
            (bindings[port.symbol].role, bindings[port.symbol].owner)
            == ('ports', port.owner),
            'port identity has incompatible role/owner',
        )
        require(
            {(bindings[m].role, bindings[m].owner) for m in port.members}
            == {('ports', port.owner)},
            'port member has implementation role/owner',
        )
    ports = {p.id: p for p in document.ports}
    for slot in document.consumer_slots:
        require(
            slot.symbol.context == slot.consumer.context,
            'slot and consumer context differ',
        )
        if slot.nature == 'collaborator':
            require(
                all(
                    (slot.required, slot.port is not None, bool(slot.capabilities_used))
                ),
                'collaborator needs required narrow port',
            )
            port = ports[str(slot.port)]
            require(
                all(
                    (
                        slot.consumer in port.consumers,
                        set(slot.capabilities_used) <= set(port.members),
                        bindings[slot.consumer].owner == port.owner,
                    )
                ),
                'slot capability/consumer differs from port',
            )
        else:
            require(
                (slot.port, slot.factory, slot.capabilities_used) == (None, None, ()),
                'plain value conceals collaborator contract',
            )
    for export in document.public_contracts:
        role = 'types' if export.kind == 'value' else 'ports'
        require(
            all(
                (
                    bindings[export.symbol].role == role,
                    bindings[export.symbol].owner == export.owner,
                )
            ),
            'public contract has implementation role/owner',
        )
        members = (*export.members, *export.member_types, *export.reexports)
        require(
            {bindings[s].role for s in members} <= {'types', 'ports'},
            'public member/type/reexport leaks implementation',
        )
        permitted = {
            s
            for c in document.public_contracts
            if c.id in export.foreign_types
            for s in (c.symbol, *c.members)
        }
        require(
            all(bindings[s].owner == export.owner or s in permitted for s in members),
            'public contract references foreign private type/member',
        )
    for effect in document.effects:
        regions = {r.id: r for r in effect.regions}
        require(
            set(
                (
                    *effect.reads,
                    *effect.writes,
                    *effect.aliases,
                    *effect.escapes,
                    *effect.returns,
                )
            )
            <= set(regions),
            'summary region belongs to another effect',
        )
        if 'pure' in effect.categories:
            require(
                all(
                    (
                        effect.categories == ('pure',),
                        {regions[r].kind for r in effect.writes}
                        <= {'fresh_local', 'unescaped_initialization'},
                    )
                ),
                'pure summary declares external effect/mutation',
            )
    slots = {s.id: s for s in document.consumer_slots}
    for constructor in document.constructors_and_factories:
        require(
            {bindings[s].role for s in constructor.assembly_sites}
            <= {'module', 'composition'},
            'constructor assembly site has nonassembly role',
        )
        if constructor.category in ('collaborator', 'generic_resource'):
            require(
                all(
                    (
                        constructor.lifetime_owner is not None,
                        any(
                            (
                                bool(constructor.assembly_sites),
                                constructor.factory_slot is not None,
                            )
                        ),
                    )
                ),
                'constructor needs explicit factory/assembly lifetime',
            )
            if constructor.factory_slot is not None:
                slot = slots[constructor.factory_slot]
                require(
                    (slot.nature, slot.required, slot.factory, slot.lifetime_owner)
                    == (
                        'collaborator',
                        True,
                        constructor.id,
                        constructor.lifetime_owner,
                    ),
                    'factory slot/lifetime does not bind constructor',
                )
        if constructor.category == 'owned_value':
            require(
                bindings[constructor.produced_type].role == 'types',
                'owned constructor produces implementation',
            )
    by_resource = {r.id: r for r in document.resources_and_storage}
    for resource in document.resources_and_storage:
        require(
            (resource.relationship == 'storage_only') == (resource.parent is not None),
            'invalid resource parent relationship',
        )
        seen = {resource.id}
        current = resource
        while current.parent is not None:
            parent = by_resource[current.parent]
            require(
                all((parent.id not in seen, parent.owner == resource.owner)),
                'resource parent cycle or foreign owner',
            )
            seen.add(parent.id)
            current = parent
    for identifier in document.identifiers:
        require(
            (
                identifier.owner,
                bindings[identifier.distinct_type].role,
                bindings[identifier.distinct_type].owner,
            )
            == (by_resource[identifier.resource].owner, 'types', identifier.owner),
            'identifier resource/type ownership differs',
        )
    for error in document.errors:
        require(
            (error.model == 'infallible') == (error.disposition == 'infallible'),
            'incompatible failure disposition',
        )
        require(
            {bindings[s].role for s in error.error_types} <= {'types', 'ports'},
            'raw implementation error leak',
        )
    for use_case in document.use_cases_and_handlers:
        require(
            (
                bindings[use_case.operation].role,
                bindings[use_case.handler].role,
                bindings[use_case.operation].owner,
                bindings[use_case.handler].owner,
            )
            == ('service', 'command_adapter', use_case.owner, use_case.owner),
            'use case/handler has incompatible role/owner',
        )
