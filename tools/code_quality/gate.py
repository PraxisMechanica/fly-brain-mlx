import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from .diagnostics import measure


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


def require_indexed_inputs() -> None:
    indexed = set(git('ls-files', '--cached', '-z').split('\0'))
    inputs = {
        str(path)
        for root in ('src', 'tests', 'tools', 'typings')
        for pattern in ('*.py', '*.pyi')
        for path in Path(root).rglob(pattern)
    }
    inputs.update(
        (
            'main.py',
            'pyproject.toml',
            'uv.lock',
            'package.json',
            'pnpm-lock.yaml',
            'justfile',
            '.pre-commit-config.yaml',
            'tools/architecture/ownership.json',
            'tools/code-quality/provenance.json',
            'tools/code-quality/vendor/eng-metrics-code-quality-0.1.0.tgz',
            'tools/code-quality/vendor/eng-metrics-code-quality-0.1.1.tgz',
            'tools/code-quality/python-aggregation.patch',
            'tools/code_quality/metrics.mjs',
        )
    )
    if missing := sorted(inputs - indexed):
        raise ValueError('COV001: unindexed check inputs: ' + ', '.join(missing))


def main() -> int:
    if os.environ.get('PRE_COMMIT') == '1':
        require_indexed_inputs()
    requested = references(os.environ)
    base, head = requested or (git('merge-base', 'origin/main', 'HEAD'), 'HEAD')
    resolved = git('rev-parse', base), git('rev-parse', head)
    if requested and resolved[0] == resolved[1]:
        raise ValueError('COV002: requested commit range is empty')
    if result := measure(['--staged'], 'staged'):
        return result
    if resolved[0] != resolved[1]:
        return measure(['--base', base, '--head', head], 'commits')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'ANALYSIS FAILED: {error}', file=sys.stderr)
        sys.exit(2)
