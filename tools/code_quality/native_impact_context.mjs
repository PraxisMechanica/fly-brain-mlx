// @ts-check
/// <reference path="../architecture/native_types_node.d.ts" />
import {readFileSync, realpathSync} from 'node:fs';
import {fail, object, array, string, hash, inside} from '../architecture/native_types_values.mjs';
import {loadCompiler, verifyCompiler} from '../architecture/native_sources_compiler.mjs';

/** @param {unknown} value @param {string} root @returns {Map<string,string>} */
function inputs(value, root) {
  return new Map(Object.entries(object(value, 'native inputs')).map(([name, value]) => {
    const path = realpathSync(name);
    const digest = string(value, 'native input digest');
    if (path !== name || !inside(root, path) || hash(path) !== digest) fail(`native input changed or escapes scope: ${name}`);
    return [path, digest];
  }));
}

/** @param {string[]} failures */
function rejectFailures(failures) { if (failures.length) fail(failures.join('; ')); }

/** @typedef {{ts: typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js'), parsed: import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').ParsedCommandLine, host: import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').CompilerHost, builder: import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').SemanticDiagnosticsBuilderProgram, program: import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').Program, flags: string[], sources: Map<string,string>, configuration: Map<string,string>, reads: Map<string,string>, readFailures: string[], packageRoot: string}} Context */
/** @param {unknown} value @returns {Context} */
export function createContext(value) {
  const request = object(value, 'native dependency request');
  if (request.schema !== 1) fail('native dependency schema changed');
  const root = realpathSync(string(request.root, 'native root'));
  const packageRoot = realpathSync(string(request.package, 'compiler package'));
  const dependencyRoot = realpathSync(string(request.dependencies, 'dependency root'));
  const ts = loadCompiler(packageRoot);
  const flags = array(request.flags, 'compiler flags').map(value => string(value, 'compiler flag'));
  const parsed = ts.parseCommandLine(flags);
  if (parsed.errors.length + parsed.fileNames.length) fail('native compiler flags are invalid');
  const sources = inputs(request.sources, root);
  const configuration = inputs(request.configuration, root);
  if (!sources.size) fail('native dependency source scope is empty');
  const discovered = new Set([...sources.keys(), ...configuration.keys()]);
  const host = ts.createIncrementalCompilerHost(parsed.options);
  const read = host.readFile.bind(host);
  /** @type {Map<string,string>} */
  const reads = new Map();
  /** @type {string[]} */
  const readFailures = [];
  /** @param {string} message @returns {never} */
  function rejectRead(message) { readFailures.push(message); fail(message); }
  host.readFile = (name) => {
    const text = read(name);
    if (text !== undefined) {
      const path = realpathSync(name);
      if (!discovered.has(path) && !inside(dependencyRoot, path)) rejectRead(`native compiler reached undiscovered input: ${path}`);
      const digest = hash(path);
      if (text !== readFileSync(path, 'utf8').replace(/^\uFEFF/, '') || (reads.has(path) && reads.get(path) !== digest)) rejectRead(`native compiler text changed: ${path}`);
      reads.set(path, digest);
    }
    return text;
  };
  const builder = ts.createSemanticDiagnosticsBuilderProgram([...sources.keys()], parsed.options, host);
  rejectFailures(readFailures);
  const program = builder.getProgram();
  const diagnostics = [...program.getOptionsDiagnostics(), ...program.getSyntacticDiagnostics(), ...program.getGlobalDiagnostics()];
  const diagnostic = diagnostics[0];
  if (diagnostic) fail(`native parser rejected: ${diagnostic.file?.fileName || '<context>'}: TS${diagnostic.code}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, ' ')}`);
  return {ts, parsed, host, builder, program, flags, sources, configuration, reads, readFailures, packageRoot};
}

/** @param {Context} context */
export function verifyInputs(context) {
  const {reads, sources, configuration, packageRoot} = context;
  rejectFailures(context.readFailures);
  for (const [path, digest] of [...reads, ...sources, ...configuration]) {
    if (hash(path) !== digest) fail(`native compiler input changed after parsing: ${path}`);
  }
  verifyCompiler(packageRoot);
}
