import { parseArgs } from 'node:util';

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
  const { checkStaged, checkCommits } = await import('@eng-metrics/code-quality');
  const result = values.staged
    ? await checkStaged()
    : await checkCommits({ base: values.base, head: values.head });
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
