import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from .changes import Plan, build_plan
from .native_impact import commands
from .run import check
from .test_selection import commands as test_commands
from .test_selection import execution_arguments

Stage = Literal['commit', 'push', 'ci', 'manual']
COMMAND = ('uv', 'run', '--locked', '--no-sync')


class Arguments(argparse.Namespace):
    stage: Stage
    only: str | None


def tasks(plan: Plan, stage: Stage) -> tuple[tuple[str, tuple[str, ...]], ...]:
    result: list[tuple[str, tuple[str, ...]]] = [
        ('inputs', ('python', '-m', 'tools.code_quality.gate', '--inputs-only')),
    ]
    if plan.format_files:
        result.extend(
            (
                ('format', ('ruff', 'format', '--check', *plan.format_files)),
                ('lint', ('ruff', 'check', *plan.format_files)),
            )
        )
    if plan.python:
        result.append(('types', ('pyright', *plan.python)))
    result.extend(commands(plan.changed, plan.native))
    if plan.boundaries:
        result.append(
            (
                'boundaries',
                (
                    'python',
                    '-m',
                    'tools.code_quality.boundaries',
                    *(('--tree', plan.tree) if plan.tree else ()),
                    *(plan.boundary_files or plan.python),
                ),
            )
        )
    if plan.changed and (
        plan.python or 'tools/architecture/ownership.json' in plan.changed
    ):
        result.append(
            (
                'ownership',
                (
                    'python',
                    '-m',
                    'tools.code_quality.ownership',
                    '--base',
                    plan.base or 'HEAD',
                    *plan.changed,
                ),
            )
        )
    if plan.metrics:
        result.append(
            ('metrics', ('python', '-m', 'tools.code_quality.gate', '--stage', stage))
        )
    result.extend(test_commands(plan.tests, stage))
    return tuple(result)


def verify_checkout(stage: Stage, head: str | None) -> None:
    if stage == 'manual':
        return
    revision = () if stage == 'commit' else (head or 'HEAD',)
    result = subprocess.run(
        [
            'git',
            'diff',
            '--quiet',
            *revision,
            '--',
            'src',
            'tests',
            'tools',
            'typings',
            'main.py',
            'pyproject.toml',
            'uv.lock',
            'package.json',
            'pnpm-lock.yaml',
            'justfile',
            '.pre-commit-config.yaml',
        ],
        check=False,
    )
    if result.returncode:
        raise ValueError(
            'COV002: execution inputs differ from the selected index or submitted commit'
        )


def execute(plan: Plan, stage: Stage, only: str | None = None) -> int:
    selected = tuple(
        item for item in tasks(plan, stage) if only is None or item[0] == only
    )
    print(
        f'Incremental {stage}: {len(plan.changed)} changed inputs; '
        f'{len(plan.python)} affected Python files.'
        f' {len(plan.tests)} selected test targets.'
    )
    for name, arguments in selected:
        if result := check(
            name, (*COMMAND, *execution_arguments(name, arguments, stage))
        ):
            return result
    if not selected:
        print('No changed inputs require this check.')
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'stage', choices=('commit', 'push', 'ci', 'manual'), default='commit', nargs='?'
    )
    parser.add_argument(
        '--only',
        choices=(
            'inputs',
            'format',
            'lint',
            'types',
            'boundaries',
            'ownership',
            'metrics',
            'tests',
        ),
    )
    options = parser.parse_args(arguments, namespace=Arguments())
    root = Path.cwd().resolve()
    os.environ['PYTHONPATH'] = str(root / 'src') + os.pathsep + str(root)
    try:
        head = os.environ.get('QUALITY_HEAD') or os.environ.get('PRE_COMMIT_TO_REF')
        verify_checkout(options.stage, head)
        plan = build_plan(root, options.stage, os.environ)
        return execute(plan, options.stage, options.only)
    except (OSError, ValueError) as error:
        print('ANALYSIS FAILED: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
