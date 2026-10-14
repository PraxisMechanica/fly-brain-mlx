import { parseArgs } from 'node:util';
import { strictEqual } from 'node:assert';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

async function factIdentity(manifest) {
  const entry = import.meta.resolve('@eng-metrics/code-quality');
  const require = createRequire(entry);
  const provenance = JSON.parse(await fs.readFile(new URL('../code-quality/provenance.json', import.meta.url), 'utf8'));
  const implementation = await Promise.all(Object.entries(provenance.files).map(async ([name, record]) => {
    const digest = sha256(await fs.readFile(new URL(`../${name}`, entry)));
    strictEqual(digest, record.sha256, `Unqualified metric implementation: ${name}`);
    return [name, digest];
  }));
  const napi = require.resolve('@ast-grep/napi');
  require(napi);
  const bindings = require.cache[napi].children.filter(item => item.filename.endsWith('.node'));
  strictEqual(bindings.length, 1, 'Unqualified native metric binding');
  const go = require.resolve('@ast-grep/lang-go');
  const csharp = path.dirname(require.resolve('tree-sitter-c-sharp/package.json'));
  const native = [require.resolve('typescript'), napi, bindings[0].filename,
    go, createRequire(go).resolve('@ast-grep/setup-lang'), require('@ast-grep/lang-go').libraryPath,
    require.resolve('node-gyp-build'), require.resolve('node-gyp-build/node-gyp-build.js'),
    require('node-gyp-build').path(csharp)].sort();
  const runtime = await Promise.all(native.map(async name => [name, sha256(await fs.readFile(name))]));
  const python = execFileSync('python', ['-c',
    "import hashlib,json,pathlib,radon,sys\nif radon.__version__ != '6.0.1':\n raise RuntimeError('Required Radon 6.0.1 is unavailable')\nroot=pathlib.Path(radon.__file__).parent\nprint(json.dumps([sys.executable,sys.version,radon.__version__,[(str(p),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(root.rglob('*.py'))]]))",
  ], { encoding: 'utf8' });
  const configuration = await Promise.all(['package.json', 'pnpm-lock.yaml'].map(async name => sha256(await fs.readFile(new URL(`../../${name}`, import.meta.url)))));
  return sha256(JSON.stringify([implementation, manifest, runtime, python, process.versions, configuration]));
}

/** @param {import('@eng-metrics/code-quality').Comparison | import('@eng-metrics/code-quality').CommitCheck} result */
function compact(result) {
  const commits = 'commits' in result ? result.commits : [];
  const comparisons = commits.length
    ? commits.flatMap(({ commit, comparisons }) => comparisons.map(comparison => ({ commit, ...comparison })))
    : 'findings' in result ? [result] : [];
  const byRule = {};
  const examples = [];
  let total = 0;
  for (const comparison of comparisons) {
    for (const finding of comparison.findings) {
      total++;
      byRule[finding.rule] = (byRule[finding.rule] || 0) + 1;
      if (examples.length < 20) {
        examples.push({ ...finding, ...('commit' in comparison ? { commit: comparison.commit } : {}) });
      }
    }
  }
  return {
    status: result.passed ? 'pass' : 'regression',
    passed: result.passed,
    commits: commits.length,
    comparisons: comparisons.length,
    before: comparisons[0]?.before?.summary ?? null,
    after: comparisons.at(-1)?.after.summary ?? null,
    findings: { total, by_rule: byRule, examples, omitted: total - examples.length },
  };
}

try {
  const { values, tokens } = parseArgs({
    options: { staged: { type: 'boolean' }, base: { type: 'string' }, head: { type: 'string' } },
    tokens: true,
  });
  const names = tokens.map(token => token.name);
  if (new Set(names).size !== names.length || (
    values.staged ? values.base !== undefined || values.head !== undefined
      : !values.base?.trim() || !values.head?.trim()
  )) {
    throw new Error('Use --staged OR --base REF --head REF, once per argument');
  }
  const { checkStaged, checkCommits, createAnalysisManifest, loadMetricFacts, saveMetricFacts } = await import('@eng-metrics/code-quality');
  const identity = await factIdentity(createAnalysisManifest());
  const filename = 'logs/quality/metric-facts.json';
  const cache = await loadMetricFacts(filename, identity);
  const result = values.staged
    ? await checkStaged({ cache })
    : await checkCommits({ base: values.base, head: values.head, cache });
  await saveMetricFacts(filename, identity, cache);
  console.log(JSON.stringify(compact(result)));
  process.exitCode = result.passed ? 0 : 1;
} catch (error) {
  const reason = error instanceof Error ? error.message : String(error);
  const omitted = reason.length > 2000 ? reason.length - 1900 : 0;
  const message = omitted
    ? `${reason.slice(0, 1400)}\n[${omitted} characters omitted]\n${reason.slice(-500)}`
    : reason;
  console.log(JSON.stringify({
    status: 'analysis_error',
    passed: false,
    error: { message, omitted_chars: omitted },
  }));
  process.exitCode = 2;
}
