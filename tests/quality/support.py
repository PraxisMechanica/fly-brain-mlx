import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
ENGINE = PROJECT / 'node_modules/@eng-metrics/code-quality/src/cli.mjs'
SIMPLE = 'def calculate(value):\n    return value + 1\n'
COMPLEX = 'def calculate(value):\n    if value > 0:\n        return value\n    return -value\n'


def run(
    arguments: Sequence[str],
    root: Path,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    isolated = {
        key: value for key, value in os.environ.items() if not key.startswith('GIT_')
    }
    isolated.update(environment or {})
    return subprocess.run(
        arguments,
        cwd=root,
        env=isolated,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def git(root: Path, *arguments: str) -> str:
    result = run(['git', *arguments], root)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def repository(root: Path) -> Path:
    git(root, 'init', '-q', '--initial-branch=main', '--template=')
    git(root, 'config', 'user.name', 'Source fixture')
    git(root, 'config', 'user.email', 'source-fixture@example.invalid')
    (root / 'calculation.py').write_text(SIMPLE)
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Create source fixture baseline')
    return root


def measure(
    root: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        ['node', str(ENGINE), 'check', '--repo', str(root), *arguments],
        root,
        environment,
    )
