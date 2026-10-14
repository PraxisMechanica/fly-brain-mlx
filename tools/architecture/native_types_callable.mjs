// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { fail, object, array, string, integer, boolean } from './native_types_values.mjs';
/** @param {NativeTypes.Projector} exporter @param {unknown} value @param {number} index @param {NativeTypes.RecordValue} type */
function parameter(exporter, value, index, type) {
  const parameter = object(value, 'native function parameter');
  const category = integer(parameter.category, 'native parameter category');
  let kind = ['simple', 'args', 'kwargs'][category];
  if (exporter.types.isPositionOnlySeparator(parameter)) kind = 'positional_separator';
  if (exporter.types.isKeywordOnlySeparator(parameter)) kind = 'keyword_separator';
  if (!kind) fail(`unsupported native parameter category: ${category}`);
  const name = parameter.name === undefined ? null : string(parameter.name, 'native parameter name');
  const separator = kind.endsWith('_separator');
  const defaultType = exporter.types.FunctionType.getParamDefaultType(type, index);
  return {
    name, kind, flags: integer(parameter.flags, 'native parameter flags'),
    type: separator ? null : exporter.type(exporter.types.FunctionType.getParamType(type, index)),
    default_type: defaultType === undefined ? null : exporter.type(defaultType),
  };
}
/** @param {NativeTypes.Projector} exporter @param {NativeTypes.RecordValue} value @param {NativeTypes.RecordValue} node */
export function projectFunction(exporter, value, node) {
  const shared = object(value.shared, 'native function details');
  if (exporter.types.FunctionType.isPartiallyEvaluated(value)) fail('native function type is incomplete');
  node.name = string(shared.fullName, 'native function full name');
  node.details_flags = integer(shared.flags, 'native function flags');
  node.declaration = exporter.source.declaration(shared.declaration);
  node.parameters = array(shared.parameters, 'native function parameters').map((argument, index) => parameter(exporter, argument, index, value));
  node.type_parameters = array(shared.typeParams, 'native function type parameters').map((type) => exporter.type(type));
  node.gradual_callable = boolean(exporter.types.FunctionType.isGradualCallableForm(value), 'native gradual callable flag');
  exporter.context.program.evaluator.inferReturnTypeIfNecessary(value);
  if (shared.inferredReturnType !== undefined && object(shared.inferredReturnType, 'native inferred return').isIncomplete) fail('native inferred return type is incomplete');
  const returns = exporter.types.FunctionType.getEffectiveReturnType(value);
  if (returns === undefined) fail('native callable return type is missing');
  node.return_type = exporter.type(returns);
  node.declared_return = exporter.types.FunctionType.getEffectiveReturnType(value, false) !== undefined;
}
/** @param {NativeTypes.Projector} exporter @param {NativeTypes.RecordValue} value @param {NativeTypes.RecordValue} node */
export function projectOverloaded(exporter, value, node) {
  const overloads = array(exporter.types.OverloadedType.getOverloads(value), 'native overloads').map((type) => exporter.type(type));
  if (overloads.length === 0) fail('native overload set is empty');
  node.overloads = overloads;
  const implementation = exporter.types.OverloadedType.getImplementation(value);
  node.implementation = implementation === undefined ? null : exporter.type(implementation);
}
