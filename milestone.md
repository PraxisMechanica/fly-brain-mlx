# MLX fly-brain milestones

Audience: agents. Updated 2026-10-13 (America/Los_Angeles).
This is the current work order. Project policy is in [AGENTS.md](AGENTS.md),
scientific requirements in the [numerical contract](docs/agent/numerical-contract.md),
and commands in the [developer workflow](docs/agent/development.md).

## Current task

Finish the user's historical-record cleanup and default-deletion retention
policy, then commit and push verified changes to `origin/main`. Decision
confidence: 99% at `5f7b0d7df4df7cfae077986c98619d5eb0f6973e`. This task does not
resume numerical development or the remaining architecture implementation.

Generated outputs belong in ignored `logs/` or `executions/`. Successful commit
and push hooks delete those folders and legacy `.quality-reports/` outputs
unless an exact path, current operational reason and release condition appears
in `tools/code_quality/retention.json`. Failed hooks retain diagnostics while the
failure is unresolved. Scientific output receives no blanket exception.
Complete its repeat, batch, scoring and review consumers before deletion, or
register unfinished work before it crosses a commit. Remove expired exceptions.

Scientific qualification compares fresh MLX and CPU reference results for the
same case, fresh repeats, and individual versus batched trials. It does not
perform automatic MLX commit-N versus commit-N-minus-one output comparisons.

Historical execution records, generated outputs, archived verification scripts,
review logs and handoff histories have been removed. Seven independently
recorded regression fixtures remain as current test data under
`tests/data/reference`, totaling 45,360 bytes. Their manifest names the exact
current consumer and release condition. All seven bytes/hash identities were
preserved during relocation; production/reference arithmetic is unchanged.
The four active reference/oracle source files remain byte exact. Pinned FlyWire
input datasets and licences remain intact. The previously recorded P9 process
62191 no longer exists; no live-process output exception is registered and no
process was signalled.

Success requires:

- No historical archive directories or generated records remain in the current
  tracked tree; current test fixtures have explicit retention reasons.
- Default-deletion and specific-retention tests pass, including failed-hook,
  malformed-policy, path/symlink and indexed-input controls.
- Current source ownership reconciles the five actual source roots without
  exclusions or retired-file mappings. Scientific gates and known debt remain.
- Relevant application and real Metal/reference tests pass; required commit,
  push and hosted quality checks pass. Leave a clean checkout after delivery.

## Current scientific scope

Run the pinned FlyWire v783 leaky integrate-and-fire model on Apple silicon,
using MLX and uv. Brian2 and PyTorch are independent qualification references.
Preserve model equations, input identity, experiment definitions, native state,
events, queues and spike formats. Keep compilation and alternative arithmetic
modes subject to their explicit qualification requirements.

Numerical development remains on hold until the complete 37-rule architecture
enforcement is implemented, verified and accepted. This cleanup does not release
that hold.

The complete 52-case matrix and prescribed sugar/P9 four-trial comparisons are
not complete. Removed historical records do not establish current source or
execution-mode acceptance. Any new qualification must produce complete fresh
working data and satisfy every unchanged scientific gate before cleanup.
Future reference reuse needs verified input/source/build identity and complete
native equivalence; retain no archive simply in anticipation of possible reuse.

## Current architecture scope

Complete 37-rule structural enforcement remains **ANALYSIS FAILED (COV002)**.
Six recorded architecture/identifier findings remain. Strict typing, five
import contracts, source ownership reconciliation and qualified native metric
checks are useful components, not a full structural or scientific approval.
Current coverage is in [quality-coverage.md](docs/agent/quality-coverage.md) and
classifications in [architecture-ownership.md](docs/agent/architecture-ownership.md).

## Cleanup verification

At the `5f7b0d7` base, 157 targeted retention, hook, indexed-input and ownership
tests passed; strict typing returned zero errors. All 745 application unit and
integration tests passed (27 dependency warnings). The complete proof-artifact
integration consumer was explicitly excluded because it requires a fresh
full native proof bundle; no old bundle was retained or recreated for this task.
The relocated fixed replay passed on actual Metal against a fresh CPU reference
(one test, 86 dependency warnings). The staged native source-metric gate passed.

An independent read-only audit, reproduced for fixture/source byte identity,
confirmed all seven fixture moves, four frozen sources, six retained input files
and both licences are unchanged. Current source ownership reconciles 276 source
files with zero mapping findings and the unchanged six recorded findings. Active
document destinations and live consumers contain no removed-archive dependency.
The current index contains no historical archive or generated-output paths.

Remote reconciliation fetched `origin/main` and found it exactly equal to this
checkout at `5f7b0d7`; mandatory commit, push and hosted checks must cover the
delivery revision. Fresh verification outputs have finished their consumers and
have no retention exception; the successful delivery hooks delete them.

Keep existing independent work and other managed worktrees intact. This checkout
is detached because `main` is already checked out elsewhere; deliver through
`origin HEAD:main` without force. Other threads' read-only assessments do not
change this cleanup's scope or grant permission to overwrite their work.
