import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_sources_records import NativeBinding as NativeBinding
from tools.architecture.native_sources_records import NativeExport as NativeExport
from tools.architecture.native_sources_records import NativeImport as NativeImport
from tools.architecture.native_sources_records import NativeInput as NativeInput
from tools.architecture.native_sources_records import NativeSource as NativeSource
from tools.architecture.native_sources_records import (
    NativeSourceInventory as NativeSourceInventory,
)
from tools.architecture.native_sources_records import NativeTarget as NativeTarget
from tools.architecture.native_types_schema import boolean, integer, string, values
from tools.architecture.symbols import Location


def source_inputs(root: Path, paths: Sequence[str]) -> tuple[NativeInput, ...]:
    root = root.resolve()
    if not paths or len(set(paths)) != len(paths):
        raise ValueError('COV002: native input scope is empty or duplicated')
    result: list[NativeInput] = []
    for name in paths:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not (
            path.name.endswith('.mjs') or path.name.endswith('.d.ts')
        ):
            raise ValueError('COV002: native input escapes scope or format: ' + name)
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError('COV002: native input is missing: ' + name) from error
        result.append(NativeInput(str(path), digest))
    if len({item.path for item in result}) != len(result):
        raise ValueError('COV002: native canonical input is duplicated')
    return tuple(result)


def location(value: JsonValue) -> Location:
    item = object_value(value)
    result = Location(
        string(item.get('path')),
        integer(item.get('line')),
        integer(item.get('column')),
        integer(item.get('end_line')),
        integer(item.get('end_column')),
    )
    if result.line == 0 or (result.end_line, result.end_column) < (
        result.line,
        result.column,
    ):
        raise ValueError('COV002: native source location is invalid')
    return result


def target(value: JsonValue) -> NativeTarget:
    item = object_value(value)
    declarations = tuple(location(value) for value in values(item.get('declarations')))
    if not declarations:
        raise ValueError('COV002: native target has no declaration identity')
    return NativeTarget(
        string(item.get('name')), integer(item.get('flags')), declarations
    )


def binding(value: JsonValue) -> NativeBinding:
    item = object_value(value)
    return NativeBinding(
        string(item.get('name')),
        string(item.get('kind')),
        location(item.get('location')),
        target(item.get('target')),
    )


def parse_inventory(value: JsonValue) -> NativeSourceInventory:
    item = object_value(value)
    if (
        type(item.get('schema')) is not int
        or item.get('schema') != 1
        or item.get('version') != '5.9.3'
    ):
        raise ValueError('COV002: native inventory schema/version changed')
    files: list[NativeSource] = []
    for value in values(item.get('files')):
        file = object_value(value)
        imports: list[NativeImport] = []
        for value in values(file.get('imports')):
            imported = object_value(value)
            imports.append(
                NativeImport(
                    string(imported.get('specifier')),
                    location(imported.get('location')),
                    target(imported.get('target')),
                    boolean(imported.get('type_only')),
                )
            )
        exports: list[NativeExport] = []
        for value in values(file.get('exports')):
            exported = object_value(value)
            exports.append(
                NativeExport(
                    string(exported.get('name')), target(exported.get('target'))
                )
            )
        files.append(
            NativeSource(
                NativeInput(string(file.get('path')), string(file.get('sha256'))),
                tuple(binding(value) for value in values(file.get('declarations'))),
                tuple(binding(value) for value in values(file.get('bindings'))),
                tuple(imports),
                tuple(exports),
            )
        )
    if not files:
        raise ValueError('COV002: native inventory is empty')
    inputs = tuple(
        NativeInput(
            string(object_value(value).get('path')),
            string(object_value(value).get('sha256')),
        )
        for value in values(item.get('inputs'))
    )
    artifacts = tuple(
        (name, string(value))
        for name, value in object_value(item.get('artifacts')).items()
    )
    return NativeSourceInventory(
        string(item.get('version')), tuple(files), inputs, artifacts
    )


def inspect_native_sources(
    root: Path,
    sources: Sequence[NativeInput],
    package: Path,
    *,
    configuration: Sequence[NativeInput] = (),
    node: str = 'node',
    bridge: Path | None = None,
) -> NativeSourceInventory:
    if not sources:
        raise ValueError('COV002: native input scope is empty')
    request = {
        'schema': 1,
        'root': str(root.resolve()),
        'package': str(package.resolve()),
        'configuration': [
            {'path': source.path, 'sha256': source.sha256} for source in configuration
        ],
        'sources': [
            {'path': source.path, 'sha256': source.sha256} for source in sources
        ],
    }
    selected = bridge or Path(__file__).with_suffix('.mjs')
    try:
        result = subprocess.run(
            [node, str(selected)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=root,
            timeout=90,
            check=False,
        )
        value = cast(JsonValue, json.loads(result.stdout))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise ValueError(
            'COV002: native source inventory could not complete'
        ) from error
    response = object_value(value)
    if result.returncode or 'error' in response:
        raise ValueError(
            string(response.get('error'))
            if 'error' in response
            else 'COV002: native source inventory failed'
        )
    inventory = parse_inventory(response)
    if tuple(file.input for file in inventory.files) != tuple(sources):
        raise ValueError(
            'COV002: native inventory differs from requested input discovery'
        )
    inputs = {item.path: item.sha256 for item in inventory.inputs}
    for item in (*inventory.inputs, *sources, *configuration):
        try:
            digest = hashlib.sha256(Path(item.path).read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError(
                'COV002: native input disappeared: ' + item.path
            ) from error
        if digest != item.sha256 or inputs.get(item.path) != item.sha256:
            raise ValueError(
                'COV002: native input changed or was not parsed: ' + item.path
            )
    return inventory
