import hashlib
import json
from pathlib import Path

import pytest

from tests.quality.test_native_python_context import edited_bridge, observe
from tests.quality.test_native_python_session import context_root as context_root
from tests.quality.test_native_python_session import session_probe
from tools.architecture.native_python_context import NativePythonContextReport

QUERIES = 'from typing import Any\nprecise: int = 1\ngradual: Any = 1\n'
CAPTURE = (
    'const path=request.root+"/src/context_pkg/queries.py";\n'
    'const prototype=session.native(2752).Program.prototype,original=prototype.getParseResults;\n'
    'let program;prototype.getParseResults=function(...args){program=this;return original.apply(this,args);};\n'
    'try{session.parsed(path);}finally{prototype.getParseResults=original;}\n'
)
INVOCATION = (
    'verifyParsedImports(native, program.analyzerNodeInfoReader, path, parsed);'
)


@pytest.fixture
def import_root(context_root: Path) -> Path:
    (context_root / 'src/context_pkg/queries.py').write_text(QUERIES)
    (context_root / 'typings/late.pyi').write_text('value: int\n')
    return context_root


def test_lazy_native_precise_any_and_selected_stub_keep_canonical_inputs(
    import_root: Path,
) -> None:
    result = session_probe(
        import_root,
        CAPTURE + 'const evaluator=program.evaluator,results=[];\n'
        'for(const [suffix,line] of [["/src/context_pkg/queries.py",1],["/src/context_pkg/queries.py",2],["/typings/late.pyi",0]]){\n'
        'const parsed=session.parsed(request.root+suffix);\n'
        'const offset=session.native(7071).convertPositionToOffset({line,character:0},parsed.tokenizerOutput.lines);\n'
        'const node=session.native(1146).findNodeByOffset(parsed.parserOutput.parseTree,offset);\n'
        'const value=evaluator.getTypeOfExpression(node);\n'
        'results.push([node.d.value,node.nodeType,value.type.category,value.type.shared?.fullName??null,value.type.priv?.isEllipsis??null,value.isIncomplete]);}\n'
        'return [evaluator===program.evaluator,results,program.getSourceFileInfoList().map((info)=>info.uri.getFilePath())];',
    )
    response = json.loads(result.stdout)
    stub = import_root / 'typings/late.pyi'
    assert (
        result.returncode,
        response['value'][:2],
        set(response['value'][2])
        <= {entry['raw_uri'] for entry in response['report']['loaded']},
        {
            (str(path), hashlib.sha256(path.read_bytes()).hexdigest())
            for path in (import_root / 'src/context_pkg/queries.py', stub)
        }
        <= {
            (entry['path'], entry['sha256'])
            for entry in response['report']['read_inputs']
        },
        str(stub) in response['report']['tracked'],
        (str(stub), hashlib.sha256(stub.read_bytes()).hexdigest())
        in [(entry['path'], entry['sha256']) for entry in response['report']['loaded']],
        'types' in response['report']['missing'],
    ) == (
        0,
        [
            True,
            [
                ['precise', 38, 6, 'builtins.int', None, False],
                ['gradual', 38, 2, None, False, False],
                ['value', 38, 6, 'builtins.int', None, False],
            ],
        ],
        True,
        True,
        False,
        True,
        True,
    ), result.stdout + result.stderr


@pytest.mark.parametrize(
    'consumer,pending_after',
    (
        ('return 1;', True),
        ('session.parsed(request.root+"/typings/external.pyi"); return 1;', False),
    ),
)
def test_loaded_import_observation_reads_native_state_without_forcing_binding(
    import_root: Path, consumer: str, pending_after: bool
) -> None:
    before = (
        "const pending = boolean(invoke(sourceFile, 'isBindingRequired', []), 'native loaded binding state');\n"
        "  const value = invoke(sourceFile, 'getParseResults', []);"
    )
    bridge = edited_bridge(
        import_root,
        before,
        'const forcing=program.getParseResults;program.getParseResults=()=>{throw new Error("forcing loaded parse");};'
        + before
        + 'program.getParseResults=forcing;process.stderr.write(JSON.stringify([path,pending,value!==undefined])+"\\n");',
        'native_python_imports.mjs',
    ).with_name('native_python_session.mjs')
    result = session_probe(import_root, consumer, bridge=bridge)
    response = json.loads(result.stdout)
    report = NativePythonContextReport.model_validate_json(
        json.dumps(response['report'])
    )
    states = [json.loads(line) for line in result.stderr.splitlines()]
    assert (
        result.returncode,
        {path for path, _, _ in states},
        set(report.tracked)
        <= {path for path, pending, parsed in states if not pending and parsed},
        any(pending for _, pending, _ in states),
        [
            pending
            for path, pending, _ in states
            if path == str(import_root / 'typings/external.pyi')
        ],
        all(
            hashlib.sha256(Path(entry.path).read_bytes()).hexdigest() == entry.sha256
            for entry in report.loaded
        ),
    ) == (
        0,
        {entry.raw_uri for entry in report.loaded},
        True,
        True,
        [True, pending_after],
        True,
    ), result.stdout + result.stderr
    with pytest.raises(
        ValueError, match='COV002: native Python context lacks active_imports'
    ):
        report.require('active_imports')


@pytest.mark.parametrize(
    'source,line,column',
    (
        ('import dependency\n', 1, 7),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import dependency\n',
            3,
            11,
        ),
    ),
)
def test_active_import_rejection_and_same_dependency_repair(
    import_root: Path, source: str, line: int, column: int
) -> None:
    (import_root / 'src/context_pkg/queries.py').write_text(source)
    with pytest.raises(
        ValueError,
        match=f'COV002: native unresolved import dependency at .*queries.py:{line}:{column}',
    ):
        observe(import_root)
    dependency = import_root / 'typings/dependency.pyi'
    dependency.write_text('value: int\n')
    repaired = observe(import_root)
    assert (str(dependency), hashlib.sha256(dependency.read_bytes()).hexdigest()) in {
        (entry.path, entry.sha256) for entry in repaired.loaded
    }


@pytest.mark.parametrize(
    'source',
    (
        'if False:\n    import missing_inactive\n',
        'import sys\nif sys.version_info >= (3, 14):\n    import missing_inactive\n',
        'from namespace.provider import value\n',
    ),
)
def test_native_unreachable_and_namespace_origins_remain_valid(
    import_root: Path, source: str
) -> None:
    (import_root / 'src/context_pkg/queries.py').write_text(source)
    provider = import_root / 'typings/namespace/provider.pyi'
    provider.parent.mkdir()
    provider.write_text('value: int\n')
    report = observe(import_root)
    assert str(import_root / 'src/context_pkg/queries.py') in {
        entry.path for entry in report.loaded
    }


@pytest.mark.parametrize(
    'mutation,message',
    (
        (
            'native(1920).getImportInfo=undefined;',
            'native import node API or analyzer reader is missing',
        ),
        (
            'native(1920).getImportInfo=()=>undefined;',
            'native import record at .*queries.py:1:5 is not an object',
        ),
        (
            'native(1920).getImportInfo=()=>({resolvedUris:[],isImportFound:true,isPartlyResolved:false});',
            'native import name at .*queries.py:1:5 is not a string',
        ),
        (
            'native(1920).getImportInfo=()=>({importName:"typing",isImportFound:true,isPartlyResolved:false});',
            'native import paths at .*queries.py:1:5 is not an array',
        ),
        (
            'native(1920).getImportInfo=()=>({importName:"typing",resolvedUris:[{getFilePath:()=>"directory",isEmpty:()=>true}],isImportFound:true,isPartlyResolved:false});',
            'native import URI disagrees with its path at .*queries.py:1:5',
        ),
        (
            'native(1920).getImportInfo=()=>({importName:"typing",resolvedUris:[],isImportFound:"yes",isPartlyResolved:false});',
            'native import found flag at .*queries.py:1:5 is not a boolean',
        ),
        (
            'native(1920).getImportInfo=()=>({importName:"typing",resolvedUris:[],isImportFound:true,isPartlyResolved:true});',
            'native unresolved import typing at .*queries.py:1:5',
        ),
        (
            'native(1920).isCodeUnreachable=()=>1;',
            'native import reachability at .*queries.py:1:5 is not a boolean',
        ),
        (
            'Object.defineProperty(program,"analyzerNodeInfoReader",{value:null});',
            'native analyzer reader is not an object',
        ),
        (
            'parsed.parserOutput.importedModules=null;',
            'native parsed imports is not an array',
        ),
    ),
)
def test_canonical_import_invocation_rejects_malformed_native_records(
    import_root: Path, mutation: str, message: str
) -> None:
    bridge = edited_bridge(
        import_root,
        INVOCATION,
        'if(path.endsWith("/src/context_pkg/queries.py")){'
        + mutation
        + '}'
        + INVOCATION,
        'native_python_imports.mjs',
    )
    with pytest.raises(ValueError, match='COV002: ' + message):
        observe(import_root, bridge=bridge)


@pytest.mark.parametrize(
    'before,after,message',
    (
        (
            "const value = invoke(sourceFile, 'getParseResults', [])",
            'const value = undefined',
            'native tracked source parse or binding is missing',
        ),
        (
            "invoke(sourceFile, 'isBindingRequired', [])",
            'true',
            'native tracked source parse or binding is missing',
        ),
        (
            "invoke(sourceFile, 'isBindingRequired', [])",
            'undefined',
            'native loaded binding state is not a boolean',
        ),
        (
            "const value = invoke(sourceFile, 'getParseResults', [])",
            'const value = {}',
            'native parser output is not an object',
        ),
        (
            'const pending =',
            'sourceFile.isBindingRequired=undefined; const pending =',
            'native API method is missing: isBindingRequired',
        ),
        (
            'const value =',
            'sourceFile.getParseResults=undefined; const value =',
            'native API method is missing: getParseResults',
        ),
    ),
    ids=(
        'missing_parse',
        'pending_binding',
        'invalid_binding_state',
        'invalid_parse',
        'missing_binding_api',
        'missing_parse_api',
    ),
)
def test_missing_or_invalid_required_binding_state_rejects_in_the_loaded_origin_pass(
    import_root: Path, before: str, after: str, message: str
) -> None:
    bridge = edited_bridge(
        import_root,
        before,
        after,
        'native_python_imports.mjs',
    )
    with pytest.raises(ValueError, match='COV002: ' + message):
        observe(import_root, bridge=bridge)


def test_disabling_tracked_binding_guard_admits_missing_native_parse(
    import_root: Path,
) -> None:
    bridge = edited_bridge(
        import_root,
        "const value = invoke(sourceFile, 'getParseResults', [])",
        'const value = path.endsWith("/queries.py") ? undefined : invoke(sourceFile, "getParseResults", [])',
        'native_python_imports.mjs',
    )
    with pytest.raises(
        ValueError, match='COV002: native tracked source parse or binding is missing'
    ):
        observe(import_root, bridge=bridge)
    target = bridge.with_name('native_python_imports.mjs')
    source = target.read_text()
    guard = 'if (tracked && (pending || value === undefined))'
    assert guard in source
    target.write_text(source.replace(guard, 'if (false)'))
    report = observe(import_root, bridge=bridge)
    assert str(import_root / 'src/context_pkg/queries.py') in {
        entry.path for entry in report.loaded
    }


@pytest.mark.parametrize(
    'module,guard,replacement',
    (
        ('native_python_imports.mjs', INVOCATION, 'void parsed;'),
        (
            'native_types_imports.mjs',
            'if (!unreachable && (!found || partial))',
            'if (false)',
        ),
    ),
)
def test_independent_invocation_and_predicate_weakening_admit_active_missing_import(
    import_root: Path, module: str, guard: str, replacement: str
) -> None:
    (import_root / 'src/context_pkg/queries.py').write_text('import dependency\n')
    bridge = edited_bridge(import_root, guard, replacement, module)
    report = observe(import_root, bridge=bridge)
    assert str(import_root / 'src/context_pkg/queries.py') in {
        entry.path for entry in report.loaded
    }


@pytest.mark.parametrize('guard', ('normal', 'weakened'))
def test_refreshed_import_guard_observes_a_newly_enrolled_stub(
    import_root: Path, guard: str
) -> None:
    (import_root / 'typings/late.pyi').write_text('import missing_late\nvalue: int\n')
    invocation = {'normal': INVOCATION, 'weakened': 'void parsed;'}[guard]
    bridge = edited_bridge(
        import_root, INVOCATION, invocation, 'native_python_imports.mjs'
    ).with_name('native_python_session.mjs')
    result = session_probe(
        import_root,
        'session.parsed(request.root+"/typings/late.pyi");process.stderr.write("late-read");return 1;',
        bridge=bridge,
    )
    assert (
        result.returncode,
        result.stderr,
        'native unresolved import missing_late at' in result.stdout,
    ) == {'normal': (2, 'late-read', True), 'weakened': (0, 'late-read', False)}[
        guard
    ], result.stdout
