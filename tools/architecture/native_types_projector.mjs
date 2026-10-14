// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { fail, object, array, string, integer, boolean } from './native_types_values.mjs';
import { projectClass } from './native_types_class.mjs';
import { projectFunction, projectOverloaded } from './native_types_callable.mjs';
import { projectTypeVar } from './native_types_typevar.mjs';
const CATEGORIES = ['unbound', 'unknown', 'any', 'never', 'function', 'overloaded', 'class', 'module', 'union', 'typevar'];

export class Projector {
  /** @param {NativeTypes.Context} context @param {NativeTypes.SourceSnapshot} source */
  constructor(context, source) {
    this.context = context;
    this.source = source;
    /** @type {NativeTypes.RecordValue[]} */
    this.nodes = [];
    /** @type {Map<object, number>} */
    this.ids = new Map();
    const typeApi = context.native(7349);
    const api = object(typeApi, 'native type helpers');
    for (const [owner, names] of [['ClassType', ['isProtocolClass', 'isUnspecialized', 'isHierarchyPartiallyEvaluated']], ['FunctionType', ['isPartiallyEvaluated', 'isGradualCallableForm', 'getParamDefaultType', 'getParamType', 'getEffectiveReturnType']], ['OverloadedType', ['getOverloads', 'getImplementation']]]) {
      const methods = object(api[string(owner, 'native helper owner')], 'native helper group');
      for (const name of array(names, 'native helper methods')) if (typeof methods[string(name, 'native helper method')] !== 'function') fail('native type helper is missing');
    }
    this.types = /** @type {NativeTypes.TypeHelpers} */ (typeApi);
  }
  /** @param {unknown} value @returns {number} */
  type(value) {
    const input = object(value, 'native type');
    const cached = this.ids.get(input);
    if (cached !== undefined) return cached;
    const category = CATEGORIES[integer(input.category, 'native type category')];
    if (!category || category === 'module') fail(`unsupported native type category: ${input.category}`);
    const id = this.nodes.length;
    this.ids.set(input, id);
    /** @type {NativeTypes.RecordValue} */
    const node = { id, category, flags: integer(input.flags, 'native type flags') };
    this.nodes.push(node);
    if (this.nodes.length > 20000) fail('native type graph exceeds supported node count 20000');
    if (category === 'class') projectClass(this, input, node);
    else if (category === 'function') projectFunction(this, input, node);
    else if (category === 'overloaded') projectOverloaded(this, input, node);
    else if (category === 'union') node.members = array(object(input.priv, 'native union details').subtypes, 'native union members').map((member) => this.type(member));
    else if (category === 'typevar') projectTypeVar(this, input, node);
    else if (category === 'any') node.ellipsis = boolean(object(input.priv, 'native Any details').isEllipsis, 'native Any ellipsis flag');
    return id;
  }
}
