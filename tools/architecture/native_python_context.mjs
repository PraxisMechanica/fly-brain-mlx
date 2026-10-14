// @ts-check
/// <reference path="./native_python_context_api.d.ts" />
import { readFileSync } from 'node:fs';
import { withSession } from './native_python_session.mjs';

/** @param {unknown} request @param {string} text @returns {Promise<NativePython.Report>} */
export async function inspect(request, text) {
  return (await withSession(request, text)).report;
}
try {
  const text = readFileSync(0, 'utf8');
  process.stdout.write(JSON.stringify(await inspect(JSON.parse(text), text)) + '\n');
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({error: message.startsWith('COV002:') ? message : `COV002: native Python context failed: ${message}`}) + '\n');
  process.exitCode = 2;
}
