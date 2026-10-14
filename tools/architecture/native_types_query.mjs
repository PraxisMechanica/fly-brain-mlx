// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { realpathSync } from 'node:fs';
import { fail, object, string, integer } from './native_types_values.mjs';
/** @param {NativeTypes.Context} context @param {Map<string,string>} sources @param {NativeTypes.Projector} projector @param {NativeTypes.RecordValue} item */
export function query(context, sources, projector, item) {
  const path = realpathSync(string(item.path, 'type query path'));
  if (!sources.has(path)) fail('native type query is outside discovery');
  const uri = context.Uri.file(path, context.services);
  const parsed = context.program.getParseResults(uri);
  if (!parsed || context.program.getParseDiagnostics(uri)?.length) fail(`native source parse failed: ${path}`);
  const position = { line: integer(item.line, 'type query line') - 1, character: integer(item.column, 'type query column') };
  if (position.line < 0) fail('type query line is not one-based');
  const positionApi = /** @type {{convertPositionToOffset(position: NativeTypes.Position, lines: unknown): number | undefined; convertOffsetToPosition(offset: number, lines: unknown): NativeTypes.Position}} */ (object(context.native(7071), 'native position helpers'));
  const offset = positionApi.convertPositionToOffset(position, parsed.tokenizerOutput.lines);
  const translated = offset === undefined ? undefined : positionApi.convertOffsetToPosition(offset, parsed.tokenizerOutput.lines);
  if (!translated || translated.line !== position.line || translated.character !== position.character) fail('native type query position escapes its source line');
  const parseApi = /** @type {{findNodeByOffset(tree: unknown, offset: number): NativeTypes.NameNode | undefined}} */ (object(context.native(1146), 'native parse helpers'));
  const node = offset === undefined ? undefined : parseApi.findNodeByOffset(parsed.parserOutput.parseTree, offset);
  if (!node || offset === undefined || node.nodeType !== 38 || offset < node.start || offset >= node.start + node.length) fail(`native type query is not an exact name location: ${path}:${item.line}:${item.column}`);
  const result = context.program.evaluator.getTypeOfExpression(node);
  if (!result || result.isIncomplete) fail(`native expression type is missing or incomplete: ${path}:${item.line}:${item.column}`);
  const declarations = context.program.evaluator.getDeclInfoForNameNode(node)?.decls || [];
  return {
    path, line: item.line, column: item.column, type: projector.type(result.type),
    declarations: declarations.map((declaration) => {
      const resolved = context.program.evaluator.resolveAliasDeclaration(declaration, true);
      if (!resolved) fail('native declaration alias is unresolved');
      return projector.source.declaration(resolved);
    }),
  };
}
