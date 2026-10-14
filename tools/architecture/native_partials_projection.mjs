// @ts-check
/// <reference path="./native_partials_api.d.ts" />
import { join } from 'node:path';
import { fail, object, array, string, integer, boolean, hash, invoke } from './native_types_values.mjs';
import { Projector } from './native_types_projector.mjs';
const STUB_HASH = '09683310003974eee453bf8851422cd8e8a6f6226db465bbccc30f39da446140';

/** @param {unknown} value @returns {NativeCalls.Node} */
function node(value) {
  const result = object(value, 'native partial node');
  integer(result.nodeType, 'native partial node category'); integer(result.id, 'native partial node identity');
  integer(result.start, 'native partial node start'); integer(result.length, 'native partial node length');
  object(result.d, 'native partial node details');
  return /** @type {NativeCalls.Node} */ (result);
}
/** @param {unknown} value @returns {boolean | null} */
function flag(value) { return value === undefined ? null : boolean(value, 'native partial result flag'); }
/** @param {NativeTypes.Context} context @param {NativeCalls.Node} value @param {string} method */
function evaluated(context, value, method) {
  const result = object(invoke(context.program.evaluator, method, [value]), 'native partial type result');
  if (flag(result.isIncomplete) || flag(result.typeErrors)) fail('native partial type is incomplete or erroneous');
  object(result.type, 'native partial type');
  return result;
}
/** @param {NativeTypes.Context} context @param {string} path @param {unknown} lines @param {NativeCalls.Node} value @returns {NativeCalls.Location} */
function location(context, path, lines, value) {
  const api = context.native(7071);
  const start = object(invoke(api, 'convertOffsetToPosition', [value.start, lines]), 'native partial start');
  const end = object(invoke(api, 'convertOffsetToPosition', [value.start + value.length, lines]), 'native partial end');
  return { path, line: integer(start.line, 'native line') + 1, column: integer(start.character, 'native column'), end_line: integer(end.line, 'native end line') + 1, end_column: integer(end.character, 'native end column') };
}
/** @param {NativeTypes.Context} context @param {Projector} projector @param {string} path @param {unknown} lines @param {NativeCalls.Node} value @returns {NativePartials.Expression} */
function expression(context, projector, path, lines, value) {
  const result = evaluated(context, value, 'getTypeOfExpression');
  const name = value.nodeType === 38 ? value : value.nodeType === 35 ? node(value.d.member) : undefined;
  const declarations = name === undefined ? [] : (context.program.evaluator.getDeclInfoForNameNode(name)?.decls || []).map((declaration) => {
    const resolved = context.program.evaluator.resolveAliasDeclaration(declaration, true);
    if (resolved === undefined) fail('native partial declaration alias is unresolved');
    const fact = projector.source.declaration(resolved);
    if (fact === null) fail('native partial declaration is missing');
    return fact;
  });
  return { node_id: value.id, native_kind: value.nodeType, location: location(context, path, lines, value), type: projector.type(result.type), declarations, is_incomplete: flag(result.isIncomplete), type_errors: flag(result.typeErrors) };
}
/** @param {Projector} projector @param {unknown} value @param {string} path @param {string} name @param {number} line */
function library(projector, value, path, name, line) {
  const type = object(value, 'native partial library type'), shared = object(type.shared, 'native partial library details');
  const declaration = projector.source.declaration(shared.declaration);
  if (shared.fullName !== name || !declaration || declaration.path !== path || declaration.sha256 !== STUB_HASH || declaration.line !== line) fail('native partial library declaration identity changed');
}
/** @param {NativeTypes.Context} context @param {Projector} projector @param {string} path @param {unknown} lines @param {NativeCalls.Node} value @param {NativeTypes.RecordValue} callee @param {string} stub @returns {NativePartials.Construction} */
function construction(context, projector, path, lines, value, callee, stub) {
  const calleeResult = evaluated(context, node(value.d.leftExpr), 'getTypeOfExpression');
  library(projector, callee, stub, 'functools.partial', 171);
  const result = evaluated(context, value, 'getTypeResult');
  const selected = array(result.overloadsUsedForCall, 'native partial constructor signatures');
  if (selected.length !== 1) fail('native partial constructor selection is missing or ambiguous');
  library(projector, selected[0], stub, 'functools.partial.__new__', 178);
  const resultType = object(result.type, 'native partial constructed type');
  library(projector, resultType, stub, 'functools.partial', 171);
  const residual = object(object(resultType.priv, 'native partial result details').partialCallType, 'native partial residual shape');
  library(projector, residual, stub, 'functools.partial.__call__', 179);
  const bound = invoke(context.program.evaluator, 'getBoundMagicMethod', [resultType, '__call__']);
  library(projector, bound, stub, 'functools.partial.__call__', 179);
  const arguments_ = array(value.d.args, 'native partial arguments').map(node);
  const first = arguments_[0];
  if (!first || arguments_.some((argument) => argument.d.argCategory !== 0) || first.d.name !== undefined) fail('unsupported native partial argument form');
  const wrapped = expression(context, projector, path, lines, node(first.d.valueExpr));
  const captures = arguments_.slice(1).map((argument) => ({ argument_node_id: argument.id, name: argument.d.name === undefined ? null : string(node(argument.d.name).d.value, 'native partial keyword'), expression: expression(context, projector, path, lines, node(argument.d.valueExpr)) }));
  return { node_id: value.id, location: location(context, path, lines, value), sha256: hash(path), callee_type: projector.type(callee), constructor_signature: projector.type(selected[0]), wrapped, captures, result_type: projector.type(resultType), residual_signature: projector.type(bound), is_incomplete: flag(result.isIncomplete), type_errors: flag(result.typeErrors), callee_is_incomplete: flag(calleeResult.isIncomplete), callee_type_errors: flag(calleeResult.typeErrors) };
}
/** @param {NativeTypes.Context} context @param {Projector} projector @param {string} path @param {string} packageRoot @returns {NativePartials.Construction[]} */
export function partialsInSource(context, projector, path, packageRoot) {
  const parsed = context.program.getParseResults(context.Uri.file(path, context.services));
  if (!parsed || context.program.getParseDiagnostics(context.Uri.file(path, context.services))?.length) fail(`native partial source parse failed: ${path}`);
  /** @type {NativePartials.Construction[]} */
  const partials = [];
  const pending = [node(parsed.parserOutput.parseTree)];
  while (pending.length) {
    const value = node(pending.pop());
    if (value.nodeType === 9) {
      const callee = object(object(invoke(context.program.evaluator, 'getTypeOfExpression', [node(value.d.leftExpr)]), 'native partial callee result').type, 'native partial callee');
      if (callee.category === 6 && object(callee.shared, 'native class details').fullName === 'functools.partial' && boolean(invoke(object(context.native(7349), 'native type API').TypeBase, 'isInstantiable', [callee]), 'native partial construction flag')) partials.push(construction(context, projector, path, parsed.tokenizerOutput.lines, value, callee, join(packageRoot, 'dist/typeshed-fallback/stdlib/functools.pyi')));
    }
    for (const child of array(invoke(context.native(8821), 'getChildNodes', [value]), 'native partial children')) if (child !== undefined) pending.push(node(child));
  }
  return partials.sort((a, b) => a.location.line - b.location.line || a.location.column - b.location.column || a.node_id - b.node_id);
}
