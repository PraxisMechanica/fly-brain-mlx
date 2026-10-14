// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { readFileSync, realpathSync } from 'node:fs';
import { fail, object, array, string, hash, inside } from './native_types_values.mjs';
import { loadCompiler, verifyCompiler, compilerInputPaths } from './native_sources_compiler.mjs';
export { VERSION, ARTIFACTS } from './native_sources_compiler.mjs';

/** @typedef {{ts: typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js'), program: import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Program, sources: Map<string,string>, configuration: Map<string,string>, inputs: Map<string,string>, packageRoot: string}} Context */
/** @param {unknown} value @returns {Context} */
export function createContext(value) {
  const request = object(value, 'native source request');
  if (request.schema !== 1) fail('native source request schema changed');
  const root = realpathSync(string(request.root, 'native source root'));
  const packageRoot = realpathSync(string(request.package, 'TypeScript package'));
  const ts = loadCompiler(packageRoot);
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
  const compilerInputs = compilerInputPaths(ts, packageRoot, options);
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
        if (!compilerInputs.has(path)) {
          const message = `native parser reached undiscovered source: ${path}`;
          readFailures.push(message);
          fail(message);
        }
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
  verifyCompiler(packageRoot);
}
