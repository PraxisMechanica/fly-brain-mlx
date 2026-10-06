import json
from pathlib import Path
from typing import cast

import pytest

from tests.quality.support import COMPLEX, ENGINE, SIMPLE, git, measure, repository, run
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.integration


@pytest.fixture
def staged_regression(tmp_path: Path) -> Path:
    repo = repository(tmp_path)
    (repo / 'calculation.py').write_text(COMPLEX)
    git(repo, 'add', 'calculation.py')
    result = measure(repo, '--staged', '--json', str(repo / 'regression.json'))
    assert result.returncode == 1, result.stderr
    return repo


def reversed_rule(repo: Path, rule: str, metric: str, direction: str) -> Path:
    source = ENGINE.with_name('gate.mjs').read_text()
    declaration = f"{{ id: '{rule}', metric: '{metric}', direction: '{direction}' }}"
    assert source.count(declaration) == 1
    opposite = {'higher': 'lower', 'lower': 'higher'}[direction]
    path = repo / 'weakened-gate.mjs'
    path.write_text(
        source.replace(declaration, declaration.replace(direction, opposite), 1)
    )
    return path


def compare_native_rules(repo: Path, weakened: Path) -> dict[str, JsonValue]:
    script = repo / 'probe.mjs'
    script.write_text(
        "import {readFileSync} from 'node:fs';\n"
        "import {pathToFileURL} from 'node:url';\n"
        'const [original, weakened, report] = process.argv.slice(2);\n'
        'const strong = await import(pathToFileURL(original).href);\n'
        'const weak = await import(pathToFileURL(weakened).href);\n'
        "const data = JSON.parse(readFileSync(report, 'utf8'));\n"
        'const before = data.before, after = data.after;\n'
        'console.log(JSON.stringify({\n'
        '  strong: strong.compareSnapshots(before, after).findings,\n'
        '  weak: weak.compareSnapshots(before, after).findings,\n'
        '  close: weak.compareSnapshots(before, before).passed\n'
        '}));\n'
    )
    result = run(
        [
            'node',
            str(script),
            str(ENGINE.with_name('gate.mjs')),
            str(weakened),
            str(repo / 'regression.json'),
        ],
        repo,
    )
    assert result.returncode == 0, result.stderr
    return object_value(cast(JsonValue, json.loads(result.stdout)))


def findings(value: JsonValue) -> set[tuple[str, str]]:
    assert isinstance(value, list)
    return {
        (str(object_value(item)['rule']), str(object_value(item)['path']))
        for item in value
    }


@pytest.mark.parametrize(
    'rule,metric,direction,location',
    (
        ('CQ001', 'code_health', 'higher', '<repository>'),
        ('CQ002', 'cyclomatic_complexity', 'lower', 'calculation.py'),
        ('CQ003', 'maintainability_index', 'higher', '<repository>'),
    ),
)
def test_weakening_each_native_metric_rule_loses_its_actual_source_regression(
    staged_regression: Path, rule: str, metric: str, direction: str, location: str
) -> None:
    weakened = reversed_rule(staged_regression, rule, metric, direction)
    evidence = compare_native_rules(staged_regression, weakened)
    assert (rule, location) in findings(evidence['strong'])
    assert rule not in {item[0] for item in findings(evidence['weak'])}
    assert evidence['close'] is True
    (staged_regression / 'calculation.py').write_text(SIMPLE.replace('+ 1', '+ 2'))
    git(staged_regression, 'add', 'calculation.py')
    repair = measure(staged_regression, '--staged')
    assert repair.returncode == 0, repair.stderr
