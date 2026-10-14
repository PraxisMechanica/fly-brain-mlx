import subprocess
from pathlib import Path


def require_indexed_inputs() -> None:
    indexed = set(
        subprocess.check_output(['git', 'ls-files', '--cached', '-z'], text=True)
        .strip()
        .split('\0')
    )
    inputs = {
        str(path)
        for root in ('src', 'tests', 'tools', 'typings')
        for pattern in ('*.py', '*.pyi', '*.mjs', '*.js', '*.ts', '*.tsx', '*.jsx')
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
            'tools/code-quality/vendor/eng-metrics-code-quality-0.1.2.tgz',
            'tools/code-quality/metric-facts.patch',
            'tools/code-quality/python-aggregation.patch',
            'tools/code_quality/metrics.mjs',
            'tools/code_quality/retention.json',
        )
    )
    if missing := sorted(inputs - indexed):
        raise ValueError('COV001: unindexed check inputs: ' + ', '.join(missing))
