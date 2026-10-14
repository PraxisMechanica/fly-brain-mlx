import hashlib
import json
from pathlib import Path

import pytest

from tests.quality.test_native_python_context import edited_bridge
from tests.quality.test_native_python_session import context_root as context_root
from tests.quality.test_native_python_session import session_probe


@pytest.mark.parametrize(
    'consumer,after,mutation,message',
    (
        (
            'return session.bind(request.root+"/typings/late.pyi");',
            '',
            'program.addInterimFile=undefined;',
            'native API method is missing: addInterimFile',
        ),
        (
            'return session.bind(request.root+"/typings/late.pyi");',
            '',
            'program.addInterimFile=()=>undefined;',
            'native selected source binding is not an object',
        ),
        (
            'return session.bind(request.root+"/typings/late.pyi");',
            '',
            'program.getParseResults=()=>undefined;',
            'native selected source binding is not an object',
        ),
        (
            'return session.bind(request.root+"/typings/late.pyi");',
            '',
            'program.getParseResults=undefined;',
            'native API method is missing: getParseResults',
        ),
        (
            'return session.parsed(request.root+"/typings/late.pyi");',
            '',
            'program.getParseResults=()=>({});',
            'native selected parser output',
        ),
        (
            'return session.parsed(request.root+"/typings/late.pyi");',
            '',
            'const parse=program.getParseResults.bind(program); program.getParseResults=(source)=>{const result=parse(source); result.parserOutput.parseTree.nodeType=31; return result;};',
            'native selected source binding differs',
        ),
        (
            'return session.parsed(request.root+"/typings/late.pyi");',
            '',
            'const parse=program.getParseResults.bind(program); program.getParseResults=(source)=>{const result=parse(source); invoke(native(1920),"getScope",[result.parserOutput.parseTree,program.analyzerNodeInfoReader]).type=2; return result;};',
            'native selected source binding differs',
        ),
        (
            'return session.parsed(request.root+"/typings/late.pyi");',
            '',
            'const parse=program.getParseResults.bind(program); program.getParseResults=(source)=>{const result=parse(source); invoke(native(1920),"getScope",[result.parserOutput.parseTree,program.analyzerNodeInfoReader]).symbolTable=undefined; return result;};',
            'native selected source binding differs',
        ),
        (
            'return session.parsed(request.root+"/typings/late.pyi");',
            '',
            'const parse=program.getParseResults.bind(program); program.getParseResults=()=>parse(Uri.file(root+"/src/context_pkg/model.py",services));',
            'native selected source binding differs',
        ),
    ),
)
def test_native_enrollment_rejects_missing_or_invalid_binding(
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


@pytest.mark.parametrize(
    'consumer,after,mutation,module,guard,replacement,exit_code,admitted,value',
    (
        (
            'return session.parsed(request.root+"/typings/late.pyi")===undefined;',
            '',
            'program.getParseResults=()=>undefined;',
            'native_python_binding.mjs',
            "const parsed = object(invoke(program, 'getParseResults', [source]), `${resolved}: native selected source binding`);\n  const tree = object(object(parsed.parserOutput, `${resolved}: native selected parser output`).parseTree, `${resolved}: native selected module`);\n  const reader = program.analyzerNodeInfoReader, scope = object(invoke(native(1920), 'getScope', [tree, reader]), `${resolved}: native selected scope`);\n  const info = object(invoke(native(1920), 'getFileInfo', [tree, reader]), `${resolved}: native selected file info`);\n  if (tree.nodeType !== 36 || scope.type !== 4 || !(scope.symbolTable instanceof Map) || realpathSync(uri(invoke(fs, 'getOriginalUri', [info.fileUri]))) !== resolved) fail(`native selected source binding differs: ${resolved}`);",
            "void invoke(program, 'getParseResults', [source]);",
            0,
            '',
            True,
        ),
    ),
)
def test_disabling_native_binding_proof_admits_an_incomplete_selected_stub(
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


@pytest.mark.parametrize(
    'read,identity',
    (
        ('bind', 'first===session.bind(path)'),
        (
            'parsed',
            'first.parserOutput.parseTree===session.parsed(path).parserOutput.parseTree',
        ),
        (
            'diagnostics',
            'JSON.stringify(first)===JSON.stringify(session.diagnostics(path))',
        ),
    ),
)
def test_selected_unreferenced_stub_enrolls_on_each_bounded_native_read(
    context_root: Path, read: str, identity: str
) -> None:
    path = context_root / 'typings/late.pyi'
    path.write_text('value: int\n')
    result = session_probe(
        context_root,
        'const path=request.root+"/typings/late.pyi";\n'
        f'const first=session.{read}(path);\n'
        'const tree=session.parsed(path).parserOutput.parseTree;\n'
        'const scope=session.native(1920).getScope(tree,session.node_info);\n'
        'const symbol=scope.symbolTable.get("value"),declaration=symbol.getDeclarations()[0];\n'
        f'return [{identity},tree.nodeType,session.diagnostics(path),\n'
        'session.bind(path).isBindingRequired(),\n'
        'Number.isInteger(symbol.id)&&symbol.id>0,Number.isInteger(declaration.node.id)&&declaration.node.id>0,\n'
        'declaration.type,declaration.node.start,declaration.node.length];',
    )
    value = json.loads(result.stdout)
    assert (
        result.returncode,
        value['value'],
        str(path) in value['report']['stub_inputs'],
        str(path) in value['report']['tracked'],
        (str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        in [(entry['path'], entry['sha256']) for entry in value['report']['loaded']],
        (str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        in [
            (entry['path'], entry['sha256']) for entry in value['report']['read_inputs']
        ],
    ) == (0, [True, 36, [], False, True, True, 1, 0, 5], True, False, True, True), (
        result.stdout
    )
