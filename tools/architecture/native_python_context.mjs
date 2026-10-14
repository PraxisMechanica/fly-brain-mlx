// @ts-check
/// <reference path="./native_python_context_api.d.ts" />
import { createHash } from 'node:crypto';
import { readFileSync, realpathSync } from 'node:fs';
import { join } from 'node:path';
import { observe, uri } from './native_python_observation.mjs';
import { captureReads } from './native_types_context.mjs';
import { pinnedPackage, loader, VERSION, HASHES } from './native_types_loading.mjs';
import { array, construct, fail, hash, inside, integer, invoke, object, string } from './native_types_values.mjs';

/** @param {unknown} value @returns {string|null} */
function optionalUri(value) { return value === undefined ? null : uri(value); }
/** @param {unknown} value @returns {NativeTypes.FileInput[]} */
function inputs(value) {
  return array(value, 'input manifest').map((entry) => {
    const item = object(entry, 'input'), path = realpathSync(string(item.path, 'input path')), sha256 = string(item.sha256, 'input hash');
    if (hash(path) !== sha256) fail(`context input changed: ${path}`);
    return {path, sha256};
  });
}
/** @param {unknown} value @returns {[string,string][]} */
function specs(value) {
  return array(value, 'native file specs').map((entry) => {
    const item = object(entry, 'native file spec');
    return [uri(item.wildcardRoot), string(object(item.regExp, 'native regexp').source, 'native regexp source')];
  });
}
/** @param {unknown} request @param {string} text @returns {Promise<NativePython.Report>} */
export async function inspect(request, text) {
  const data = object(request, 'context request');
  if (data.schema !== 1 || Number(process.versions.node.split('.')[0]) < 22) fail('unsupported context schema or Node version');
  const root = realpathSync(string(data.root, 'context root')), packageRoot = pinnedPackage(data.package), native = loader(packageRoot);
  const sources = inputs(data.sources), configuration = inputs(data.configuration), bridge = inputs(data.bridge_sources);
  const required = new Map(sources.map((entry) => [entry.path, entry.sha256]));
  if (!required.size || required.size !== sources.length || [...required.keys()].some((path) => !inside(root, path))) fail('context source scope is empty, duplicated or escaping');
  const console = object(construct(object(native(2674), 'native console').NullConsole, []), 'console');
  /** @type {string[]} */ const errors = [];
  console.error = /** @param {unknown} message */ (message) => { errors.push(String(message)); };
  const temporary = construct(object(native(4788), 'native filesystem').RealTempFile, [string(data.temporary, 'context temporary directory')]);
  const realFS = /** @type {NativeTypes.NativeFs} */ (invoke(native(4788), 'createFromRealFileSystem', [temporary, console]));
  const reads = captureReads(realFS);
  const fs = /** @type {NativePython.FileSystem} */ (construct(object(native(3761), 'native overlay filesystem').PyrightFileSystem, [realFS]));
  const services = /** @type {NativeTypes.Services} */ (invoke(native(1795), 'createServiceProvider', [fs, console, temporary]));
  const service = /** @type {NativePython.Service} */ (construct(object(native(5987), 'native analyzer service').AnalyzerService, ['context-observer', services, {
    console, hostFactory: () => construct(object(native(210), 'native host').FullAccessHost, [services]), shouldRunAnalysis: () => false,
  }]));
  try {
    await invoke(native(6074), 'ensureTomlModuleLoaded', []);
    const options = object(construct(object(native(5288), 'native options').CommandLineOptions, [root, false]), 'options');
    object(options.configSettings, 'native config settings').autoSearchPaths = true;
    invoke(service, 'setOptions', [options]);
    const hostKind = integer(object(object(service.backgroundAnalysisProgram, 'native background program').host, 'native host').kind, 'native host kind');
    if (hostKind !== 0) fail('canonical native full host differs');
    const config = object(invoke(service, 'getConfigOptions', []), 'native config'), primary = optionalUri(config.configFileSource);
    if (errors.length || primary === null || !configuration.some((entry) => entry.path === realpathSync(primary)) || config.effectiveTypeCheckingMode !== 'strict' || JSON.stringify(config.diagnosticRuleSet) !== JSON.stringify(invoke(native(9963), 'getStrictDiagnosticRuleSet', []))) fail(`native configuration failed, fell back or weakened: ${errors.join('; ')}`);
    if (realpathSync(uri(config.projectRoot)) !== root || array(service._extendedConfigFileUris, 'native configuration chain').some((entry) => !configuration.some((input) => input.path === realpathSync(uri(entry))))) fail('native configuration chain differs from declared inputs');
    const {tracked: trackedPaths, stub_inputs: stubs, stub_path: stubPath, loaded, environments} = observe(service, config, fs, required, native, console);
    for (const entry of [...sources, ...configuration, ...bridge, ...loaded, ...[...reads].map(([path, sha256]) => ({path, sha256}))]) if (hash(entry.path) !== entry.sha256) fail(`context input changed after observation: ${entry.path}`);
    pinnedPackage(packageRoot);
    return {schema: 1, version: VERSION, node_version: process.versions.node, host_kind: hostKind, request_sha256: createHash('sha256').update(text).digest('hex'),
      configuration, primary_config: realpathSync(primary), diagnostic_rules: Object.entries(object(config.diagnosticRuleSet, 'native diagnostic rules')).map(([name, value]) => [name, typeof value === 'boolean' ? value : string(value, 'native diagnostic severity')]),
      include: specs(config.include), exclude: specs(config.exclude), ignore: specs(config.ignore), environments,
      venv: config.venv === undefined ? null : string(config.venv, 'native venv'), venv_path: optionalUri(config.venvPath), stub_path: stubPath, configured_typeshed: optionalUri(config.typeshedPath),
      tracked: trackedPaths, stub_inputs: stubs, sources, loaded, read_inputs: [...reads].map(([path, sha256]) => ({path, sha256})), bridge_sources: bridge,
      compiler_artifacts: Object.entries(HASHES).map(([path, sha256]) => ({path: join(packageRoot, path), sha256})),
      missing: ['declarations', 'types', 'calls', 'alias_resolution', 'effects', 'control_flow', 'runtime_targets', 'runtime_environment_equivalence']};
  } finally { invoke(service, 'dispose', []); services.dispose(); invoke(temporary, 'dispose', []); }
}
try {
  const text = readFileSync(0, 'utf8');
  process.stdout.write(JSON.stringify(await inspect(JSON.parse(text), text)) + '\n');
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({error: message.startsWith('COV002:') ? message : `COV002: native Python context failed: ${message}`}) + '\n');
  process.exitCode = 2;
}
