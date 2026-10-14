// @ts-check
/// <reference path="./native_calls_api.d.ts" />
import { createHash } from 'node:crypto';
import { realpathSync } from 'node:fs';
import { fail, object, array, string, hash, inside } from './native_types_values.mjs';
import { VERSION, HASHES, pinnedPackage, loader } from './native_types_loading.mjs';
import { setup } from './native_types_context.mjs';
import { NativeSources } from './native_types_sources.mjs';
import { Projector } from './native_types_projector.mjs';
import { callsInSource } from './native_calls_projection.mjs';

/** @param {unknown} value @param {string} requestText @returns {NativeTypes.RecordValue} */
export function inspect(value, requestText) {
  const request = object(value, 'native call request');
  if (request.schema !== 1 || Number(process.versions.node.split('.')[0]) < 22) fail('unsupported native call schema or Node version');
  const packageRoot = pinnedPackage(request.package), root = realpathSync(string(request.root, 'native call root'));
  /** @type {Map<string,string>} */
  const sources = new Map();
  for (const value of array(request.sources, 'native source discovery')) {
    const source = object(value, 'native discovered source'), path = realpathSync(string(source.path, 'native source path'));
    if (!inside(root, path) || sources.has(path) || hash(path) !== source.sha256) fail('native call source escapes scope, duplicates or changed');
    sources.set(path, string(source.sha256, 'native source hash'));
  }
  if (!sources.size) fail('native call source discovery is empty');
  const artifacts = array(request.bridge_sources, 'native call bridge sources').map((value) => object(value, 'native call bridge source'));
  const verifyArtifacts = () => { for (const artifact of artifacts) if (hash(string(artifact.path, 'native bridge source path')) !== artifact.sha256) fail('native call bridge source changed'); };
  verifyArtifacts();
  const settings = object(request.settings, 'native call settings');
  const context = setup(root, { package: packageRoot, extra_paths: array(settings.extra_paths, 'native extra paths').map((value) => realpathSync(string(value, 'native extra path'))), stub_path: settings.stub_path === null ? null : realpathSync(string(settings.stub_path, 'native stub path')) }, loader(packageRoot));
  try {
    context.program.setTrackedFiles([...sources.keys()].map((path) => context.Uri.file(path, context.services)));
    const deadline = Date.now() + 60000;
    while (context.program.analyze({ openFilesTimeInMs: 25, noOpenFilesTimeInMs: 25 })) if (Date.now() > deadline) fail('native call analysis timed out');
    const source = new NativeSources(context, root, sources), projector = new Projector(context, source);
    for (const info of context.program.getSourceFileInfoList()) source.file(info.uri.getFilePath());
    const files = [...sources].map(([path, sha256]) => ({ path, sha256, calls: callsInSource(context, projector, path) }));
    const calls = files.flatMap((file) => file.calls);
    if (!calls.length) fail('native explicit call scope is empty');
    source.verify(); pinnedPackage(packageRoot); verifyArtifacts();
    const sites = calls.flatMap((call) => [call.callee_type, call.receiver_type, call.selected_signature, call.result_type, ...call.arguments.map((arg) => arg.type)].filter((type) => type !== null).map((type) => ({ path: call.location.path, line: call.location.line, column: call.location.column, type, declarations: [] })));
    return { schema: 1, version: VERSION, artifacts: HASHES, node: process.versions.node, python: '3.10', request_sha256: createHash('sha256').update(requestText).digest('hex'), bridge_sources: artifacts, files, sites, types: projector.nodes, inputs: [...source.files].map(([path, sha256]) => ({ path, sha256 })) };
  } finally { context.program.dispose(); context.services.dispose(); }
}
