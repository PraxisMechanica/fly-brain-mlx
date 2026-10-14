// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { readFileSync, realpathSync } from 'node:fs';
import { fail, object, array, string, hash, inside } from './native_types_values.mjs';
import { VERSION, HASHES, pinnedPackage, loader } from './native_types_loading.mjs';
import { setup } from './native_types_context.mjs';
import { NativeSources } from './native_types_sources.mjs';
import { Projector } from './native_types_projector.mjs';
import { query } from './native_types_query.mjs';
/** @param {unknown} value @returns {NativeTypes.RecordValue} */
function inspect(value) {
  const request = object(value, 'native request');
  if (request.schema !== 1) fail('unsupported native request schema');
  if (Number(process.versions.node.split('.')[0]) < 22) fail('native bridge requires Node.js 22 or newer');
  const packageRoot = pinnedPackage(request.package);
  const root = realpathSync(string(request.root, 'native workspace'));
  /** @type {Map<string, string>} */
  const sources = new Map();
  for (const value of array(request.sources, 'native discovery')) {
    const item = object(value, 'native discovery item');
    const path = realpathSync(string(item.path, 'native discovery path'));
    if (!inside(root, path) || sources.has(path)) fail('native discovery path escapes workspace or is duplicated');
    if (hash(path) !== item.sha256) fail(`native discovery source changed: ${path}`);
    sources.set(path, string(item.sha256, 'native discovery hash'));
  }
  if (sources.size === 0) fail('native discovery scope is empty');
  const queries = array(request.queries, 'native type queries');
  if (queries.length === 0) fail('native type query scope is empty');
  const settings = object(request.settings, 'native settings');
  const extra_paths = array(settings.extra_paths, 'native extra paths').map((path) => realpathSync(string(path, 'native extra path')));
  const stub_path = settings.stub_path === null ? null : realpathSync(string(settings.stub_path, 'native stub path'));
  const native = loader(packageRoot);
  const context = setup(root, { package: packageRoot, extra_paths, stub_path }, native);
  try {
    context.program.setTrackedFiles([...sources.keys()].map((path) => context.Uri.file(path, context.services)));
    const deadline = Date.now() + 60000;
    while (context.program.analyze({ openFilesTimeInMs: 25, noOpenFilesTimeInMs: 25 })) {
      if (Date.now() > deadline) fail('native type analysis timed out');
    }
    const source = new NativeSources(context, root, sources);
    const projector = new Projector(context, source);
    for (const info of context.program.getSourceFileInfoList()) {
      const path = info.uri.getFilePath();
      if (path) source.file(path);
      if (sources.has(realpathSync(path)) && context.program.getParseDiagnostics(info.uri)?.length) fail(`native discovered source parse failed: ${path}`);
    }
    const sites = queries.map((item) => query(context, sources, projector, object(item, 'native type query')));
    source.verify();
    pinnedPackage(packageRoot);
    return { schema: 1, version: VERSION, artifacts: HASHES, node: process.versions.node, python: '3.10', sites, types: projector.nodes, inputs: [...source.files].map(([path, sha256]) => ({ path, sha256 })) };
  } finally { context.program.dispose(); context.services.dispose(); }
}

try {
  process.stdout.write(JSON.stringify(inspect(JSON.parse(readFileSync(0, 'utf8')))) + '\n');
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({ error: message.startsWith('COV002:') ? message : `COV002: native evaluator failed: ${message}` }) + '\n');
  process.exitCode = 2;
}
