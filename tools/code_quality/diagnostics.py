import json
import subprocess
import sys
from pathlib import Path
from typing import cast


def bounded(text: str, limit: int) -> str:
    encoded = text.encode('utf-8')
    if len(encoded) <= limit:
        return text
    kept = limit - 100
    beginning = kept // 3
    head = encoded[:beginning].decode('utf-8', errors='ignore')
    tail = encoded[-(kept - beginning) :].decode('utf-8', errors='ignore')
    omitted = len(encoded) - len((head + tail).encode('utf-8'))
    return head + f'\n[{omitted} bytes omitted]\n' + tail


def destination(name: str, suffix: str) -> Path:
    directory = Path('logs') / 'quality'
    if Path('logs').is_symlink() or directory.is_symlink():
        raise ValueError('Diagnostic logs must not use a symlinked directory')
    directory.mkdir(parents=True, exist_ok=True)
    report = directory / f'{name}.{suffix}'
    if report.is_symlink():
        raise ValueError('Diagnostic report must not be a symlink')
    return report


def metric_payload(process: subprocess.CompletedProcess[str]) -> dict[str, object]:
    if len(process.stdout.encode('utf-8')) > 32768:
        raise ValueError('Metric diagnostics exceeded the 32 KiB limit')
    value: object = json.loads(process.stdout)
    if not isinstance(value, dict):
        raise ValueError('Metric diagnostics must be an object')
    payload = cast(dict[str, object], value)
    expected = {
        0: ('pass', True),
        1: ('regression', False),
        2: ('analysis_error', False),
    }.get(process.returncode)
    if (
        expected is None
        or payload.get('status') != expected[0]
        or payload.get('passed') is not expected[1]
    ):
        raise ValueError('Metric diagnostics disagree with the check exit status')
    return payload


def measure(arguments: list[str], name: str) -> int:
    report = destination(name, 'json')
    process = subprocess.run(
        ['node', str(Path(__file__).with_name('metrics.mjs')), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = metric_payload(process)
    except ValueError as error:
        payload = {
            'status': 'analysis_error',
            'passed': False,
            'error': {
                'message': str(error),
                'process_output': bounded(process.stderr or process.stdout, 2000),
            },
        }
        process.returncode = 2
    report.write_text(json.dumps(payload, indent=2) + '\n')
    print(f'{name}: {payload["status"]}; diagnostics: {report}')
    if process.returncode:
        print(json.dumps(payload, indent=2), file=sys.stderr)
    return process.returncode
