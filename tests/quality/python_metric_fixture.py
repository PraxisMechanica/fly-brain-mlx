import json
import shlex
import shutil
import sys
import tarfile
from pathlib import Path
from typing import cast

from tests.quality.support import ENGINE, PROJECT, git, repository, run
from tools.architecture.compiler import JsonValue, object_value

VENDOR = PROJECT / 'tools/code-quality/vendor'
BASE_ARCHIVE = VENDOR / 'eng-metrics-code-quality-0.1.0.tgz'
ARCHIVE = VENDOR / 'eng-metrics-code-quality-0.1.1.tgz'
PATCH = PROJECT / 'tools/code-quality/python-aggregation.patch'
PROVENANCE = PROJECT / 'tools/code-quality/provenance.json'


def archive_sources(path: Path) -> dict[str, bytes]:
    with tarfile.open(path) as archive:
        result: dict[str, bytes] = {}
        for member in archive.getmembers():
            stream = archive.extractfile(member)
            if not member.isfile() or stream is None:
                raise ValueError('Source archive contains a non-file member')
            name = member.name.removeprefix('package/')
            if member.name != 'package/' + name or '..' in Path(name).parts:
                raise ValueError('Source archive contains an invalid path')
            result[name] = stream.read()
        return result


def package(root: Path, name: str, archive: Path = ARCHIVE) -> Path:
    folder = root / name
    folder.mkdir()
    for relative, content in archive_sources(archive).items():
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (folder / 'node_modules').symlink_to(ENGINE.resolve().parents[3])
    return folder


def probe(
    root: Path, source: str, *arguments: Path, environment: dict[str, str] | None = None
) -> dict[str, JsonValue]:
    script = root / 'probe.mjs'
    script.write_text(source)
    result = run(['node', str(script), *(str(p) for p in arguments)], root, environment)
    assert result.returncode == 0, result.stderr
    return object_value(cast(JsonValue, json.loads(result.stdout)))


def analyze(root: Path, source: str, module: Path) -> dict[str, JsonValue]:
    path = root / 'input.py'
    path.write_text(source)
    return probe(
        root,
        "import {pathToFileURL} from 'node:url';\n"
        'const [module, file] = process.argv.slice(2);\n'
        'const {analyzePythonComplexity} = await import(pathToFileURL(module));\n'
        'console.log(JSON.stringify(await analyzePythonComplexity(file)));\n',
        module,
        path,
    )


def changed_package(root: Path, before: str, after: str) -> Path:
    folder = package(root, 'changed-engine')
    path = folder / 'src/analyzers.mjs'
    source = path.read_text()
    assert source.count(before) == 1
    path.write_text(source.replace(before, after, 1))
    return folder / 'src/cli.mjs'


def metric_repository(root: Path, source: str) -> Path:
    repo = repository(root)
    (repo / 'calculation.py').write_text(source)
    git(repo, 'add', 'calculation.py')
    git(repo, 'commit', '-qm', 'Declare source measurement fixture')
    return repo


def masked_source(extra: bool = False) -> str:
    condition = ' and value != -1' if extra else ''
    checks = '\n'.join(
        f'    if value > {index}{condition if index == 19 else ""}:\n'
        '        result += 1'
        for index in range(20)
    )
    siblings = '\n'.join(
        f'def simple{index}(value):\n    return value' for index in range(20)
    )
    return f'def complicated(value):\n    result = 0\n{checks}\n    return result\n{siblings}\n'


def python_tool(root: Path, body: str) -> dict[str, str]:
    folder = root / 'executables'
    folder.mkdir()
    for name in ('node', 'git'):
        executable = shutil.which(name)
        assert executable is not None
        (folder / name).symlink_to(executable)
    path = folder / 'python'
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)
    return {'PATH': str(folder)}


def protocol_tool(root: Path, output: str) -> dict[str, str]:
    return python_tool(root, "printf '%s\\n' " + shlex.quote(output) + '\n')


def unavailable_radon(root: Path) -> dict[str, str]:
    return python_tool(root, 'exec ' + shlex.quote(sys.executable) + ' -S "$@"\n')
