// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { realpathSync } from 'node:fs';
import { fail, object, string, integer, hash, inside, invoke } from './native_types_values.mjs';
export class NativeSources {
  /** @param {NativeTypes.Context} context @param {string} root @param {Map<string,string>} sources */
  constructor(context, root, sources) {
    this.context = context;
    this.root = root;
    this.sources = sources;
    /** @type {Map<string,string>} */
    this.files = new Map();
  }
  /** @param {string} path */
  file(path) {
    path = realpathSync(path);
    if (inside(this.root, path) && !this.sources.has(path)) fail(`native type reached undiscovered first-party source: ${path}`);
    const digest = hash(path);
    const parsed = this.context.readInputs.get(path);
    if (parsed !== undefined && parsed !== digest) fail(`source changed after native parsing: ${path}`);
    if (this.files.has(path) && this.files.get(path) !== digest) fail(`source changed during native type analysis: ${path}`);
    this.files.set(path, digest);
    return { path, sha256: digest };
  }
  /** @param {unknown} value */
  declaration(value) {
    if (value === undefined) return null;
    const item = object(value, 'native declaration');
    const file = this.file(string(invoke(item.uri, 'getFilePath', []), 'native declaration path'));
    const range = object(item.range, 'native declaration range');
    const start = object(range.start, 'native declaration start');
    const end = object(range.end, 'native declaration end');
    return {
      ...file, kind: integer(item.type, 'native declaration kind'),
      line: integer(start.line, 'native declaration line') + 1,
      column: integer(start.character, 'native declaration column'),
      end_line: integer(end.line, 'native declaration end line') + 1,
      end_column: integer(end.character, 'native declaration end column'),
    };
  }
  verify() {
    for (const [path, digest] of this.files) {
      if (hash(path) !== digest) fail(`source changed during native type analysis: ${path}`);
    }
    for (const [path, digest] of this.sources) {
      if (hash(path) !== digest) fail(`discovery source changed during native type analysis: ${path}`);
    }
    for (const [path, digest] of this.context.readInputs) {
      if (hash(path) !== digest) fail(`source changed after native reading: ${path}`);
      this.files.set(path, digest);
    }
  }
}
