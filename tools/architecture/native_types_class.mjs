// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { fail, object, array, string, integer, boolean } from './native_types_values.mjs';
/** @param {NativeTypes.Projector} exporter @param {NativeTypes.RecordValue} value @param {NativeTypes.RecordValue} node */
export function projectClass(exporter, value, node) {
  const shared = object(value.shared, 'native class details');
  const priv = object(value.priv, 'native class specialization');
  node.name = string(shared.fullName, 'native class full name');
  node.native_source_id = integer(shared.typeSourceId, 'native class source identity');
  node.details_flags = integer(shared.flags, 'native class flags');
  node.declaration = exporter.source.declaration(shared.declaration);
  if (exporter.types.ClassType.isHierarchyPartiallyEvaluated(value)) fail('native class hierarchy is incomplete');
  node.protocol = boolean(exporter.types.ClassType.isProtocolClass(value), 'native Protocol flag');
  node.unspecialized = boolean(exporter.types.ClassType.isUnspecialized(value), 'native specialization flag');
  node.arguments = (priv.typeArgs === undefined ? [] : array(priv.typeArgs, 'native class arguments')).map((type) => exporter.type(type));
  node.type_parameters = array(shared.typeParams, 'native class type parameters').map((type) => exporter.type(type));
  node.bases = array(shared.baseClasses, 'native class bases').map((type) => exporter.type(type));
  node.tuple_arguments = (priv.tupleTypeArgs === undefined ? [] : array(priv.tupleTypeArgs, 'native tuple arguments')).map((arg) => ({ type: exporter.type(object(arg, 'native tuple argument').type), unbounded: object(arg, 'native tuple argument').isUnbounded === true }));
  if (priv.literalValue !== undefined) {
    if (!['string', 'boolean', 'number'].includes(typeof priv.literalValue)) fail('unsupported native class literal value');
    node.literal = priv.literalValue;
  }
}
