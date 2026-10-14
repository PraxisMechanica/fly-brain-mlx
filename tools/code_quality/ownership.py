"""Protected scientific source identities; ordinary bindings are review inputs."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.architecture.inventory import Finding, discover
from tools.architecture.policy import load_policy

POLICY = 'tools/architecture/ownership.json'
PROTECTED = (
    'src/fly_brain/qualification/adapters/brian_reference.py',
    'src/fly_brain/qualification/adapters/torch_reference.py',
    'src/fly_brain/qualification/reference_parameters.py',
    'tests/support/legacy_mlx_ledger.py',
    'tests/support/legacy_mlx_observer.py',
)


def review(root: Path) -> tuple[Finding, ...]:
    policy = load_policy(root / POLICY)
    guards = {
        path: row.frozen.sha256
        for path, row in policy.files.items()
        if row.frozen is not None
    }
    if set(guards) != set(PROTECTED):
        raise ValueError('COV002: protected scientific source inventory changed')
    sources = discover(root, PROTECTED)
    findings = tuple(
        Finding('COV001', source.path, 1, 'Protected scientific source hash changed')
        for source in sources
        if source.sha256 != guards[source.path]
    )
    print(f'Source integrity: {len(sources)} protected scientific sources checked.')
    return findings


def main(arguments: Sequence[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(arguments)
    try:
        findings = review(Path.cwd().resolve())
    except (OSError, ValueError) as error:
        print('ANALYSIS FAILED: ' + str(error), file=sys.stderr)
        return 2
    for finding in findings:
        print(
            f'{finding.rule}: {finding.path}:{finding.line}: {finding.message}',
            file=sys.stderr,
        )
    return int(bool(findings))


if __name__ == '__main__':
    sys.exit(main())
