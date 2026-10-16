import json
import subprocess
import sys
import tempfile
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


def destination(name: str, suffix: str, *, retained: bool = False) -> Path:
    root = Path('executions' if retained else 'logs')
    directory = root / ('quality-failures' if retained else 'quality')
    if root.is_symlink() or directory.is_symlink():
        raise ValueError('Diagnostic logs must not use a symlinked directory')
    directory.mkdir(parents=True, exist_ok=True)
    if retained:
        directory = Path(tempfile.mkdtemp(prefix=name + '-', dir=directory))
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


def project_metric_exit(payload: dict[str, object], native_exit: int) -> int:
    if native_exit != 1:
        return native_exit
    value = payload.get('findings')
    if not isinstance(value, dict):
        raise ValueError('Metric regression findings must be an object')
    findings = cast(dict[str, object], value)
    total, omitted = findings.get('total'), findings.get('omitted')
    counts, examples = findings.get('by_rule'), findings.get('examples')
    if (
        type(total) is not int
        or type(omitted) is not int
        or not isinstance(counts, dict)
        or not isinstance(examples, list)
    ):
        raise ValueError('Metric regression findings have an invalid shape')
    by_rule = cast(dict[str, object], counts)
    samples = cast(list[object], examples)
    if not by_rule or any(
        rule not in ('CQ001', 'CQ002', 'CQ003') or type(count) is not int or count <= 0
        for rule, count in by_rule.items()
    ):
        raise ValueError('Metric regression contains unknown rules or invalid counts')
    if (
        total <= 0
        or omitted < 0
        or total != sum(cast(int, count) for count in by_rule.values())
        or total != len(samples) + omitted
        or not 1 <= len(samples) <= 20
    ):
        raise ValueError('Metric regression findings do not explain the failure')
    return 0


def measure(arguments: list[str], name: str) -> int:
    disposable = destination(name, 'json')
    process = subprocess.run(
        ['node', str(Path(__file__).with_name('metrics.mjs')), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict[str, object]
    try:
        payload = metric_payload(process)
        exit_code = project_metric_exit(payload, process.returncode)
    except ValueError as error:
        payload = {
            'status': 'analysis_error',
            'passed': False,
            'error': {
                'message': str(error),
                'process_output': bounded(process.stderr or process.stdout, 2000),
            },
        }
        exit_code = 2
    payload['project_policy'] = {
        'name': 'advisory_numerical_metrics',
        'native_exit_code': process.returncode,
        'blocking': exit_code != 0,
        'advisory': process.returncode == 1 and exit_code == 0,
    }
    report = (
        destination(name, 'json', retained=True)
        if payload['status'] != 'pass'
        else disposable
    )
    report.write_text(json.dumps(payload, indent=2) + '\n')
    print(
        f'{name}: {payload["status"]}; blocking: {exit_code != 0}; diagnostics: {report}'
    )
    if payload['status'] != 'pass':
        print(json.dumps(payload, indent=2), file=sys.stderr)
    return exit_code
