// @ts-check
/// <reference path="./native_python_context_api.d.ts" />
import { existsSync, realpathSync } from 'node:fs';
import { verifySourceImports } from './native_python_imports.mjs';
import { array, boolean, construct, fail, hash, integer, invoke, object, string } from './native_types_values.mjs';

/** @param {unknown} value @returns {string} */
export function uri(value) { return string(invoke(value, 'getFilePath', []), 'native URI'); }

/** @param {NativePython.Service} service @param {NativeTypes.RecordValue} config @param {NativePython.FileSystem} fs
 * @param {Map<string,string>} required @param {NativeTypes.Loader} native @param {NativeTypes.RecordValue} console
 * @returns {NativePython.ObservationSnapshot} */
export function observe(service, config, fs, required, native, console) {
  const enumeration = service._sourceEnumerator.enumerate(0);
  if (!(enumeration.matches instanceof Map) || !boolean(enumeration.isComplete, 'enumeration completion') || !boolean(invoke(service, 'enumerateSourceFiles', [0]), 'service enumeration completion')) fail('native source enumeration is incomplete');
  const tracked = [...enumeration.matches.values()], trackedPaths = tracked.map((entry) => realpathSync(uri(entry)));
  const stubPath = uri(config.stubPath);
  /** @type {string[]} */ let stubs = [];
  if (existsSync(stubPath)) {
    const specification = invoke(native(2091), 'getFileSpec', [config.stubPath, '.']);
    const enumerator = /** @type {NativePython.SourceEnumerator} */ (construct(object(native(5346), 'native source enumeration').SourceEnumerator, [[specification], config.exclude, false, fs, console]));
    const result = enumerator.enumerate(0);
    if (!boolean(result.isComplete, 'stub enumeration completion')) fail('native stub enumeration is incomplete');
    stubs = [...result.matches.values()].map((entry) => realpathSync(uri(entry)));
  }
  const selected = new Set([...trackedPaths, ...stubs]);
  if (!tracked.length || selected.size !== required.size || [...selected].some((path) => !required.has(path))) fail('native enumeration differs from independent discovery');
  const resolver = invoke(service, 'getImportResolver', []), program = service.test_program;
  /** @param {NativeTypes.Uri} path */
  const environment = (path) => object(invoke(config, 'findExecEnvironment', [path]), 'execution environment');
  /** @param {NativeTypes.Uri} path @returns {string} */
  const moduleName = (path) => string(object(invoke(resolver, 'getModuleNameForImport', [path, environment(path)]), 'native module identity').moduleName, 'native module name');
  const packages = tracked.filter((entry) => uri(entry).endsWith('/__init__.py')).map(moduleName);
  for (const path of tracked) {
    if (!invoke(program, 'getBoundSourceFile', [path]) || array(invoke(program, 'getParseDiagnostics', [path]), 'parse diagnostics').length) fail(`native source cannot be bound: ${uri(path)}`);
  }
  const loadedSources = () => Array.from(program.getSourceFileInfoList(), (info) => {
    const original = fs.getOriginalUri(info.uri), path = realpathSync(uri(original)), module = moduleName(info.uri);
    const typeshed = boolean(info.isTypeshedFile, 'typeshed origin'), third_party = boolean(info.isThirdPartyImport, 'third-party origin');
    if (!required.has(path) && (!typeshed && !third_party || packages.some((name) => module === name || module.startsWith(name + '.')))) fail(`foreign or unregistered first-party resolution: ${module}: ${path}`);
    verifySourceImports(native, program, path, info.sourceFile, trackedPaths.includes(path));
    return {path, sha256: hash(path), raw_uri: uri(info.uri), module, mapped: boolean(fs.isMappedUri(info.uri), 'native URI mapping'), typeshed, third_party,
      py_typed: boolean(info.isThirdPartyPyTypedPresent, 'py.typed origin')};
  });
  const loaded = loadedSources();
  const environments = tracked.map((path) => {
    const env = environment(path), version = object(env.pythonVersion, 'native Python version');
    return {root: typeof env.root === 'string' ? env.root : uri(env.root), python: `${integer(version.major, 'Python major')}.${integer(version.minor, 'Python minor')}`, platform: string(env.pythonPlatform, 'native platform'),
      extra_paths: array(env.extraPaths, 'extra paths').map(uri), import_roots: array(invoke(resolver, 'getImportRoots', [env, true]), 'import roots').map(uri)};
  });
  return {tracked: trackedPaths, stub_inputs: stubs, stub_path: stubPath, loaded, environments, refreshLoaded: loadedSources};
}
