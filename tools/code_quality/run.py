import argparse
import subprocess
import sys
from collections.abc import Sequence

from .diagnostics import bounded, destination


def check(name: str, command: Sequence[str]) -> int:
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        output = process.stdout + process.stderr
        result = process.returncode
    except OSError as error:
        output, result = str(error), 2
    if result:
        report = destination(name, 'log')
        report.write_text(bounded(output, 65536))
        print(f'{name}: FAIL ({result}); diagnostics: {report}', file=sys.stderr)
        print(bounded(output, 4096), file=sys.stderr)
    else:
        print(f'{name}: PASS')
        print(bounded('\n'.join(output.splitlines()[-3:]), 1024))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name', choices=('format', 'lint', 'types', 'boundaries', 'tests', 'metrics')
    )
    parser.add_argument('command', nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    if not arguments.command:
        parser.error('A check command is required')
    return check(arguments.name, arguments.command)


if __name__ == '__main__':
    sys.exit(main())
