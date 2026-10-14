import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from tools.architecture.inventory import Finding
from tools.architecture.policy import (
    Policy,
    load_policy,
    parse_policy,
)
from tools.architecture.policy_review import review_policy

POLICY = 'tools/architecture/ownership.json'


def baseline(base: str) -> Policy | None:
    subprocess.run(
        ['git', 'rev-parse', '--verify', base], check=True, capture_output=True
    )
    probe = subprocess.run(
        ['git', 'cat-file', '-e', f'{base}:{POLICY}'], capture_output=True, check=False
    )
    if probe.returncode:
        return None
    content = subprocess.check_output(['git', 'show', f'{base}:{POLICY}'], text=True)
    return parse_policy(content)


def affected(
    current: Policy, previous: Policy | None, changed: Sequence[str]
) -> set[str]:
    selected = set(changed) & current.files.keys()
    if (
        previous is None
        or current.document.source_roots != previous.document.source_roots
    ):
        return set(current.files)
    selected.update(
        path for path, row in current.files.items() if row != previous.files.get(path)
    )
    if current.document.owners != previous.document.owners:
        selected.update(current.files)
    if (
        current.document.resources,
        current.document.identifiers,
        current.document.absences,
        current.document.findings,
    ) != (
        previous.document.resources,
        previous.document.identifiers,
        previous.document.absences,
        previous.document.findings,
    ):
        for policy in (previous, current):
            selected.update(
                symbol.path
                for item in (
                    *policy.document.resources.values(),
                    *policy.document.identifiers.values(),
                )
                for symbol in item.evidence
            )
            selected.update(item.symbol.path for item in policy.document.findings)
            selected.update(
                path
                for item in policy.document.absences.values()
                for path in item.evidence
            )
    return selected & current.files.keys()


def review(root: Path, base: str, changed: Sequence[str]) -> tuple[Finding, ...]:
    current = load_policy(root / POLICY)
    selected = affected(current, baseline(base), changed)
    result = review_policy(root, current, source_scope=tuple(sorted(selected)))
    print(
        f'Ownership: {len(result.sources)} affected sources checked; '
        f'{len(current.files) - len(result.sources)} unchanged source records retained; '
        f'{len(result.recorded_findings)} recorded findings. '
        'Complete 37-rule analysis remains incomplete.'
    )
    return result.findings


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', required=True)
    parser.add_argument('changed', nargs='*')
    options = parser.parse_args(arguments)
    try:
        findings = review(Path.cwd().resolve(), options.base, options.changed)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print('ANALYSIS FAILED: ' + str(error), file=sys.stderr)
        return 2
    for finding in findings[:20]:
        print(
            f'{finding.rule}: {finding.path}:{finding.line}: {finding.message}',
            file=sys.stderr,
        )
    if len(findings) > 20:
        print(f'{len(findings) - 20} additional findings omitted', file=sys.stderr)
    return int(bool(findings))


if __name__ == '__main__':
    sys.exit(main())
