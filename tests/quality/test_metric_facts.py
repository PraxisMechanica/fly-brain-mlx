"""Actual persistent numeric-fact reuse for selected commit and CI execution."""

import json
from pathlib import Path

from tests.quality.support import PROJECT, git, repository, run

METRICS = PROJECT / 'tools/code_quality/metrics.mjs'
ENTRY = PROJECT / 'node_modules/@eng-metrics/code-quality/src/index.mjs'
MONITOR = """
import childProcess from 'node:child_process';
import {syncBuiltinESMExports} from 'node:module';
import {writeFileSync} from 'node:fs';
const spawn = childProcess.spawn;
const counts = {blobs: 0, python: 0};
childProcess.spawn = function(command, arguments_, ...options) {
  const child = spawn.call(this, command, arguments_, ...options);
  if (command === 'python') counts.python++;
  if (command === 'git' && arguments_.includes('--batch')) {
    const write = child.stdin.write.bind(child.stdin);
    child.stdin.write = (...args) => { counts.blobs++; return write(...args); };
  }
  return child;
};
syncBuiltinESMExports();
process.on('exit', () => writeFileSync(process.env.METRIC_FACT_COUNTS, JSON.stringify(counts)));
"""


def metric_repository(root: Path) -> Path:
    repository(root)
    (root / 'plain.js').write_text('export const value = 1;\n')
    (root / 'typed.ts').write_text('export const value: number = 1;\n')
    (root / 'value.go').write_text('package value\nfunc Value() int { return 1 }\n')
    (root / 'Value.cs').write_text('class Value { int Read() { return 1; } }\n')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Add native language calculations')
    return root


def measure(
    root: Path,
    program: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> tuple[dict[str, object], dict[str, int]]:
    monitor = root / '.monitor.mjs'
    monitor.write_text(MONITOR)
    counts = root / '.counts.json'
    process = run(
        ['node', '--import', str(monitor), str(program), *arguments],
        root,
        {'METRIC_FACT_COUNTS': str(counts)} | (environment or {}),
    )
    assert process.returncode in (0, 1), process.stdout + process.stderr
    return json.loads(process.stdout), json.loads(counts.read_text())


def test_warm_invocation_skips_blob_reads_and_calculators_then_reads_one_change(
    tmp_path: Path,
) -> None:
    root = metric_repository(tmp_path)
    cold, cold_counts = measure(root, METRICS, '--staged')
    warm, warm_counts = measure(root, METRICS, '--staged')
    assert (cold, cold_counts, warm_counts) == (
        warm,
        {'blobs': 5, 'python': 1},
        {'blobs': 0, 'python': 0},
    )
    facts = json.loads((root / 'logs/quality/metric-facts.json').read_text())
    assert len(facts[2]) == 5
    (root / 'calculation.py').write_text(
        'def calculate(value):\n    return value + 2\n'
    )
    git(root, 'add', 'calculation.py')
    changed, changed_counts = measure(root, METRICS, '--staged')
    assert (changed['after'], changed_counts) == (
        cold['after'],
        {'blobs': 1, 'python': 1},
    )


def test_configuration_invalidates_facts_and_malformed_protocol_fails(
    tmp_path: Path,
) -> None:
    root = metric_repository(tmp_path)
    measure(root, METRICS, '--staged', environment={'CSHARP_DEFINE_SYMBOLS': ''})
    _, counts = measure(
        root,
        METRICS,
        '--staged',
        environment={'CSHARP_DEFINE_SYMBOLS': 'METRIC_FACT_QUALIFICATION'},
    )
    assert counts == {'blobs': 5, 'python': 1}
    (root / 'logs/quality/metric-facts.json').write_text('[1, "invalid", []]')
    result = run(['node', str(METRICS), '--staged'], root)
    assert (result.returncode, json.loads(result.stdout)['error']['message']) == (
        2,
        'Invalid metric-facts protocol',
    )


def test_reused_facts_preserve_rename_delete_and_each_merge_parent_comparison(
    tmp_path: Path,
) -> None:
    root = repository(tmp_path)
    (root / 'plain.js').write_text('export const value = 1;\n')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Add removable source')
    base = git(root, 'rev-parse', 'HEAD')
    git(root, 'checkout', '-qb', 'side')
    (root / 'calculation.py').write_text(
        'def calculate(value):\n    if value > 0:\n        return value\n    return -value\n'
    )
    git(root, 'commit', '-qam', 'Change calculation')
    git(root, 'checkout', '-q', 'main')
    git(root, 'mv', 'calculation.py', 'renamed.py')
    git(root, 'commit', '-qm', 'Rename source')
    git(root, 'rm', '-q', 'plain.js')
    git(root, 'commit', '-qm', 'Delete source')
    git(root, 'merge', '-q', '--no-ff', 'side', '-m', 'Merge calculation')
    script = root / '.commits.mjs'
    script.write_text("""
import {pathToFileURL} from 'node:url';
const [entry, base] = process.argv.slice(2);
const {checkCommits, loadMetricFacts, saveMetricFacts} = await import(pathToFileURL(entry));
const identity = 'a'.repeat(64);
const cache = await loadMetricFacts('.facts.json', identity);
const result = await checkCommits({base, cache});
await saveMetricFacts('.facts.json', identity, cache);
const comparisons = result.commits.flatMap(commit => commit.comparisons);
console.log(JSON.stringify({result, coverage: {
  commits: result.commits.length, comparisons: comparisons.length,
  merge_parents: result.commits.at(-1).comparisons.length,
  totals: [...new Set(comparisons.map(item => item.after.summary.total_files))].sort(),
  findings: comparisons.some(item => item.findings.length),
}}));
""")
    cold, counts = measure(root, script, str(ENTRY), base)
    warm, reused = measure(root, script, str(ENTRY), base)
    assert cold == warm
    assert (counts, reused) == ({'blobs': 3, 'python': 2}, {'blobs': 0, 'python': 0})
    assert cold['coverage'] == {
        'commits': 4,
        'comparisons': 5,
        'merge_parents': 2,
        'totals': [1, 2],
        'findings': True,
    }
