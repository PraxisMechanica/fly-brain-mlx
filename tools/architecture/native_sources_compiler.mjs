// @ts-check
/// <reference path="./native_types_node.d.ts" />
import { realpathSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { fail, object, string, hash } from './native_types_values.mjs';

export const VERSION = '5.9.3';
export const ARTIFACTS = {
  'package.json': '822ef7ca6452205657b6288b066481ecf508bfbf43455d715cf7d3ec457561e6',
  'lib/typescript.js': '3ae902c92cc44dace175c0e69e13a4b0899f6983c6121d76b9ab8dd5795e7675',
  'lib/typescript.d.ts': 'e134052a6b1ded61693b4037f615dc72f14e2881e79c1ddbff6c514c8a516b05',
};

/** @param {string} packageRoot */
export function verifyCompiler(packageRoot) {
  for (const [path, digest] of Object.entries(ARTIFACTS)) if (hash(join(packageRoot, path)) !== digest) fail(`TypeScript artifact changed: ${path}`);
}

/** @param {string} packageRoot @returns {typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js')} */
export function loadCompiler(packageRoot) {
  verifyCompiler(packageRoot);
  const require = createRequire(join(packageRoot, 'package.json'));
  const ts = /** @type {typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js')} */ (require(join(packageRoot, 'lib/typescript.js')));
  if (ts.version !== VERSION) fail('native TypeScript version changed');
  return ts;
}

/** @param {typeof import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js')} ts @param {string} packageRoot @param {import('../../node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/lib/typescript.js').CompilerOptions} options @returns {Set<string>} */
export function compilerInputPaths(ts, packageRoot, options) {
  const libraryMap = object(ts, 'native compiler namespace').libMap;
  if (!(libraryMap instanceof Map)) fail('native compiler standard-library map is absent');
  const compilerInputs = new Set(Object.keys(ARTIFACTS).map((path) => realpathSync(join(packageRoot, path))));
  for (const name of /** @type {Map<unknown,unknown>} */ (libraryMap).values()) compilerInputs.add(realpathSync(join(packageRoot, 'lib', string(name, 'native compiler standard-library name'))));
  compilerInputs.add(realpathSync(ts.getDefaultLibFilePath(options)));
  return compilerInputs;
}
