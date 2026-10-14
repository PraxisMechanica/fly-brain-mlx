// @ts-check
/// <reference path="../architecture/native_types_node.d.ts" />
import {readFileSync} from 'node:fs';
import {VERSION} from '../architecture/native_sources_compiler.mjs';
import {createContext, verifyInputs} from './native_impact_context.mjs';
import {project} from './native_impact_projection.mjs';
/** @param {unknown} value */
function inspect(value) {
  const context = createContext(value);
  const {graph, globals} = project(context);
  verifyInputs(context);
  const {flags, reads} = context;
  return {schema: 1, version: VERSION, flags, graph, globals, inputs: Object.fromEntries(reads), node: process.versions.node};
}

try {
  process.stdout.write(JSON.stringify(inspect(JSON.parse(readFileSync(0, 'utf8')))) + '\n');
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({error: `COV002: native dependency observation failed: ${message.slice(0, 1900)}`}) + '\n');
  process.exitCode = 2;
}
