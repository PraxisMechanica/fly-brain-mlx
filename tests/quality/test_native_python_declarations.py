import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tests.quality.support import PROJECT
from tests.quality.test_native_python_context import edited_bridge
from tests.quality.test_native_python_session import context_root as context_root
from tests.quality.test_native_python_session import session_probe

BRIDGE = PROJECT / 'tools/architecture/native_python_session.mjs'
MODEL = (
    '# 🧠\nfrom .target import Thing as ImportedThing\n'
    'class Item:\n    value: int\n'
    'def factory(value: int) -> int:\n    local = value\n    return local\n'
    'callback = lambda captured: captured\nitems = [item for item in (1,)]\n'
    'if False:\n    dormant = 1\n'
)
STUB = (
    'from context_pkg.target import Thing as StubThing\n'
    'def make(value: int) -> StubThing: ...\n'
)
SETUP = (
    'const path=request.root+"/src/context_pkg/model.py";\n'
    'const tree=session.parsed(path).parserOutput.parseTree,api=session.native(1920);\n'
    'const scope=api.getScope(tree,session.node_info),symbol=scope.symbolTable.get("factory");\n'
    'const declared=symbol.getDeclarations()[0];\n'
)


@pytest.fixture
def declarations_root(context_root: Path) -> Path:
    (context_root / 'src/context_pkg/model.py').write_text(MODEL)
    (context_root / 'src/context_pkg/target.py').write_text('class Thing: ...\n')
    (context_root / 'typings/late.pyi').write_text(STUB)
    return context_root


def probe(
    root: Path, consumer: str, bridge: Path = BRIDGE
) -> subprocess.CompletedProcess[str]:
    observer = bridge.with_name('native_python_declarations.mjs')
    return session_probe(
        root,
        f'const {{observe_declarations}}=await import({json.dumps(observer.as_uri())});\n'
        + consumer,
        bridge=bridge,
    )


@pytest.mark.parametrize(
    'path,name,alias,category,scope_kinds',
    (
        ('src/context_pkg/model.py', 'factory', 'ImportedThing', 5, [4, 1, 2, 2, 3]),
        ('typings/late.pyi', 'make', 'StubThing', 5, [4, 2]),
    ),
)
def test_bound_facts_keep_real_ids_raw_alias_fields_and_intrinsic_ranges(
    declarations_root: Path,
    path: str,
    name: str,
    alias: str,
    category: int,
    scope_kinds: list[int],
) -> None:
    source = declarations_root / path
    result = probe(
        declarations_root,
        f'const path=request.root+{json.dumps("/" + path)};\n'
        'const tree=session.parsed(path).parserOutput.parseTree;\n'
        'const scope=session.native(1920).getScope(tree,session.node_info);\n'
        f'const symbol=scope.symbolTable.get({json.dumps(name)}),native=symbol.getDeclarations()[0];\n'
        'const observed=observe_declarations(session,path);\n'
        f'const binding=observed.bindings.find((value)=>value.name==={json.dumps(name)});\n'
        f'const alias=observed.bindings.find((value)=>value.name==={json.dumps(alias)});\n'
        'const declaration=observed.declarations[binding.declarations[0]],imported=observed.declarations[alias.declarations[0]];\n'
        'const intrinsic=observed.declarations.find((value)=>value.native_category===0);\n'
        'return [observed.capability,observed.missing,\n'
        '[binding.native_symbol_id===symbol.id,declaration.node.native_id===native.node.id,\n'
        'declaration.native_category,declaration.origin,declaration.node.lexical_uri===path,\n'
        'observed.scopes.map((value)=>value.native_kind)],\n'
        '[imported.raw_uri,imported.node.lexical_uri,imported.raw_range.start,imported.node.span.start],\n'
        '[intrinsic.origin,intrinsic.raw_range,intrinsic.node.native_kind],\n'
        '[Object.isFrozen(observed),Object.isFrozen(observed.bindings),Object.isFrozen(binding),Object.isFrozen(declaration.node.span.start)]];',
    )
    value = json.loads(result.stdout)
    alias_column = {'ImportedThing': 29, 'StubThing': 40}[alias]
    lexical_column = {'ImportedThing': 20, 'StubThing': 31}[alias]
    alias_line = {'ImportedThing': 1, 'StubThing': 0}[alias]
    assert (
        result.returncode,
        value['value'],
        str(source) in value['report']['tracked'],
        (str(source), hashlib.sha256(source.read_bytes()).hexdigest())
        in [(entry['path'], entry['sha256']) for entry in value['report']['loaded']],
        (str(source), hashlib.sha256(source.read_bytes()).hexdigest())
        in [
            (entry['path'], entry['sha256']) for entry in value['report']['read_inputs']
        ],
    ) == (
        0,
        [
            'native_bound_declarations',
            [
                'complete_authored_bindings',
                'parsed_name_roles',
                'declaration_payloads',
                'alias_resolution',
                'types',
                'calls',
                'effects',
                'control_flow',
                'runtime_targets',
            ],
            [True, True, category, 'parsed', True, scope_kinds],
            [
                str(declarations_root / 'src/context_pkg/target.py'),
                str(source),
                {'line': alias_line, 'character': alias_column},
                {'line': alias_line, 'character': lexical_column},
            ],
            [
                'intrinsic',
                {
                    'start': {'line': 0, 'character': 0},
                    'end': {'line': 0, 'character': 0},
                },
                36,
            ],
            [True, True, True, True],
        ],
        source.suffix == '.py',
        True,
        True,
    ), result.stdout + result.stderr


def test_dormant_parsed_name_has_utf16_identity_without_native_binding_proof(
    declarations_root: Path,
) -> None:
    result = probe(
        declarations_root,
        SETUP + 'const observed=observe_declarations(session,path);\n'
        'const dormant=observed.nodes.find((value)=>value.name==="dormant");\n'
        'return [dormant,observed.bindings.some((value)=>value.name==="dormant"),\n'
        'observed.declarations.some((value)=>value.node.native_id===dormant.native_id),\n'
        'observed.bindings.map((value)=>[value.name,value.scope]),\n'
        'observed.scopes.map((value)=>[value.index,value.parent,value.owner])];',
    )
    value = json.loads(result.stdout)['value']
    dormant = value[0]
    assert (
        result.returncode,
        dormant['native_id'] > 0,
        dormant['native_kind'],
        dormant['start'],
        dormant['length'],
        dormant['span'],
        dormant['unreachable'],
        value[1:3],
        {'value', 'local', 'captured', 'item'}.issubset(name for name, _ in value[3]),
        len(value[4]),
    ) == (
        0,
        True,
        38,
        len(MODEL[: MODEL.index('dormant')].encode('utf-16-le')) // 2,
        7,
        {'start': {'line': 10, 'character': 4}, 'end': {'line': 10, 'character': 11}},
        True,
        [False, False],
        True,
        5,
    ), result.stdout


def test_native_augmented_destination_keeps_its_unmatched_identity(
    declarations_root: Path,
) -> None:
    (declarations_root / 'src/context_pkg/model.py').write_text(
        MODEL + 'counter = 1\ncounter += 1\n'
    )
    result = probe(
        declarations_root,
        SETUP + 'const native=scope.symbolTable.get("counter").getDeclarations();\n'
        'const observed=observe_declarations(session,path);\n'
        'const binding=observed.bindings.find((value)=>value.name==="counter");\n'
        'const declarations=binding.declarations.map((index)=>observed.declarations[index]);\n'
        'return [declarations.map((value,index)=>[value.node.native_id===native[index].node.id,\n'
        'value.origin,value.node.span.start,value.node.lexical_uri===path,\n'
        'observed.nodes.some((node)=>node.native_id===value.node.native_id)]),\n'
        'observed.missing.includes("complete_authored_bindings")];',
    )
    assert (result.returncode, json.loads(result.stdout).get('value')) == (
        0,
        [
            [
                [True, 'parsed', {'line': 11, 'character': 0}, True, True],
                [
                    True,
                    'unmatched_native_node',
                    {'line': 12, 'character': 0},
                    True,
                    False,
                ],
            ],
            True,
        ],
    ), result.stdout + result.stderr


@pytest.mark.parametrize(
    'mutation,message',
    (
        ('tree.id=0;', 'native node ID is zero'),
        ('tree.length=-1;', 'native node length is not a nonnegative integer'),
        ('tree.d=undefined;', 'native node payload is not an object'),
        (
            'api.getScope(declared.node,session.node_info).symbolTable=undefined;',
            'native declaration scope maps are invalid',
        ),
        (
            'scope.notLocalBindings=undefined;',
            'native declaration scope maps are invalid',
        ),
        ('symbol.id=true;', 'native Symbol ID is not a nonnegative integer'),
        ('symbol.id=0;', 'native Symbol ID is zero'),
        (
            'symbol._flags=undefined;',
            'native Symbol flags is not a nonnegative integer',
        ),
        (
            'symbol.getDeclarations=undefined;',
            'native API method is missing: getDeclarations',
        ),
        (
            'symbol.getDeclarations=()=>[];',
            'native declaration Symbol has no declarations',
        ),
        (
            'symbol.getDeclarations=()=>[null];',
            'native bound declaration is not an object',
        ),
        ('declared.node=undefined;', 'native declaration node is not an object'),
        (
            'declared.type=true;',
            'native declaration category is not a nonnegative integer',
        ),
        ('declared.uri=undefined;', 'native API is not an object'),
        (
            'declared.range.end.character=-1;',
            'native declaration column is not a nonnegative integer',
        ),
        (
            'declared.range.end={line:0,character:0};',
            'native declaration range is reversed',
        ),
        ('declared.submoduleFallback={};', 'native API is not an object'),
        (
            'api.getChildNodes=undefined;session.native(8821).getChildNodes=undefined;',
            'native API method is missing: getChildNodes',
        ),
        (
            'session.node_info.get=undefined;',
            'native declaration reader method is missing',
        ),
    ),
)
def test_malformed_native_facts_cannot_become_declaration_observations(
    declarations_root: Path, mutation: str, message: str
) -> None:
    result = probe(
        declarations_root,
        SETUP + mutation + '\nreturn observe_declarations(session,path);',
    )
    assert (
        result.returncode,
        'COV002:' in result.stdout,
        message in result.stdout,
    ) == (
        2,
        True,
        True,
    ), result.stdout + result.stderr


def test_restoring_the_actual_native_method_repairs_the_same_symbol(
    declarations_root: Path,
) -> None:
    result = probe(
        declarations_root,
        SETUP
        + 'const original=symbol.getDeclarations;symbol.getDeclarations=()=>({});\n'
        'let failure;try{observe_declarations(session,path);}catch(error){failure=String(error);}\n'
        'symbol.getDeclarations=original;const observed=observe_declarations(session,path);\n'
        'const binding=observed.bindings.find((value)=>value.name==="factory");\n'
        'return [failure,binding.native_symbol_id===symbol.id,observed.declarations[binding.declarations[0]].node.native_id===declared.node.id];',
    )
    assert (result.returncode, json.loads(result.stdout)['value']) == (
        0,
        ['Error: COV002: native Symbol declarations is not an array', True, True],
    ), result.stdout


@pytest.mark.parametrize(
    'guard,mutation,predicate',
    (
        (
            'if (id === 0)',
            'declared.node.id=0;',
            'observed.declarations.some((value)=>value.node.native_id===0)',
        ),
        (
            'if (end.line < start.line || end.line === start.line && end.character < start.character)',
            'declared.range.end={line:0,character:0};',
            'observed.declarations.some((value)=>value.raw_range.end.line<value.raw_range.start.line)',
        ),
    ),
)
def test_disabling_independent_fact_guards_admits_their_malformed_records(
    declarations_root: Path, guard: str, mutation: str, predicate: str
) -> None:
    bridge = edited_bridge(
        declarations_root, guard, 'if (false)', 'native_python_declarations.mjs'
    ).with_name('native_python_session.mjs')
    result = probe(
        declarations_root,
        SETUP
        + mutation
        + '\nconst observed=observe_declarations(session,path);\nreturn '
        + predicate
        + ';',
        bridge,
    )
    assert (result.returncode, json.loads(result.stdout).get('value')) == (
        0,
        True,
    ), result.stdout + result.stderr
