// @ts-check
/// <reference path="./native_python_declarations_api.d.ts" />
import { uri } from './native_python_observation.mjs';
import { array, boolean, fail, integer, invoke, object, string } from './native_types_values.mjs';

/** @param {unknown} value @param {string} label @returns {number} */
function native_id(value, label) {
  const id = integer(value, label);
  if (id === 0) fail(`${label} is zero`);
  return id;
}
/** @param {unknown} value @returns {NativeBoundDeclarations.Node} */
function node(value) {
  const current = object(value, 'native declaration node');
  native_id(current.id, 'native node ID'); integer(current.nodeType, 'native node kind');
  integer(current.start, 'native node offset'); integer(current.length, 'native node length'); object(current.d, 'native node payload');
  return /** @type {NativeBoundDeclarations.Node} */ (current);
}
/** @param {unknown} value @returns {NativeBoundDeclarations.Position} */
function position(value) {
  const current = object(value, 'native declaration position');
  return Object.freeze({line: integer(current.line, 'native declaration line'), character: integer(current.character, 'native declaration column')});
}
/** @param {unknown} value @returns {NativeBoundDeclarations.Range} */
function range(value) {
  const current = object(value, 'native declaration range'), start = position(current.start), end = position(current.end);
  if (end.line < start.line || end.line === start.line && end.character < start.character) fail('native declaration range is reversed');
  return Object.freeze({start, end});
}

/** Observe bound facts only; the enclosing withSession report supplies provenance and lifetime.
 * Scope/declaration indexes are local; node/Symbol IDs are native. Raw declaration URI/range are independent of lexical spans.
 * @param {NativePython.Session} session @param {string} path @returns {NativeBoundDeclarations.Observation} */
export function observe_declarations(session, path) {
  const api = session.native(1920), reader = object(session.node_info, 'native declaration reader');
  if (typeof reader.get !== 'function') fail('native declaration reader method is missing');
  const parsed = object(session.parsed(path), `${path}: native declaration parse`);
  const output = object(parsed.parserOutput, 'native declaration parser output'), tree = node(output.parseTree);
  const lines = object(parsed.tokenizerOutput, 'native declaration tokenizer output').lines;
  const lexicalUri = uri(object(invoke(api, 'getFileInfo', [tree, reader]), 'native declaration file info').fileUri);
  /** @type {Map<number,NativeBoundDeclarations.Node>} */ const nodes = new Map();
  /** @type {{owner: NativeBoundDeclarations.Node; scope: NativeBoundDeclarations.Scope}[]} */ const scopes = [];
  const pending = [tree];
  while (pending.length) {
    const current = node(pending.pop());
    if (nodes.has(current.id)) fail('native declaration parsed node ID is duplicated');
    nodes.set(current.id, current);
    const value = invoke(api, 'getScope', [current, reader]);
    if (value !== undefined) {
      const scope = object(value, 'native declaration scope');
      if (!(scope.symbolTable instanceof Map) || !(scope.notLocalBindings instanceof Map)) fail('native declaration scope maps are invalid');
      scopes.push({owner: current, scope: /** @type {NativeBoundDeclarations.Scope} */ (scope)});
    }
    pending.push(...array(invoke(session.native(8821), 'getChildNodes', [current]), 'native declaration child nodes').filter((child) => child !== undefined).map(node));
  }
  /** @param {NativeBoundDeclarations.Node} current @returns {NativeBoundDeclarations.ParsedNode} */
  const ref = (current) => {
    const source = uri(object(invoke(api, 'getFileInfo', [current, reader]), 'native declaration lexical file').fileUri);
    if (source !== lexicalUri || current.start + current.length > tree.start + tree.length) fail('native declaration node escapes selected source');
    const at = (/** @type {number} */ offset) => position(invoke(session.native(7071), 'convertOffsetToPosition', [offset, lines]));
    return Object.freeze({native_id: current.id, native_kind: current.nodeType, start: current.start, length: current.length, lexical_uri: source,
      span: Object.freeze({start: at(current.start), end: at(current.start + current.length)}), name: current.nodeType === 38 ? string(current.d.value, 'native parsed name') : null,
      unreachable: boolean(invoke(api, 'isCodeUnreachable', [current, reader]), 'native declaration reachability')});
  };
  /** @type {NativeBoundDeclarations.Declaration[]} */ const declarations = [];
  /** @type {Map<unknown,number>} */ const indexes = new Map();
  /** @param {unknown} value @returns {number} */
  const declaration = (value) => {
    const existing = indexes.get(value);
    if (existing !== undefined) return existing;
    const current = object(value, 'native bound declaration'), target = node(current.node), kind = integer(current.type, 'native declaration category');
    const index = declarations.length;
    declarations.push(Object.freeze({index, native_category: kind, node: ref(target), origin: kind === 0 ? 'intrinsic' : nodes.get(target.id) === target ? 'parsed' : 'unmatched_native_node',
      raw_uri: uri(current.uri), raw_range: range(current.range), fallback_uri: current.submoduleFallback === undefined ? null : uri(object(current.submoduleFallback, 'native declaration fallback').uri)}));
    indexes.set(value, index);
    return index;
  };
  const bindings = scopes.flatMap(({scope}, index) => [...scope.symbolTable].map(([name, value]) => {
    const symbol = object(value, 'native declaration Symbol');
    const declared = array(invoke(symbol, 'getDeclarations', []), 'native Symbol declarations').map(declaration);
    if (!declared.length) fail('native declaration Symbol has no declarations');
    return Object.freeze({scope: index, name: string(name, 'native binding name'), native_symbol_id: native_id(symbol.id, 'native Symbol ID'), native_flags: integer(symbol._flags, 'native Symbol flags'), declarations: Object.freeze(declared)});
  }));
  const scopeIndexes = new Map(scopes.map(({scope}, index) => [scope, index]));
  return Object.freeze({path, capability: 'native_bound_declarations',
    missing: Object.freeze(['complete_authored_bindings', 'parsed_name_roles', 'declaration_payloads', 'alias_resolution', 'types', 'calls', 'effects', 'control_flow', 'runtime_targets']),
    nodes: Object.freeze([...nodes.values()].map(ref)), declarations: Object.freeze(declarations), bindings: Object.freeze(bindings),
    scopes: Object.freeze(scopes.map(({owner, scope}, index) => Object.freeze({index, native_kind: integer(scope.type, 'native scope kind'), owner: owner.id,
      parent: scopeIndexes.get(/** @type {NativeBoundDeclarations.Scope} */ (scope.parent)) ?? null, parent_kind: scope.parent === undefined ? null : integer(object(scope.parent, 'native parent scope').type, 'native parent scope kind'),
      dynamic: boolean(scope.hasPotentiallyDynamicSymbolTable, 'native dynamic scope'), nonlocal_bindings: Object.freeze([...scope.notLocalBindings].map(([name, kind]) => Object.freeze(/** @type {[string,number]} */ ([string(name, 'native nonlocal name'), integer(kind, 'native nonlocal binding kind')]))))})))});
}
