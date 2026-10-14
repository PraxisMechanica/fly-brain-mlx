// @ts-check
/// <reference path="./native_calls_api.d.ts" />
import { readFileSync } from 'node:fs';
import { inspect } from './native_calls_context.mjs';

try {
  const request = readFileSync(0, 'utf8');
  process.stdout.write(JSON.stringify(inspect(JSON.parse(request), request)) + '\n');
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({ error: message.startsWith('COV002:') ? message : `COV002: native call evaluation failed: ${message}` }) + '\n');
  process.exitCode = 2;
}
