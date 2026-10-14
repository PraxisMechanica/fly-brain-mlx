from .semantic_policy_records import Binding
from .semantic_policy_validation import ValidatedSemanticInputs


def _location(binding: Binding) -> str:
    symbol, anchor = binding.symbol, binding.anchor
    return (
        f'{symbol.path}:{anchor.line}:{anchor.column} '
        f'[{symbol.context}:{symbol.qualified_name}:'
        f'{symbol.native_kind}:{symbol.occurrence}]'
    )


def _require(binding: Binding, condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f'COV002: OWN001 {_location(binding)}: {message}')


def _domain_scope(inputs: ValidatedSemanticInputs) -> tuple[Binding, ...]:
    document = inputs.document
    if not inputs.bindings:
        raise ValueError('COV002: OWN001 <policy>:1:0: observed binding scope is empty')
    first = next(iter(inputs.bindings.values()))
    _require(
        first,
        'declaration_identity' not in inputs.missing_capabilities,
        'native declaration identity is incomplete',
    )
    expected = {b.symbol: b for b in document.semantic_bindings}
    _require(
        first,
        dict(inputs.bindings) == expected,
        'validated binding inventory differs from reviewed identities',
    )
    contexts = {c.id: c for c in document.contexts}
    _require(
        first,
        {key for c in document.contexts for key in c.expected_bindings}
        == set(inputs.bindings),
        'observed context binding coverage differs',
    )
    scopes = {
        rule.context: set(rule.scope)
        for rule in document.applicability
        if rule.rule == 'OWN001'
    }
    _require(first, set(scopes) == set(contexts), 'OWN001 context scope is missing')
    placements = {p.owner: p for p in document.placement}
    _require(
        first,
        set(placements) == set(document.owners),
        'reviewed owner placement inventory differs',
    )
    selected: list[Binding] = []
    for key, binding in inputs.bindings.items():
        _require(binding, key == binding.symbol, 'binding key and identity differ')
        _require(binding, binding.owner in document.owners, 'unknown reviewed owner')
        _require(binding, key.context in contexts, 'unknown native context')
        if document.owners[binding.owner].kind != 'domain':
            continue
        context = contexts[key.context]
        _require(
            binding,
            key.path in {item.path for item in context.sources},
            'domain placement lacks first-party source observation',
        )
        _require(
            binding,
            inputs.input_hashes.get(key.path) == binding.anchor.source_sha256,
            'validated source hash and native anchor differ',
        )
        _require(
            binding,
            key in scopes[key.context],
            'domain binding omitted from OWN001 scope',
        )
        selected.append(binding)
    _require(first, bool(selected), 'intended domain placement scope is empty')
    return tuple(selected)


domain_scope = _domain_scope
location = _location
