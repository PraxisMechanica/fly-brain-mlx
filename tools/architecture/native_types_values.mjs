// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { relative, isAbsolute } from 'node:path';
/** @param {string} message @returns {never} */
export function fail(message) { throw new Error(`COV002: ${message}`); }
/** @param {unknown} value @param {string} label @returns {NativeTypes.RecordValue} */
export function object(value, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) fail(`${label} is not an object`);
  return /** @type {NativeTypes.RecordValue} */ (value);
}
/** @param {unknown} value @param {string} label @returns {unknown[]} */
export function array(value, label) {
  if (!Array.isArray(value)) fail(`${label} is not an array`);
  return value;
}
/** @param {unknown} value @param {string} label @returns {string} */
export function string(value, label) {
  if (typeof value !== 'string') fail(`${label} is not a string`);
  return value;
}
/** @param {unknown} value @param {string} label @returns {number} */
export function integer(value, label) {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0) fail(`${label} is not a nonnegative integer`);
  return value;
}
/** @param {unknown} value @param {string} label @returns {boolean} */
export function boolean(value, label) {
  if (typeof value !== 'boolean') fail(`${label} is not a boolean`);
  return value;
}
/** @param {string} path @returns {string} */
export function hash(path) { return createHash('sha256').update(readFileSync(path)).digest('hex'); }
/** @param {string} root @param {string} path @returns {boolean} */
export function inside(root, path) {
  const suffix = relative(root, path);
  return suffix === '' || (!suffix.startsWith('..') && !isAbsolute(suffix));
}
/** @param {unknown} owner @param {string} name @param {unknown[]} args @returns {unknown} */
export function invoke(owner, name, args) {
  const method = object(owner, 'native API')[name];
  if (typeof method !== 'function') fail(`native API method is missing: ${name}`);
  return /** @type {NativeTypes.ForeignFunction} */ (method).apply(owner, args);
}
/** @template T @param {unknown} value @param {unknown[]} args @returns {T} */
export function construct(value, args) {
  if (typeof value !== 'function') fail('native constructor is missing');
  return new (/** @type {NativeTypes.ForeignConstructor<T>} */ (value))(...args);
}
