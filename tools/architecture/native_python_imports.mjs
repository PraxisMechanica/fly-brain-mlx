// @ts-check
/// <reference path="./native_python_context_api.d.ts" />
import { verifyParsedImports } from './native_types_imports.mjs';
import { boolean, fail, invoke, object } from './native_types_values.mjs';

/** @param {NativeTypes.Loader} native @param {Pick<NativePython.Program, 'analyzerNodeInfoReader'>} program
 * @param {string} path @param {unknown} sourceFile @param {boolean} tracked */
export function verifySourceImports(native, program, path, sourceFile, tracked) {
  const pending = boolean(invoke(sourceFile, 'isBindingRequired', []), 'native loaded binding state');
  const value = invoke(sourceFile, 'getParseResults', []);
  if (tracked && (pending || value === undefined)) fail(`native tracked source parse or binding is missing: ${path}`);
  if (!pending && value !== undefined) {
    object(value, 'native loaded parse');
    const parsed = /** @type {NativeTypes.Parsed} */ (value);
    verifyParsedImports(native, program.analyzerNodeInfoReader, path, parsed);
  }
}
