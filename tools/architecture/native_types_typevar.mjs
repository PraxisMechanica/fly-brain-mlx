// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { fail, object, array, string, integer, boolean } from './native_types_values.mjs';
/** @param {NativeTypes.Projector} exporter @param {NativeTypes.RecordValue} value @param {NativeTypes.RecordValue} node */
export function projectTypeVar(exporter, value, node) {
  const shared = object(value.shared, 'native type variable');
  const priv = object(value.priv, 'native type-variable scope');
  if (shared.kind !== exporter.types.TypeVarKind.TypeVar || shared.recursiveAlias !== undefined) fail('unsupported native ParamSpec, TypeVarTuple or recursive alias');
  node.name = string(shared.name, 'native type-variable name');
  node.scope = priv.scopeId === undefined ? null : string(priv.scopeId, 'native type-variable scope');
  node.variance = integer(shared.declaredVariance, 'native declared variance');
  node.constraints = array(shared.constraints, 'native type-variable constraints').map((type) => exporter.type(type));
  node.bound = shared.boundType === undefined ? null : exporter.type(shared.boundType);
  node.default_type = shared.defaultType === undefined ? null : exporter.type(shared.defaultType);
  node.default_explicit = boolean(shared.isDefaultExplicit, 'native type-variable default flag');
}
