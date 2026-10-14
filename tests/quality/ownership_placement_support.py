import hashlib
from collections.abc import Mapping
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

from tests.quality.support import PROJECT
from tests.quality.test_architecture_symbols import semantic_model
from tools.architecture.policy import Owner, Role
from tools.architecture.semantic_policy_records import (
    Applicability,
    Binding,
    Context,
    ExternalProvenance,
    Input,
    NativeAnchor,
    NativeObservation,
    ObservedArtifact,
    Placement,
)
from tools.architecture.semantic_policy_schema import CATALOG, SemanticPolicyDocument
from tools.architecture.semantic_policy_validation import (
    ValidatedSemanticInputs,
    observed_bindings,
    validate_semantic_inputs,
)

SOURCE = 'class Value: pass\n\ndef policy(value: Value) -> Value:\n    return value\n'
ROOTS = ('src/owned', 'tests/owned', 'docs/owned')


def native_inputs(
    root: Path,
    files: Mapping[str, str],
    *,
    role: Role = 'types',
    outside_role: str | None = None,
) -> tuple[ValidatedSemanticInputs, NativeObservation]:
    model = semantic_model(root, files)
    facts = observed_bindings('active', model)
    executable = (PROJECT / '.venv/bin/pyright-langserver').resolve()
    artifact = ObservedArtifact(
        absolute_path=str(executable),
        sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        distribution='pyright',
        version=version('pyright'),
    )
    document = SemanticPolicyDocument(
        version=2,
        owners={
            'example': Owner(kind='domain', responsibility='Reviewed fixture values')
        },
        contexts=(
            Context(
                id='active',
                languages=('python',),
                sources=tuple(
                    Input(path=s.path, sha256=s.sha256) for s in model.sources
                ),
                artifacts=('compiler',),
                expected_bindings=tuple(facts),
                build_variant='source-only',
            ),
        ),
        placement=(
            Placement.model_validate(
                {'owner': 'example', 'roots': ROOTS, 'outside_role': outside_role}
            ),
        ),
        semantic_bindings=tuple(
            Binding(
                symbol=key,
                anchor=NativeAnchor(
                    source_sha256=symbol.provenance.sha256,
                    artifact='compiler',
                    line=symbol.location.line,
                    column=symbol.location.column,
                    end_line=symbol.location.end_line,
                    end_column=symbol.location.end_column,
                ),
                owner='example',
                role=role,
                phase='declaration',
                semantic_kind='test_or_analysis',
                evidence='Explicit fixture classification, independent of filename and code.',
            )
            for key, symbol in facts.items()
        ),
        consumer_slots=(),
        ports=(),
        public_contracts=(),
        effects=(),
        constructors_and_factories=(),
        use_cases_and_handlers=(),
        resources_and_storage=(),
        identifiers=(),
        errors=(),
        applicability=tuple(
            Applicability(
                rule=rule,
                context='active',
                scope=tuple(facts),
                required_capabilities=('declaration_identity',),
            )
            for rule in CATALOG
        ),
        external_provenance=(
            ExternalProvenance(
                id='compiler',
                absolute_path=artifact.absolute_path,
                sha256=artifact.sha256,
                distribution=artifact.distribution,
                version=artifact.version,
                binary_or_generated='Observed locked compiler; no source-placement exemption.',
            ),
        ),
    )
    observation = NativeObservation(model, (), (artifact,))
    return validate_semantic_inputs(
        root, document, {'active': observation}
    ), observation


def policy_binding(inputs: ValidatedSemanticInputs) -> Binding:
    return next(
        b for b in inputs.bindings.values() if b.symbol.qualified_name == 'policy'
    )


def without_policy_scope(inputs: ValidatedSemanticInputs) -> ValidatedSemanticInputs:
    symbol = policy_binding(inputs).symbol
    rules = tuple(
        rule.model_copy(
            update={'scope': tuple(key for key in rule.scope if key != symbol)}
        )
        if rule.rule == 'OWN001'
        else rule
        for rule in inputs.document.applicability
    )
    return replace(
        inputs, document=inputs.document.model_copy(update={'applicability': rules})
    )
