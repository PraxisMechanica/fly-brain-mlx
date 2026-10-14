// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { readFileSync, realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { fail, object, array, string, hash, inside } from './native_types_values.mjs';

export const VERSION = '5.9.3';
export const ARTIFACTS = {
  'package.json': '822ef7ca6452205657b6288b066481ecf508bfbf43455d715cf7d3ec457561e6',
  'lib/typescript.js': '3ae902c92cc44dace175c0e69e13a4b0899f6983c6121d76b9ab8dd5795e7675',
  'lib/typescript.d.ts': 'e134052a6b1ded61693b4037f615dc72f14e2881e79c1ddbff6c514c8a516b05',
};

/** @typedef {{ts: typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js'), program: import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Program, sources: Map<string,string>, configuration: Map<string,string>, inputs: Map<string,string>, packageRoot: string}} Context */
/** @param {unknown} value @returns {Context} */
export function createContext(value) {
  const request = object(value, 'native source request');
  if (request.schema !== 1) fail('native source request schema changed');
  const root = realpathSync(string(request.root, 'native source root'));
  const packageRoot = realpathSync(string(request.package, 'TypeScript package'));
  for (const [path, digest] of Object.entries(ARTIFACTS)) {
    if (hash(join(packageRoot, path)) !== digest) fail(`TypeScript artifact changed: ${path}`);
  }
  const require = createRequire(join(packageRoot, 'package.json'));
  const ts = /** @type {typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js')} */ (require(join(packageRoot, 'lib/typescript.js')));
  if (ts.version !== VERSION) fail('native TypeScript version changed');
  /** @type {Map<string,string>} */
  const sources = new Map();
  for (const entry of array(request.sources, 'native sources')) {
    const item = object(entry, 'native source');
    const path = realpathSync(string(item.path, 'native source path'));
    if (!inside(root, path) || sources.has(path)) fail('native source escapes discovery or is duplicated');
    if (hash(path) !== item.sha256) fail(`native source changed: ${path}`);
    sources.set(path, string(item.sha256, 'native source digest'));
  }
  if (!sources.size) fail('native source scope is empty');
  const configuration = new Map(array(request.configuration, 'native configuration inputs').map((entry) => {
    const item = object(entry, 'native configuration input');
    const path = realpathSync(string(item.path, 'native configuration path'));
    const digest = string(item.sha256, 'native configuration hash');
    if (!inside(root, path) || hash(path) !== digest) fail('native configuration input escapes scope or changed');
    return [path, digest];
  }));
  const options = {allowJs: true, checkJs: true, noEmit: true, strict: true,
    noUncheckedIndexedAccess: true, exactOptionalPropertyTypes: true,
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.NodeNext,
    moduleResolution: ts.ModuleResolutionKind.NodeNext, types: []};
  const host = ts.createCompilerHost(options);
  const read = host.readFile.bind(host);
  /** @type {Map<string,string>} */
  const inputs = new Map();
  /** @type {string[]} */
  const readFailures = [];
  host.readFile = (file) => {
    const text = read(file);
    if (text !== undefined) {
      const path = realpathSync(file);
      if (inside(root, path) && !sources.has(path) && !configuration.has(path)) {
        const message = `native parser reached undiscovered source: ${path}`;
        readFailures.push(message);
        fail(message);
      }
      const digest = hash(path);
      const decoded = readFileSync(path, 'utf8').replace(/^\uFEFF/, '');
      if (text !== decoded) fail(`native parser text differs from hashed UTF-8 input: ${path}`);
      if (hash(path) !== digest) fail(`native source changed during read: ${path}`);
      if (inputs.has(path) && inputs.get(path) !== digest) fail(`native source changed between reads: ${path}`);
      inputs.set(path, digest);
    }
    return text;
  };
  const program = ts.createProgram([...sources.keys()], options, host);
  if (readFailures.length) fail(readFailures.join('; '));
  const diagnostics = ts.getPreEmitDiagnostics(program);
  if (diagnostics.length) {
    const diagnostic = diagnostics[0];
    if (!diagnostic) fail('native diagnostic is missing');
    const path = diagnostic.file?.fileName || '<configuration>';
    const line = diagnostic.file?.getLineAndCharacterOfPosition(diagnostic.start || 0).line;
    fail(`native source rejected: ${path}:${line === undefined ? 1 : line + 1}: TS${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, ' ')}`);
  }
  return {ts, program, sources, configuration, inputs, packageRoot};
}

/** @param {Context} context */
export function verifyInputs(context) {
  const {inputs, sources, configuration, packageRoot} = context;
  for (const [path, digest] of inputs) if (hash(path) !== digest) fail(`native source changed after parsing: ${path}`);
  for (const [path, digest] of [...sources, ...configuration]) if (inputs.get(path) !== digest) fail(`native source was not parsed: ${path}`);
  for (const [path, digest] of Object.entries(ARTIFACTS)) if (hash(join(packageRoot, path)) !== digest) fail(`TypeScript artifact changed: ${path}`);
}
