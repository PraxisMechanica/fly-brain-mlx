import hashlib
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.quality.native_type_support import PACKAGE
from tests.quality.support import PROJECT
from tests.quality.test_native_python_context import SCOPES, edited_bridge
from tests.quality.test_native_python_context import context_root as context_root
from tools.architecture.inventory import discover
from tools.architecture.native_sources import source_inputs


def session_probe(
    root: Path,
    consumer: str,
    *,
    after: str = '',
    bridge: Path = PROJECT / 'tools/architecture/native_python_session.mjs',
    omitted: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    artifacts = source_inputs(
        bridge.parent,
        tuple(
            sorted(
                path.name
                for pattern in ('native_*.mjs', 'native_*.d.ts')
                for path in bridge.parent.glob(pattern)
            )
        ),
    )
    parent = root / 'logs'
    parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=parent, prefix='session-') as temporary:
        probe = Path(temporary) / 'consumer.mjs'
        probe.write_text(
            'import {readFileSync} from "node:fs";\n'
            f'import {{withSession}} from {json.dumps(bridge.as_uri())};\n'
            'const text = readFileSync(0,"utf8"), request = JSON.parse(text);\n'
            'let borrowed;\ntry {\n'
            'const result = await withSession(request,text,async(session)=>{\n'
            'borrowed=session;\n' + consumer + '\n});\n' + after + '\n'
            'process.stdout.write(JSON.stringify(result)+"\\n");\n'
            '} catch(error) {\n'
            'process.stdout.write(JSON.stringify({error:String(error)})+"\\n");\n'
            'process.exitCode=2;\n}\n'
        )
        configuration = root / 'pyproject.toml'
        request = {
            'schema': 1,
            'root': str(root),
            'package': str(PACKAGE.resolve()),
            'temporary': temporary,
            'sources': [
                {'path': str(root / source.path), 'sha256': source.sha256}
                for source in discover(root, SCOPES)
                if source.path not in omitted
            ],
            'configuration': [
                {
                    'path': str(configuration),
                    'sha256': hashlib.sha256(configuration.read_bytes()).hexdigest(),
                }
            ],
            'bridge_sources': [
                {'path': item.path, 'sha256': item.sha256} for item in artifacts
            ],
        }
        return subprocess.run(
            ['node', str(probe)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=90,
        )


def test_live_native_reads_share_the_canonical_program_without_tracking_mutation(
    context_root: Path,
) -> None:
    result = session_probe(
        context_root,
        'const path=request.root+"/src/context_pkg/model.py";\n'
        'const bound=session.bind(path),tree=session.parsed(path).parserOutput.parseTree;\n'
        'return [bound===session.bind(path),tree===session.parsed(path).parserOutput.parseTree,tree.nodeType,\n'
        'session.diagnostics(path),typeof session.node_info,"setTrackedFiles" in session,Object.isFrozen(session)];',
    )
    value = json.loads(result.stdout)
    assert (result.returncode, value['value'], value['report']['host_kind']) == (
        0,
        [True, True, 36, [], 'object', False, True],
        0,
    ), result.stdout + result.stderr


@pytest.mark.parametrize(
    'consumer,after,mutation,message',
    (
        (
            'return session.parsed(request.root+"/outside.py");',
            '',
            '',
            'session read is outside discovery',
        ),
        (
            'return session.parsed(request.package+"/dist/typeshed-fallback/stdlib/builtins.pyi");',
            '',
            '',
            'session read is outside discovery',
        ),
        (
            'session.parsed(request.root+"/src/context_pkg/model.py"); return 1;',
            'borrowed.parsed(request.root+"/src/context_pkg/model.py");',
            '',
            'session is closed',
        ),
        (
            'const path=request.root+"/typings/late.pyi"; session.parsed(path);\nconst {writeFileSync}=await import("node:fs"); writeFileSync(path,"value: str\\n"); return 1;',
            '',
            '',
            'COV002: context input changed after observation',
        ),
    ),
)
def test_session_rejects_missing_or_invalid_selected_reads(
    context_root: Path, consumer: str, after: str, mutation: str, message: str
) -> None:
    (context_root / 'outside.py').write_text('value = 1\n')
    (context_root / 'typings/late.pyi').write_text('value: int\n')
    bridge = edited_bridge(
        context_root,
        'const session = Object.freeze({',
        mutation + ' const session = Object.freeze({',
    ).with_name('native_python_session.mjs')
    result = session_probe(context_root, consumer, after=after, bridge=bridge)
    assert (
        result.returncode,
        'COV002:' in result.stdout,
        message in result.stdout,
    ) == (
        2,
        True,
        True,
    ), result.stdout


@pytest.mark.parametrize('omitted', ('src/context_pkg/model.py', 'typings/late.pyi'))
def test_native_enumeration_rejects_omission_before_the_consumer_runs(
    context_root: Path, omitted: str
) -> None:
    (context_root / 'typings/late.pyi').write_text('value: int\n')
    result = session_probe(
        context_root,
        'process.stderr.write("consumer-ran"); return 1;',
        omitted=(omitted,),
    )
    assert (
        result.returncode,
        'native enumeration differs from independent discovery' in result.stdout,
        result.stderr,
    ) == (2, True, '')


@pytest.mark.parametrize(
    'consumer,exit_code',
    (('return "finished";', 0), ('throw new Error("consumer failed");', 2)),
)
def test_real_native_resources_dispose_on_consumer_success_and_failure(
    context_root: Path, consumer: str, exit_code: int
) -> None:
    before = "invoke(service, 'dispose', []); services.dispose(); invoke(temporary, 'dispose', []);"
    bridge = edited_bridge(
        context_root,
        before,
        before
        + ' process.stderr.write(JSON.stringify([service._disposed,service.test_program._disposed,services._disposed,temporary._tmpdir===undefined])+"\\n");',
    ).with_name('native_python_session.mjs')
    result = session_probe(context_root, consumer, bridge=bridge)
    assert (result.returncode, json.loads(result.stderr)) == (
        exit_code,
        [True, True, True, True],
    ), result.stdout


@pytest.mark.parametrize(
    'consumer,after,mutation,module,guard,replacement,exit_code,admitted,value',
    (
        (
            'session.parsed(request.root+"/outside.py"); process.stderr.write("outside-read"); return 1;',
            '',
            '',
            'native_python_session.mjs',
            'if (!required.has(resolved))',
            'if (false)',
            2,
            'outside-read',
            None,
        ),
        (
            'session.parsed(request.root+"/src/context_pkg/model.py"); return 1;',
            'borrowed.parsed(request.root+"/src/context_pkg/model.py");',
            '',
            'native_python_session.mjs',
            'if (!active)',
            'if (false)',
            0,
            '',
            1,
        ),
    ),
)
def test_disabling_each_read_guard_admits_the_same_unsupported_read(
    context_root: Path,
    consumer: str,
    after: str,
    mutation: str,
    module: str,
    guard: str,
    replacement: str,
    exit_code: int,
    admitted: str,
    value: bool | int | None,
) -> None:
    (context_root / 'outside.py').write_text('value = 1\n')
    (context_root / 'typings/late.pyi').write_text('value: int\n')
    bridge = edited_bridge(context_root, guard, replacement, module).with_name(
        'native_python_session.mjs'
    )
    text = bridge.read_text()
    bridge.write_text(
        text.replace(
            'const session = Object.freeze({',
            mutation + ' const session = Object.freeze({',
        )
    )
    result = session_probe(context_root, consumer, after=after, bridge=bridge)
    assert (
        result.returncode,
        result.stderr,
        json.loads(result.stdout).get('value'),
    ) == (
        exit_code,
        admitted,
        value,
    ), result.stdout


@pytest.mark.parametrize('guard', ('normal', 'weakened'))
def test_same_program_final_origin_guard_rejects_native_mutation_and_weakening(
    context_root: Path, guard: str
) -> None:
    (context_root / 'outside.py').write_text('value = 1\n')
    bridge = edited_bridge(
        context_root,
        'const value = await consume?.(session);',
        'const value = await consume?.(session); '
        'program.setTrackedFiles([...initial.tracked,root+"/outside.py"].map((path)=>Uri.file(path,services))); '
        'program.getBoundSourceFile(Uri.file(root+"/outside.py",services));',
    ).with_name('native_python_session.mjs')
    projection = bridge.parent / 'native_python_observation.mjs'
    predicate = "if (!required.has(path) && (!typeshed && !third_party || packages.some((name) => module === name || module.startsWith(name + '.'))))"
    replacements = {'normal': predicate, 'weakened': 'if (false)'}
    text = projection.read_text()
    projection.write_text(text.replace(predicate, replacements[guard]))
    result = session_probe(context_root, 'return 1;', bridge=bridge)
    assert (
        result.returncode,
        'foreign or unregistered first-party resolution' in result.stdout,
    ) == {'normal': (2, True), 'weakened': (0, False)}[guard], result.stdout
