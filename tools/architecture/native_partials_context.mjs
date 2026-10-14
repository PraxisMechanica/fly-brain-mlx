// @ts-check
/// <reference path="./native_partials_api.d.ts" />
import { createHash } from 'node:crypto';
import { realpathSync } from 'node:fs';
import { fail, object, array, string, hash, inside } from './native_types_values.mjs';
import { VERSION, HASHES, pinnedPackage, loader } from './native_types_loading.mjs';
import { setup } from './native_types_context.mjs';
import { NativeSources } from './native_types_sources.mjs';
import { Projector } from './native_types_projector.mjs';
import { partialsInSource } from './native_partials_projection.mjs';
/** @param {unknown} value @param {string} requestText @returns {NativeTypes.RecordValue} */
export function inspect(value, requestText) {
  const request = object(value, 'native partial request');
  if (request.schema !== 1 || Number(process.versions.node.split('.')[0]) < 22) fail('unsupported native partial schema or Node version');
  const packageRoot = pinnedPackage(request.package), root = realpathSync(string(request.root, 'native partial root'));
  /** @type {Map<string,string>} */
  const sources = new Map();
  for (const entry of array(request.sources, 'native partial source discovery')) {
    const source = object(entry, 'native partial source'), path = realpathSync(string(source.path, 'native partial path'));
    if (!inside(root, path) || sources.has(path) || hash(path) !== source.sha256) fail('native partial source escapes scope, duplicates or changed');
    sources.set(path, string(source.sha256, 'native partial source hash'));
  }
  if (!sources.size) fail('native partial source discovery is empty');
  const artifacts = array(request.bridge_sources, 'native partial bridge sources').map((entry) => object(entry, 'native partial bridge source'));
  const verifyArtifacts = () => { for (const artifact of artifacts) if (hash(string(artifact.path, 'native partial artifact path')) !== artifact.sha256) fail('native partial bridge source changed'); };
  verifyArtifacts();
  const settings = object(request.settings, 'native partial settings');
  const context = setup(root, { package: packageRoot, extra_paths: array(settings.extra_paths, 'native partial extra paths').map((path) => realpathSync(string(path, 'native partial extra path'))), stub_path: settings.stub_path === null ? null : realpathSync(string(settings.stub_path, 'native partial stub path')) }, loader(packageRoot));
  try {
    context.program.setTrackedFiles([...sources.keys()].map((path) => context.Uri.file(path, context.services)));
    const deadline = Date.now() + 60000;
    while (context.program.analyze({ openFilesTimeInMs: 25, noOpenFilesTimeInMs: 25 })) if (Date.now() > deadline) fail('native partial analysis timed out');
    const source = new NativeSources(context, root, sources), projector = new Projector(context, source);
    for (const info of context.program.getSourceFileInfoList()) source.file(info.uri.getFilePath());
    const files = [...sources].map(([path, sha256]) => ({ path, sha256, constructions: partialsInSource(context, projector, path, packageRoot) }));
    const constructions = files.flatMap((file) => file.constructions);
    if (!constructions.length) fail('native partial construction scope is empty');
    const sites = constructions.flatMap((value) => [value.callee_type, value.constructor_signature, value.wrapped.type, ...value.captures.map((capture) => capture.expression.type), value.result_type, value.residual_signature].map((type) => ({ path: value.location.path, line: value.location.line, column: value.location.column, type, declarations: [] })));
    source.verify(); pinnedPackage(packageRoot); verifyArtifacts();
    return { schema: 1, version: VERSION, artifacts: HASHES, node: process.versions.node, python: '3.10', request_sha256: createHash('sha256').update(requestText).digest('hex'), bridge_sources: artifacts, files, sites, types: projector.nodes, inputs: [...source.files].map(([path, sha256]) => ({ path, sha256 })) };
  } finally { context.program.dispose(); context.services.dispose(); }
}
