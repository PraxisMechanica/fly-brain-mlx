// @ts-check
/// <reference path="./native_types_node.d.ts" />
import {readFileSync} from 'node:fs';
import {createContext,verifyInputs,VERSION,ARTIFACTS} from './native_sources_context.mjs';
import {projectSources} from './native_sources_symbols.mjs';

/** @param {unknown} value */
function inspect(value) {
  const context = createContext(value);
  const files = projectSources(context);
  verifyInputs(context);
  return {schema: 1, version: VERSION, artifacts: ARTIFACTS, files, inputs: [...context.inputs].map(([path, sha256]) => ({path, sha256}))};
}

try {
  process.stdout.write(JSON.stringify(inspect(JSON.parse(readFileSync(0, 'utf8')))) + '\n');
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({error: message.startsWith('COV002:') ? message : `COV002: native source inventory failed: ${message}`}) + '\n');
  process.exitCode = 2;
}
