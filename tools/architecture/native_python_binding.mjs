// @ts-check
/// <reference path="./native_python_context_api.d.ts" />
import { realpathSync } from 'node:fs';
import { uri } from './native_python_observation.mjs';
import { fail, invoke, object } from './native_types_values.mjs';

/** @param {NativePython.Program} program @param {NativeTypes.Uri} source
 * @param {NativePython.FileSystem} fs @param {NativeTypes.Loader} native */
export function enroll(program, source, fs, native) {
  const resolved = uri(source);
  invoke(program, 'addInterimFile', [source]);
  const parsed = object(invoke(program, 'getParseResults', [source]), `${resolved}: native selected source binding`);
  const tree = object(object(parsed.parserOutput, `${resolved}: native selected parser output`).parseTree, `${resolved}: native selected module`);
  const reader = program.analyzerNodeInfoReader, scope = object(invoke(native(1920), 'getScope', [tree, reader]), `${resolved}: native selected scope`);
  const info = object(invoke(native(1920), 'getFileInfo', [tree, reader]), `${resolved}: native selected file info`);
  if (tree.nodeType !== 36 || scope.type !== 4 || !(scope.symbolTable instanceof Map) || realpathSync(uri(invoke(fs, 'getOriginalUri', [info.fileUri]))) !== resolved) fail(`native selected source binding differs: ${resolved}`);
}
