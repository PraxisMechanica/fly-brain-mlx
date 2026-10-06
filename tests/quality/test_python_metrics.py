import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from tests.quality.python_metric_fixture import (
    ARCHIVE,
    BASE_ARCHIVE,
    PATCH,
    PROVENANCE,
    analyze,
    archive_sources,
    changed_package,
    masked_source,
    metric_repository,
    package,
    probe,
    protocol_tool,
    unavailable_radon,
)
from tests.quality.support import ENGINE, git, measure, repository, run
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.integration
CASES = (
    ('', 1),
    ('# if and for\n', 1),
    ('text = "if and for"\n', 1),
    ('if flag:\n    pass\n', 2),
    (
        'def a(x):\n    if x:\n        return 1\ndef b(x):\n    if x:\n        return 1\n',
        3,
    ),
    ('class A:\n    def a(self):\n        pass\n    def b(self):\n        pass\n', 1),
    (
        'class A:\n    def a(self,x):\n        if x:\n            return 1\n    def b(self,x):\n        if x:\n            return 1\n',
        3,
    ),
    ('def a():\n    def b(x):\n        if x:\n            return 1\n    return b\n', 2),
    (
        'class A:\n    class B:\n        def a(self,x):\n            if x:\n                return 1\n',
        2,
    ),
    ('value = lambda x: 1 if x else 0\n', 2),
    ('def a(x=1 if flag else 0):\n    return x\n', 2),
    ('@(first if flag else second)\ndef a():\n    pass\n', 2),
    ('class A(First if flag else Second):\n    pass\n', 2),
    ('async def a(x):\n    if x:\n        return 1\n', 2),
    ('def a(x):\n    assert x\n', 2),
    ('def a(x,y):\n    assert x and y\n', 2),
    ('value = [x for x in rows if x if flag]\n', 4),
    ('value = (x for x in rows if x)\n', 3),
    ('value = {x for x in rows if x}\n', 3),
    ('value = {x:x for x in rows if x}\n', 3),
    ('for x in rows:\n    pass\nelse:\n    pass\n', 3),
    ('while flag:\n    pass\nelse:\n    pass\n', 3),
    (
        'try:\n    pass\nexcept ValueError:\n    pass\nexcept TypeError:\n    pass\nelse:\n    pass\n',
        4,
    ),
    ('match value:\n    case 1:\n        pass\n    case _:\n        pass\n', 2),
    ('match value:\n    case 1:\n        pass\n    case 2:\n        pass\n', 3),
    ('match value:\n    case _:\n        pass\n', 1),
    ('value = first and second and third\n', 3),
    ('\ufeffif flag:\n    pass\n', 2),
)


@pytest.mark.parametrize('source,expected', CASES)
def test_whole_file_native_decisions_preserve_every_other_public_measurement(
    tmp_path: Path, source: str, expected: int
) -> None:
    original = package(tmp_path, 'original-engine', BASE_ARCHIVE)
    before = analyze(tmp_path, source, original / 'src/analyzers.mjs')
    after = analyze(tmp_path, source, ENGINE.with_name('analyzers.mjs'))
    assert after == {**before, 'cyclomatic_complexity': expected}


def test_masked_function_regression_repair_close_and_staging(tmp_path: Path) -> None:
    baseline = masked_source()
    repo = metric_repository(tmp_path, baseline)
    source = repo / 'calculation.py'
    source.write_text(masked_source(True))
    git(repo, 'add', 'calculation.py')
    source.write_text(baseline)
    result = measure(repo, '--staged', '--json', str(repo / 'regression.json'))
    evidence = object_value(
        cast(JsonValue, json.loads((repo / 'regression.json').read_text()))
    )
    assert (result.returncode, source.read_text(), evidence['findings']) == (
        1,
        baseline,
        [
            {
                'rule': 'CQ002',
                'path': '<repository>',
                'metric': 'avg_cyclomatic_complexity',
                'before': 21,
                'after': 22,
            },
            {
                'rule': 'CQ002',
                'path': '<repository>',
                'metric': 'max_cyclomatic_complexity',
                'before': 21,
                'after': 22,
            },
            {
                'rule': 'CQ002',
                'path': 'calculation.py',
                'metric': 'cyclomatic_complexity',
                'before': 21,
                'after': 22,
            },
        ],
    )
    source.write_text(baseline.replace('value > 0:', 'value > -1:'))
    git(repo, 'add', 'calculation.py')
    assert measure(repo, '--staged').returncode == 0
    source.write_text(baseline)
    git(repo, 'add', 'calculation.py')
    assert measure(repo, '--staged').returncode == 0


def test_a_later_repair_cannot_hide_the_masked_function_commit(tmp_path: Path) -> None:
    repo = metric_repository(tmp_path, masked_source())
    base = git(repo, 'rev-parse', 'HEAD')
    source = repo / 'calculation.py'
    source.write_text(masked_source(True))
    git(repo, 'add', 'calculation.py')
    git(repo, 'commit', '-qm', 'Introduce masked source regression')
    source.write_text(masked_source())
    git(repo, 'add', 'calculation.py')
    git(repo, 'commit', '-qm', 'Repair masked source regression')
    result = measure(repo, '--base', base, '--head', 'HEAD')
    assert result.returncode == 1 and 'calculation.py' in result.stderr


@pytest.mark.parametrize(
    'guard,baseline',
    (
        (
            'FunctionDef',
            'def outer():\n    def inner(x):\n        return x\n    return inner\n',
        ),
        ('FunctionDef', 'async def run(x):\n    return x\n'),
        (
            'ClassDef',
            'class Outer:\n    class Inner:\n        def run(self,x):\n            return x\n',
        ),
    ),
)
def test_each_effective_scope_guard_loses_its_own_source_rejection_when_disabled(
    tmp_path: Path, guard: str, baseline: str
) -> None:
    repo = metric_repository(tmp_path, baseline)
    (repo / 'calculation.py').write_text(
        baseline.replace('return x', 'return 1 if x else 0')
    )
    git(repo, 'add', 'calculation.py')
    strong = measure(repo, '--staged')
    weak = changed_package(
        repo, f'    visit_{guard} = ComplexityVisitor.generic_visit\\n', ''
    )
    result = run(['node', str(weak), 'check', '--repo', str(repo), '--staged'], repo)
    assert (strong.returncode, 'CQ002' in strong.stderr, result.returncode) == (
        1,
        True,
        0,
    )


@pytest.mark.parametrize('source', ('def broken(:\n', 'if flag:\n'))
def test_native_syntax_errors_keep_the_analysis_failure_exit(
    tmp_path: Path, source: str
) -> None:
    repo = repository(tmp_path)
    (repo / 'calculation.py').write_text(source)
    git(repo, 'add', 'calculation.py')
    result = measure(repo, '--staged')
    assert result.returncode == 2 and 'calculation.py' in result.stderr


@pytest.mark.parametrize(
    'output',
    (
        'bad',
        '1:',
        '1:0:0',
        '0:0',
        '1:-1',
        '1.5:0',
        'NaN:0',
        'Infinity:0',
        '9007199254740992:0',
        '1:9007199254740992',
        '1:0\nnoise',
    ),
)
def test_malformed_or_unsafe_tool_protocol_cannot_become_a_valid_snapshot(
    tmp_path: Path, output: str
) -> None:
    repo = repository(tmp_path)
    result = measure(repo, '--staged', environment=protocol_tool(repo, output))
    assert result.returncode == 2 and 'Radon could not analyze' in result.stderr


def test_disabling_protocol_shape_validation_loses_its_missing_field_error(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    environment = protocol_tool(repo, '1:')
    strong = measure(repo, '--staged', environment=environment)
    weak = changed_package(repo, '!/^[1-9]\\d*:\\d+$/.test(stdout.trim()) || ', '')
    result = run(
        ['node', str(weak), 'check', '--repo', str(repo), '--staged'], repo, environment
    )
    assert (strong.returncode, result.returncode) == (2, 0)


def test_unavailable_radon_remains_a_native_tool_analysis_failure(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    result = measure(repo, '--staged', environment=unavailable_radon(repo))
    assert result.returncode == 2 and 'radon' in result.stderr


def test_wrong_radon_version_rejects_and_disabling_the_pin_loses_detection(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    native = run(['python', '-c', 'import radon; print(radon.__path__[0])'], repo)
    fake = repo / 'fake/radon'
    fake.mkdir(parents=True)
    (fake / '__init__.py').write_text(
        f'__version__ = "9.9.9"\n__path__.append({native.stdout.strip()!r})\n'
    )
    environment = {'PYTHONPATH': str(fake.parent)}
    strong = measure(repo, '--staged', environment=environment)
    weak = changed_package(
        repo,
        "if radon.__version__ != '6.0.1':\\n    raise RuntimeError('Required Radon 6.0.1 is unavailable')\\n",
        '',
    )
    result = run(
        ['node', str(weak), 'check', '--repo', str(repo), '--staged'], repo, environment
    )
    assert (
        strong.returncode,
        'Required Radon 6.0.1' in strong.stderr,
        result.returncode,
    ) == (2, True, 0)


def test_only_python_identity_changes_and_old_cache_entries_cannot_hide_the_correction(
    tmp_path: Path,
) -> None:
    repo = metric_repository(tmp_path, 'if flag:\n    pass\n')
    original = package(repo, 'original-engine', BASE_ARCHIVE)
    result = probe(
        repo,
        "import {pathToFileURL} from 'node:url';\n"
        'const [oldPath, newPath, repo] = process.argv.slice(2);\n'
        'const old = await import(pathToFileURL(oldPath)), next = await import(pathToFileURL(newPath));\n'
        'const a = old.createAnalysisManifest(), b = next.createAnalysisManifest();\n'
        'const cache = new Map(), before = await old.analyzeSnapshot({repositoryPath:repo,cache});\n'
        'const first = cache.size, after = await next.analyzeSnapshot({repositoryPath:repo,cache});\n'
        'const second = cache.size; await next.analyzeSnapshot({repositoryPath:repo,cache});\n'
        'let mismatch = false; try {next.compareSnapshots(before,after)} catch {mismatch = true}\n'
        'console.log(JSON.stringify({before:before.files[0].cyclomatic_complexity,after:after.files[0].cyclomatic_complexity,first,second,third:cache.size,mismatch,python:a.languages.python!==b.languages.python,rest:JSON.stringify({...a,languages:{...a.languages,python:null}})===JSON.stringify({...b,languages:{...b.languages,python:null}})}));\n',
        original / 'src/index.mjs',
        ENGINE.with_name('index.mjs'),
        repo,
    )
    assert result == {
        'before': 1,
        'after': 2,
        'first': 1,
        'second': 2,
        'third': 2,
        'mismatch': True,
        'python': True,
        'rest': True,
    }


def test_exact_archive_patch_and_installed_bytes_preserve_every_other_engine_source(
    tmp_path: Path,
) -> None:
    provenance = object_value(cast(JsonValue, json.loads(PROVENANCE.read_text())))
    base = object_value(provenance['base'])
    patch = object_value(provenance['patch'])
    before, after = archive_sources(BASE_ARCHIVE), archive_sources(ARCHIVE)
    original = package(tmp_path, 'reconstructed', BASE_ARCHIVE)
    applied = run(['patch', '-p1', '-i', str(PATCH)], original)
    files = object_value(provenance['files'])
    assert (
        hashlib.sha256(BASE_ARCHIVE.read_bytes()).hexdigest(),
        base['archive_sha256'],
        hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        hashlib.sha256(PATCH.read_bytes()).hexdigest(),
        applied.returncode,
        {name: (original / name).read_bytes() for name in before},
        {name: (ENGINE.parent.parent / name).read_bytes() for name in after},
        {name: hashlib.sha256(value).hexdigest() for name, value in after.items()},
        sorted(name for name in before if before[name] != after[name]),
    ) == (
        '57e0ff1d7aa9d8ae627b5385795470b46ea29dcae8ff186f5432c58a410956a7',
        '57e0ff1d7aa9d8ae627b5385795470b46ea29dcae8ff186f5432c58a410956a7',
        provenance['archive_sha256'],
        patch['sha256'],
        0,
        after,
        after,
        {name: object_value(value)['sha256'] for name, value in files.items()},
        ['package.json', 'src/analyzers.mjs', 'src/manifest.mjs'],
    )
