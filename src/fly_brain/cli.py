import argparse
import json
import time
from collections.abc import Sequence
from pathlib import Path

from . import bootstrap
from .comparison.schemas import ComparisonOptions
from .qualification.schemas import ParityOptions, QualificationOptions
from .simulation.schemas import SimulationOptions


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description='MLX fly-brain simulation and qualification'
    )
    commands = result.add_subparsers(dest='command', required=True)
    for name in (
        'qualify',
        'probe-accumulation',
        'probe-factored',
        'probe-bucketed',
        'probe-replay',
        'inspect-reference',
        'audit-inputs',
        'qualify-fan-in',
        'qualify-layout-fan-in',
        'qualify-device-layout',
        'qualify-connectome-pulse',
    ):
        command = commands.add_parser(name)
        command.add_argument('--output', type=Path, required=True)
        command.add_argument('--project', type=Path, default=Path.cwd())
    command = commands.add_parser('qualify-parity')
    command.add_argument('--project', type=Path, default=Path.cwd())
    command.add_argument('--output', type=Path, required=True)
    command.add_argument(
        '--experiment',
        choices=('sugar', 'p9', 'sugar-silenced', 'two-class', 'silent'),
        default='sugar',
    )
    command.add_argument(
        '--duration-s', type=float, choices=(0.1, 1.0, 10.0), default=0.1
    )
    command.add_argument('--trial', type=int, choices=range(5), default=0)
    command = commands.add_parser('compare')
    command.add_argument('--first', type=Path, required=True)
    command.add_argument('--second', type=Path, required=True)
    command.add_argument('--duration-s', type=float, required=True)
    command.add_argument('--trials', type=int, required=True)
    command.add_argument('--tolerance-ms', type=float, default=0.1)
    command.add_argument('--first-label', default='mlx')
    command.add_argument('--second-label', default='brian2cpp')
    command.add_argument('--output', type=Path, required=True)
    command = commands.add_parser('simulate')
    command.add_argument('--project', type=Path, default=Path.cwd())
    command.add_argument('--output', type=Path)
    command.add_argument(
        '--experiment',
        choices=('sugar', 'p9', 'sugar-silenced', 'two-class', 'silent'),
        default='sugar',
    )
    command.add_argument('--duration-s', type=float, default=0.1)
    command.add_argument('--trials', type=int, default=1)
    command.add_argument('--seed', type=int, default=20261004)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == 'qualify-parity':
        parity_options = ParityOptions(
            project=arguments.project,
            output=arguments.output,
            experiment=arguments.experiment,
            duration_s=arguments.duration_s,
            trial=arguments.trial,
        )
        parity_report = bootstrap.parity_case(
            parity_options.project, parity_options.output, parity_options.to_case()
        )
        print(
            json.dumps(
                {
                    'case': parity_report['case'],
                    'case_accepted': parity_report['case_accepted'],
                    'scientific_review_required': parity_report[
                        'scientific_review_required'
                    ],
                    'report': str(parity_options.output / 'case.json'),
                },
                indent=2,
            )
        )
        return 0 if parity_report['case_accepted'] else 1
    if arguments.command == 'simulate':
        output = (
            arguments.output
            or arguments.project / 'data/results' / f'mlx-{time.time_ns()}'
        )
        request = SimulationOptions(
            project=arguments.project,
            output=output,
            experiment=arguments.experiment,
            duration_s=arguments.duration_s,
            trials=arguments.trials,
            seed=arguments.seed,
        ).to_request()
        result = bootstrap.simulation(request)
        print(
            json.dumps(
                {
                    'spike_file': str(result.spike_file),
                    'spikes': result.spikes,
                    'active_neurons': result.active_neurons,
                    'elapsed_s': result.elapsed_s,
                },
                indent=2,
            )
        )
        return 0
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
    elif arguments.command == 'probe-bucketed':
        report = bootstrap.bucketed_scalars(request.project, request.output)
    elif arguments.command == 'probe-replay':
        report = bootstrap.replay(request.output)
    elif arguments.command == 'audit-inputs':
        report = bootstrap.input_audit(request.project, request.output)
    elif arguments.command == 'qualify-fan-in':
        report = bootstrap.fan_in_audit(request.project, request.output)
    elif arguments.command == 'qualify-layout-fan-in':
        report = bootstrap.layout_fan_in_audit(request.project, request.output)
    elif arguments.command == 'qualify-device-layout':
        report = bootstrap.device_layout_audit(request.project, request.output)
    elif arguments.command == 'qualify-connectome-pulse':
        report = bootstrap.connectome_pulse(request.project, request.output)
    else:
        report = bootstrap.schedule(request.output)
    print(json.dumps(report, indent=2))
    return 0 if report.get('accepted', True) else 1
