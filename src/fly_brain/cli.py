import argparse
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
        case = parity_options.to_case()
        return bootstrap.parity_case()(
            parity_options.project, parity_options.output, case
        )
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
        return bootstrap.simulation()(request)
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
        request = options.to_request()
        output = Path(arguments.output).resolve()
        return bootstrap.comparison()(request, output)
    options = QualificationOptions(project=arguments.project, output=arguments.output)
    request = options.to_request()
    if arguments.command == 'qualify':
        return bootstrap.qualification()(request)
    if arguments.command == 'probe-accumulation':
        command = bootstrap.accumulation()
    elif arguments.command == 'probe-factored':
        command = bootstrap.factored()
    elif arguments.command == 'probe-bucketed':
        command = bootstrap.bucketed_scalars()
    elif arguments.command == 'probe-replay':
        command = bootstrap.replay()
    elif arguments.command == 'audit-inputs':
        command = bootstrap.input_audit()
    elif arguments.command == 'qualify-fan-in':
        command = bootstrap.fan_in_audit()
    elif arguments.command == 'qualify-layout-fan-in':
        command = bootstrap.layout_fan_in_audit()
    elif arguments.command == 'qualify-device-layout':
        command = bootstrap.device_layout_audit()
    elif arguments.command == 'qualify-connectome-pulse':
        command = bootstrap.connectome_pulse()
    else:
        command = bootstrap.schedule()
    return command(request)
