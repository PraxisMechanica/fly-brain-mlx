// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { createHash } from 'node:crypto';
import { realpathSync } from 'node:fs';
import { join } from 'node:path';
import { fail, object, invoke, construct } from './native_types_values.mjs';
/** @param {string} root @param {NativeTypes.Settings} settings @param {NativeTypes.Loader} native @returns {NativeTypes.Context} */
export function setup(root, settings, native) {
  const detector = { isCaseSensitive: () => true };
  const console = construct(object(native(2674), 'console module').NullConsole, []);
  const fs = /** @type {NativeTypes.NativeFs} */ (invoke(native(4788), 'createFromRealFileSystem', [detector, console]));
  /** @type {Map<string, string>} */
  const readInputs = new Map();
  const read = fs.readFileSync.bind(fs);
  fs.readFileSync = (uri, encoding) => {
    const value = read(uri, encoding);
    const path = realpathSync(uri.getFilePath());
    const digest = createHash('sha256').update(value).digest('hex');
    if (readInputs.has(path) && readInputs.get(path) !== digest) fail(`source changed between native reads: ${path}`);
    readInputs.set(path, digest);
    return value;
  };
  const services = /** @type {NativeTypes.Services} */ (invoke(native(1795), 'createServiceProvider', [fs, detector, console]));
  const Uri = /** @type {NativeTypes.Context['Uri']} */ (object(native(9424), 'URI module').Uri);
  const config = /** @type {NativeTypes.Config} */ (construct(object(native(9963), 'configuration module').ConfigOptions, [Uri.file(root, services)]));
  config.defaultPythonVersion = object(native(4825), 'Python version module').pythonVersion3_10;
  config.diagnosticRuleSet = invoke(native(9963), 'getStrictDiagnosticRuleSet', []);
  config.typeshedPath = Uri.file(join(settings.package, 'dist/typeshed-fallback'), services);
  config.defaultExtraPaths = settings.extra_paths.map((path) => Uri.file(path, services));
  if (settings.stub_path !== null) config.stubPath = Uri.file(settings.stub_path, services);
  const host = construct(object(native(210), 'host module').LimitedAccessHost, []);
  const imports = construct(object(native(9005), 'import module').ImportResolver, [services, config, host]);
  const program = /** @type {NativeTypes.Program} */ (construct(object(native(2752), 'program module').Program, [imports, config, services]));
  return { program, services, config, Uri, native, readInputs };
}
