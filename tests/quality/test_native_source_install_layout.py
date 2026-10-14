import hashlib
import os
import re
from itertools import chain
from pathlib import Path

import pytest

from tests.quality.support import PROJECT
from tests.quality.test_native_sources import BRIDGE, PACKAGE
from tools.architecture.native_sources import (
    NativeInput,
    inspect_native_sources,
    source_inputs,
)


def bridge_inputs(root: Path) -> tuple[NativeInput, ...]:
    return source_inputs(
        root,
        tuple(
            sorted(
                str(path.relative_to(root))
                for path in chain(
                    BRIDGE.parent.glob('native_*.mjs'),
                    BRIDGE.parent.glob('native_*.d.ts'),
                )
            )
        ),
    )


def configuration() -> tuple[NativeInput, ...]:
    path = PROJECT / 'package.json'
    return (NativeInput(str(path), hashlib.sha256(path.read_bytes()).hexdigest()),)


@pytest.mark.parametrize('compiler_inside_root', [False, True])
def test_actual_pinned_compiler_inputs_work_in_both_install_layouts(
    compiler_inside_root: bool,
) -> None:
    root = (
        Path(os.path.commonpath((PROJECT, PACKAGE.resolve())))
        if compiler_inside_root
        else PROJECT
    )
    sources = bridge_inputs(root)
    report = inspect_native_sources(
        root, sources, PACKAGE, configuration=configuration()
    )
    assert {file.input for file in report.files} == set(sources)
    actual = {item.path: item.sha256 for item in report.inputs}
    for relative in ('package.json', 'lib/typescript.d.ts', 'lib/lib.es2022.full.d.ts'):
        path = (PACKAGE / relative).resolve()
        assert actual[str(path)] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_unregistered_library_lookalike_is_rejected_and_inner_guard_weakening_loses_it(
    tmp_path: Path,
) -> None:
    hidden = tmp_path / 'node_modules/typescript/lib/lib.es2022.full.d.ts'
    hidden.parent.mkdir(parents=True)
    hidden.write_text('export declare const value: 1;\n')
    source = tmp_path / 'source.mjs'
    source.write_text(
        'export {value} from "./node_modules/typescript/lib/lib.es2022.full.js";\n'
    )
    root = Path(os.path.commonpath((PROJECT, PACKAGE.resolve(), tmp_path)))
    sources = (
        *bridge_inputs(root),
        *source_inputs(root, (str(source.relative_to(root)),)),
    )
    with pytest.raises(
        ValueError,
        match='COV002: native parser reached undiscovered source: '
        + re.escape(str(hidden)),
    ):
        inspect_native_sources(root, sources, PACKAGE, configuration=configuration())
    for path in BRIDGE.parent.glob('native_*.mjs'):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    context = tmp_path / 'native_sources_context.mjs'
    text = context.read_text()
    guard = 'if (!compilerInputs.has(path))'
    assert guard in text
    context.write_text(text.replace(guard, 'if (false)'))
    report = inspect_native_sources(
        root,
        sources,
        PACKAGE,
        configuration=configuration(),
        bridge=tmp_path / BRIDGE.name,
    )
    scanned = next(file for file in report.files if file.input.path == str(source))
    assert scanned.exports[0].target.declarations[0].path == str(hidden)


def test_changed_compiler_artifact_still_rejects_in_containing_context(
    tmp_path: Path,
) -> None:
    package = tmp_path / 'compiler'
    package.mkdir()
    (package / 'package.json').write_text('{"version":"5.9.3"}')
    source = tmp_path / 'source.mjs'
    source.write_text('export const value = 1;\n')
    sources = source_inputs(tmp_path, ('source.mjs',))
    with pytest.raises(
        ValueError, match='COV002: TypeScript artifact changed: package.json'
    ):
        inspect_native_sources(tmp_path, sources, package)


def test_artifact_identity_is_checked_after_parsing_and_weakening_loses_it(
    tmp_path: Path,
) -> None:
    for path in BRIDGE.parent.glob('native_*.mjs'):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    driver = tmp_path / BRIDGE.name
    text = driver.read_text()
    assert 'verifyInputs(context);' in text
    driver.write_text(
        text.replace(
            'verifyInputs(context);',
            "ARTIFACTS['package.json'] = 'changed'; verifyInputs(context);",
        )
    )
    root = Path(os.path.commonpath((PROJECT, PACKAGE.resolve(), tmp_path)))
    sources = bridge_inputs(root)
    with pytest.raises(
        ValueError, match='COV002: TypeScript artifact changed: package.json'
    ):
        inspect_native_sources(
            root, sources, PACKAGE, configuration=configuration(), bridge=driver
        )
    context = tmp_path / 'native_sources_context.mjs'
    guard = '  verifyCompiler(packageRoot);'
    text = context.read_text()
    assert guard in text
    context.write_text(text.replace(guard, ''))
    report = inspect_native_sources(
        root, sources, PACKAGE, configuration=configuration(), bridge=driver
    )
    assert dict(report.artifacts)['package.json'] == 'changed'
