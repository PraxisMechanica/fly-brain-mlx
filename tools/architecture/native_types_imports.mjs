// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { NativeSources } from './native_types_sources.mjs';
import { fail, object, array, string, integer, boolean, invoke } from './native_types_values.mjs';
/** @param {NativeSources} source */
export function verifyImports(source) {
  const api = object(source.context.native(1920), 'native import node API');
  const reader = object(source.context.program.analyzerNodeInfoReader, 'native analyzer reader');
  if ([api.getImportInfo, api.isCodeUnreachable, reader.get].some((method) => typeof method !== 'function')) fail('native import node API or analyzer reader is missing');
  for (const info of source.context.program.getSourceFileInfoList()) {
    const path = string(invoke(info.uri, 'getFilePath', []), 'native loaded source path');
    if (!path) fail('native loaded source path is empty');
    const file = source.file(path);
    const parsed = source.context.program.getParseResults(info.uri);
    if (parsed === undefined) {
      if (source.sources.has(file.path)) fail(`native required source parse is missing: ${file.path}`);
      continue;
    }
    for (const value of array(object(parsed.parserOutput, 'native parser output').importedModules, 'native parsed imports')) {
      const descriptor = object(value, 'native import descriptor'), node = object(descriptor.nameNode, 'native import name node');
      const names = array(object(node.d, 'native import name details').nameParts, 'native import name parts');
      const count = array(descriptor.nameParts, 'native import descriptor parts').length;
      const target = count === names.length ? node : object(names[integer(count - 1, 'native import prefix index')], 'native import prefix node');
      const position = object(invoke(source.context.native(7071), 'convertOffsetToPosition', [integer(target.start, 'native import offset'), parsed.tokenizerOutput.lines]), 'native import position');
      const location = `${file.path}:${integer(position.line, 'native import line') + 1}:${integer(position.character, 'native import column')}`;
      const result = object(invoke(api, 'getImportInfo', [target, reader]), `native import record at ${location}`);
      const name = string(result.importName, `native import name at ${location}`);
      if (!name) fail(`native import name is empty at ${location}`);
      for (const value of array(result.resolvedUris, `native import paths at ${location}`)) {
        const uri = object(value, `native import URI at ${location}`);
        const path = string(invoke(uri, 'getFilePath', []), `native import path at ${location}`);
        const empty = boolean(invoke(uri, 'isEmpty', []), `native import empty URI at ${location}`);
        if (empty !== (path === '')) fail(`native import URI disagrees with its path at ${location}`);
      }
      const found = boolean(result.isImportFound, `native import found flag at ${location}`), partial = boolean(result.isPartlyResolved, `native import partial flag at ${location}`);
      const unreachable = boolean(invoke(api, 'isCodeUnreachable', [target, reader]), `native import reachability at ${location}`);
      if (!unreachable && (!found || partial)) fail(`native unresolved import ${name} at ${location}`);
    }
  }
}
