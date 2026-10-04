import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    environment = dict(
        os.environ,
        MLX_ENABLE_TF32='0',
        MLX_QUALIFICATION_OUTPUT=str(output),
        MPLCONFIGDIR=str(output / 'matplotlib'),
    )
    command = [
        sys.executable,
        '-m',
        'pytest',
        '-q',
        'tests/test_reference_contract.py',
        'tests/test_mlx_core.py',
        '--disable-warnings',
        f'--junitxml={output / "tests.xml"}',
    ]
    with (output / 'qualification.log').open('x') as log:
        result = subprocess.run(
            command,
            cwd=root,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    report = {
        'command': command,
        'exit_code': result.returncode,
        'MLX_ENABLE_TF32': '0',
    }
    xml = output / 'tests.xml'
    if xml.exists():
        suites = list(ET.parse(xml).getroot().iter('testsuite'))
        report.update(
            {
                key: sum(int(suite.get(key, '0')) for suite in suites)
                for key in ('tests', 'failures', 'errors', 'skipped')
            }
        )
    report['accepted'] = result.returncode == 0 and report.get('skipped') == 0
    with (output / 'result.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')
    print((output / 'qualification.log').read_text())
    print(json.dumps(report, indent=2))
    if not report['accepted']:
        raise SystemExit(result.returncode or 1)


if __name__ == '__main__':
    main()
