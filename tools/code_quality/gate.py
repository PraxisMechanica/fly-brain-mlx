import argparse
import os
import subprocess
import sys
from collections.abc import Mapping

from .diagnostics import measure
from .indexed_inputs import require_indexed_inputs as require_indexed_inputs


def references(environment: Mapping[str, str]) -> tuple[str, str] | None:
    for names in (
        ('QUALITY_BASE', 'QUALITY_HEAD'),
        ('PRE_COMMIT_FROM_REF', 'PRE_COMMIT_TO_REF'),
    ):
        base, head = (environment.get(name, '') for name in names)
        if base or head:
            if not base or not head or set(base) == {'0'} or set(head) == {'0'}:
                raise ValueError(f'Incomplete commit range: {names}')
            return base, head
    return None


def git(*arguments: str) -> str:
    return subprocess.check_output(['git', *arguments], text=True).strip()


def main(stage: str | None = None, inputs_only: bool = False) -> int:
    if inputs_only:
        require_indexed_inputs()
        return 0
    if os.environ.get('PRE_COMMIT') == '1':
        require_indexed_inputs()
    if stage == 'commit':
        return measure(['--staged'], 'staged')
    requested = references(os.environ)
    base, head = requested or (git('merge-base', 'origin/main', 'HEAD'), 'HEAD')
    resolved = git('rev-parse', base), git('rev-parse', head)
    if requested and resolved[0] == resolved[1]:
        raise ValueError('COV002: requested commit range is empty')
    if stage not in ('push', 'ci'):
        if result := measure(['--staged'], 'staged'):
            return result
    if resolved[0] != resolved[1]:
        return measure(['--base', base, '--head', head], 'commits')
    return 0


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--stage', choices=('commit', 'push', 'ci', 'manual'))
        parser.add_argument('--inputs-only', action='store_true')
        arguments = parser.parse_args()
        sys.exit(main(arguments.stage, arguments.inputs_only))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'ANALYSIS FAILED: {error}', file=sys.stderr)
        sys.exit(2)
