import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from . import bootstrap
from .comparison.schemas import ComparisonOptions
from .qualification.schemas import QualificationOptions


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description='MLX numerical-core qualification')
    commands = result.add_subparsers(dest='command', required=True)
    for name in (
        'qualify',
        'probe-accumulation',
        'probe-factored',
        'probe-replay',
        'inspect-reference',
        'audit-inputs',
        'qualify-fan-in',
    ):
        command = commands.add_parser(name)
        command.add_argument('--output', type=Path, required=True)
        command.add_argument('--project', type=Path, default=Path.cwd())
    command = commands.add_parser('compare')
    command.add_argument('--first', type=Path, required=True)
    command.add_argument('--second', type=Path, required=True)
    command.add_argument('--duration-s', type=float, required=True)
    command.add_argument('--trials', type=int, required=True)
    command.add_argument('--tolerance-ms', type=float, default=0.1)
    command.add_argument('--first-label', default='mlx')
    command.add_argument('--second-label', default='brian2cpp')
    command.add_argument('--output', type=Path, required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == 'compare':
        options = ComparisonOptions(
            first=arguments.first,
            second=arguments.second,
            duration_s=arguments.duration_s,
            trials=arguments.trials,
            tolerance_ms=arguments.tolerance_ms,
            first_label=arguments.first_label,
            second_label=arguments.second_label,
        )
        result = bootstrap.comparison(
            options.to_request(), Path(arguments.output).resolve()
        )
        print(json.dumps(result.summary, indent=2))
        return 0
    options = QualificationOptions(project=arguments.project, output=arguments.output)
    request = options.to_request()
    if arguments.command == 'qualify':
        qualification = bootstrap.qualification(request)
        print(
            json.dumps(
                {
                    'accepted': qualification.accepted,
                    'exit_code': qualification.exit_code,
                },
                indent=2,
            )
        )
        return 0 if qualification.accepted else 1
    if arguments.command == 'probe-accumulation':
        report = bootstrap.accumulation(request.project, request.output)
    elif arguments.command == 'probe-factored':
        report = bootstrap.factored(request.project, request.output)
    elif arguments.command == 'probe-replay':
        report = bootstrap.replay(request.output)
    elif arguments.command == 'audit-inputs':
        report = bootstrap.input_audit(request.project, request.output)
    elif arguments.command == 'qualify-fan-in':
        report = bootstrap.fan_in_audit(request.project, request.output)
    else:
        report = bootstrap.schedule(request.output)
    print(json.dumps(report, indent=2))
    return 0 if report.get('accepted', True) else 1
