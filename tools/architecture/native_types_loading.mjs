// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { readFileSync, realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { fail, object, string, hash } from './native_types_values.mjs';
export const VERSION = '1.1.414';
/** @type {Record<string, string>} */
export const HASHES = {
  'package.json': '5812294e77125cd0221c5268550df318d8471c26252ff4037c74076831475c3b',
  'dist/pyright.js': '15e1bd7955a81f9e5210dc44da50a9baa7837780a8ac8ce14435dac325fccb50',
  'dist/pyright-internal.js': '41fb260ad72f2a16c5657e1f2fe837104d7529255d0fcd955f48432b276e7cae',
  'dist/vendor.js': '1c691bf9e3fa954dec751ace203beb5591b46a73e3848af5d1ee011d62540798',
};
/** @type {Record<number, string>} */
const EXTERNAL = {
  8240: 'fsevents', 5317: 'child_process', 6982: 'crypto', 4434: 'events',
  9896: 'fs', 857: 'os', 6928: 'path', 932: 'process', 3785: 'readline',
  2203: 'stream', 2018: 'tty', 7016: 'url', 9023: 'util', 1493: 'v8',
  8167: 'worker_threads', 3106: 'zlib',
};

/** @param {unknown} path @returns {string} */
export function pinnedPackage(path) {
  const root = realpathSync(string(path, 'native package path'));
  const metadata = object(JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')), 'native package metadata');
  if (metadata.version !== VERSION) fail('native package version differs from locked Pyright 1.1.414');
  for (const [file, expected] of Object.entries(HASHES)) {
    if (hash(join(root, file)) !== expected) fail(`native package artifact changed: ${file}`);
  }
  return root;
}

/** @param {string} root @returns {NativeTypes.Loader} */
export function loader(root) {
  const require = createRequire(join(root, 'dist/pyright.js'));
  const modules = { ...object(object(require('./vendor.js'), 'vendor bundle').modules, 'vendor modules'), ...object(object(require('./pyright-internal.js'), 'native bundle').modules, 'native modules') };
  /** @type {Map<number, NativeTypes.ModuleValue>} */
  const cache = new Map();
  /** @param {number} id @returns {unknown} */
  function native(id) {
    const cached = cache.get(id);
    if (cached) return cached.exports;
    const external = EXTERNAL[id];
    if (external !== undefined) return require(external);
    const factory = modules[id];
    if (typeof factory !== 'function') fail(`native compiled module is missing: ${id}`);
    const module = { exports: {} };
    cache.set(id, module);
    /** @type {NativeTypes.ForeignFunction} */ (factory).call(module.exports, module, module.exports, native);
    return module.exports;
  }
  /** @type {NativeTypes.Loader['d']} */
  native.d = (target, getters, values) => {
    for (const [key, get] of Object.entries(getters || {})) {
      if (!Object.hasOwn(target, key)) Object.defineProperty(target, key, { enumerable: true, get });
    }
    for (const [key, value] of Object.entries(values || {})) {
      if (!Object.hasOwn(target, key)) Object.defineProperty(target, key, { enumerable: true, value });
    }
  };
  /** @type {NativeTypes.Loader['o']} */
  native.o = (value, key) => Object.hasOwn(value, key);
  /** @type {NativeTypes.Loader['r']} */
  native.r = (value) => {
    Object.defineProperty(value, Symbol.toStringTag, { value: 'Module' });
    Object.defineProperty(value, '__esModule', { value: true });
  };
  /** @type {NativeTypes.Loader['nmd']} */
  native.nmd = (module) => { module.paths = []; module.children ||= []; return module; };
  globalThis.__rootDirectory = join(root, 'dist');
  return native;
}
