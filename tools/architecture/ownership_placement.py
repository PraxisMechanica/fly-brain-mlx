from pathlib import PurePosixPath

from .inventory import Finding
from .ownership_placement_inputs import domain_scope, location
from .semantic_policy_validation import ValidatedSemanticInputs


def check(inputs: ValidatedSemanticInputs) -> tuple[Finding, ...]:
    """Check OWN001 only; validated metadata is not full semantic compliance."""
    placements = {item.owner: item for item in inputs.document.placement}
    findings: list[Finding] = []
    for binding in domain_scope(inputs):
        placement = placements[binding.owner]
        path = PurePosixPath(binding.symbol.path)
        inside = any(path.is_relative_to(root) for root in placement.roots)
        if not inside and binding.role != placement.outside_role:
            findings.append(
                Finding(
                    'OWN001',
                    binding.symbol.path,
                    binding.anchor.line,
                    f'{location(binding)}: domain {binding.owner} symbol with role '
                    f'{binding.role} is outside reviewed roots {placement.roots}. '
                    'Move the complete owned responsibility into its domain.',
                )
            )
    return tuple(sorted(findings, key=lambda f: (f.path, f.line, f.message)))
