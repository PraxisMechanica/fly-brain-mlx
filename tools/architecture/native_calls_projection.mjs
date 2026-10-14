// @ts-check
/// <reference path="./native_calls_api.d.ts" />
import { fail, object, array, string, integer, boolean, hash, invoke } from './native_types_values.mjs';
import { Projector } from './native_types_projector.mjs';

/** @param {unknown} value @returns {NativeCalls.Node} */
function parseNode(value) {
  const node = object(value, 'native parse node');
  integer(node.nodeType, 'native node category'); integer(node.id, 'native node identity');
  integer(node.start, 'native node start'); integer(node.length, 'native node length');
  object(node.d, 'native node details');
  return /** @type {NativeCalls.Node} */ (node);
}
/** @param {NativeTypes.Context} context @param {NativeCalls.Node} node @param {string} method @param {string} path @param {unknown} lines */
function evaluated(context, node, method, path, lines) {
  const result = object(invoke(context.program.evaluator, method, [node]), 'native call type result');
  const at = location(context, path, lines, node);
  if ((result.isIncomplete !== undefined && boolean(result.isIncomplete, 'native incomplete flag')) || (result.typeErrors !== undefined && boolean(result.typeErrors, 'native type-error flag'))) fail(`native call type is incomplete or erroneous at ${path}:${at.line}:${at.column}`);
  object(result.type, 'native call expression type');
  return result;
}
/** @param {NativeTypes.Context} context @param {string} path @param {unknown} lines @param {NativeCalls.Node} node @returns {NativeCalls.Location} */
function location(context, path, lines, node) {
  const api = object(context.native(7071), 'native position API');
  const start = object(invoke(api, 'convertOffsetToPosition', [node.start, lines]), 'native start position');
  const end = object(invoke(api, 'convertOffsetToPosition', [node.start + node.length, lines]), 'native end position');
  return { path, line: integer(start.line, 'native start line') + 1, column: integer(start.character, 'native start column'), end_line: integer(end.line, 'native end line') + 1, end_column: integer(end.character, 'native end column') };
}
/** @param {NativeTypes.Context} context @param {Projector} projector @param {string} path @param {unknown} lines @param {NativeCalls.Node} node @returns {NativeCalls.Argument} */
function argument(context, projector, path, lines, node) {
  const category = (/** @type {const} */ (['simple', 'star', 'double_star']))[integer(node.d.argCategory, 'native argument category')];
  if (!category) fail('unsupported native argument category');
  const value = parseNode(node.d.valueExpr);
  return { node_id: node.id, location: location(context, path, lines, value), category, name: node.d.name === undefined ? null : string(parseNode(node.d.name).d.value, 'native keyword name'), type: projector.type(evaluated(context, value, 'getTypeOfExpression', path, lines).type) };
}
/** @param {NativeTypes.Context} context @param {Projector} projector @param {string} path @param {unknown} lines @param {NativeCalls.Node} node @returns {NativeCalls.Call} */
function call(context, projector, path, lines, node) {
  const at = location(context, path, lines, node);
  const left = parseNode(node.d.leftExpr);
  if (![38, 35, 9].includes(left.nodeType)) fail(`unsupported computed native call at ${path}:${at.line}:${at.column}`);
  const result = evaluated(context, node, 'getTypeResult', path, lines);
  const selected = array(result.overloadsUsedForCall, 'native selected call signatures');
  if (selected.length !== 1) fail(`native call target is missing or ambiguous at ${path}:${at.line}:${at.column}`);
  const signature = object(selected[0], 'native selected signature');
  if (signature.category !== 4) fail('native selected signature is not a function');
  const shared = object(signature.shared, 'native selected function details');
  const callee = object(evaluated(context, left, 'getTypeOfExpression', path, lines).type, 'native callable type');
  if (![4, 5, 6].includes(integer(callee.category, 'native callable category'))) fail(`native callable category is unsupported at ${path}:${at.line}:${at.column}`);
  const receiver = object(signature.priv, 'native selected function specialization').boundToType;
  const protocol = receiver === undefined ? false : boolean(invoke(object(context.native(7349), 'native type API').ClassType, 'isProtocolClass', [object(receiver, 'native bound receiver')]), 'native Protocol identity');
  const construction = callee.category === 6 && boolean(invoke(object(context.native(7349), 'native type API').TypeBase, 'isInstantiable', [callee]), 'native construction flag');
  /** @type {number | null} */
  let overload_index = null;
  if (callee.category === 5) {
    const variants = array(projector.types.OverloadedType.getOverloads(callee), 'native overload declarations');
    const matches = variants.map((value, index) => object(object(value, 'native overload').shared, 'native overload details').declaration === shared.declaration ? index : -1).filter((index) => index >= 0);
    if (matches.length !== 1) fail('native selected overload declaration is ambiguous');
    overload_index = integer(matches[0], 'native overload index');
  }
  return { node_id: node.id, location: at, sha256: hash(path), kind: construction ? 'construction' : callee.category === 6 ? 'callable_value' : 'function', callee_type: projector.type(callee), receiver_type: receiver === undefined ? null : projector.type(receiver), protocol, selected_signature: projector.type(signature), overload_index, arguments: array(node.d.args, 'native call arguments').map((value) => argument(context, projector, path, lines, parseNode(value))), result_type: projector.type(result.type) };
}
/** @param {NativeTypes.Context} context @param {Projector} projector @param {string} path @returns {NativeCalls.Call[]} */
export function callsInSource(context, projector, path) {
  const uri = context.Uri.file(path, context.services);
  const parsed = context.program.getParseResults(uri);
  if (!parsed || context.program.getParseDiagnostics(uri)?.length) fail(`native discovered source parse failed: ${path}`);
  /** @type {NativeCalls.Call[]} */
  const calls = [];
  const pending = [parseNode(parsed.parserOutput.parseTree)];
  while (pending.length) {
    const node = parseNode(pending.pop());
    if (node.nodeType === 9) calls.push(call(context, projector, path, parsed.tokenizerOutput.lines, node));
    for (const child of array(invoke(context.native(8821), 'getChildNodes', [node]), 'native children')) if (child !== undefined) pending.push(parseNode(child));
  }
  return calls.sort((a, b) => a.location.line - b.location.line || a.location.column - b.location.column || a.node_id - b.node_id);
}
