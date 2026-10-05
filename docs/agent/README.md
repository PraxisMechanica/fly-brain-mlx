# Agent documentation index

Start with [AGENTS.md](../../AGENTS.md), then read the active
[milestone.md](../../milestone.md). Read the contract or a review record only
when the next task needs it. The root [README.md](../../README.md) serves human
readers who want to install, run, and compare simulations.

## Document ownership

| Document | Owns |
| --- | --- |
| [AGENTS.md](../../AGENTS.md) | Project-specific agent policy, review settings, and repository remotes |
| [milestone.md](../../milestone.md) | Current scope, holds, next work, milestone acceptance, and completion evidence |
| [Numerical contract](numerical-contract.md) | Reference semantics, precision, canonical stimuli, repeatability, and the frozen full-network gates |
| [Typing limits](typing.md) | Scope and reasons for local third-party stubs and narrow suppressions |
| [Historical records](#historical-records) | Dated decisions, failures, measurements, and original qualification scope |
| [Review briefs](#review-briefs) | Original bounded assignments and their return conditions |
| [Evidence](../evidence/) | Original reports, arrays, review results, source hashes, and executed diagnostics |

Update the document that owns a fact. Other documents link to that owner.
Historical instructions describe their checkpoint; they do not reopen a review
or override the active plan. Evidence remains at its original location so that
recorded artifact paths and hashes retain their meaning.

## Historical records

- [Architecture audit](history/architecture-audit.md): findings before repair.
- [Architecture remediation](history/architecture-remediation.md): implemented
  repair, retired-source recovery, checks, and release scope.
- [Execution-time investigation](history/execution-time-investigation.md):
  measured costs and proposals before development resumed.

## Review briefs

These are retained assignment records. Current work and ownership come from
`milestone.md`; current review settings come from `AGENTS.md`.

| Brief | Recorded outcome |
| --- | --- |
| [Numerical contract](handoffs/astra-numerical-contract.md) | Resolved; durable decisions are in the numerical contract |
| [Accumulation design](handoffs/astra-accumulation-design.md) | Completed manual review; factored design integrated after architecture release |
| [Initial-state conversion](handoffs/astra-initial-state-cast.md) | [Review and engineering decision](../evidence/milestone-2/initial-state-cast/astra-review.md) |
| [Full-network evidence](handoffs/astra-full-network-evidence.md) | [Observer design decision](../evidence/milestone-4/evidence-design/astra-review.md) |
| [Full-network batches](handoffs/astra-full-batch-verification.md) | [Batch verification method](../evidence/milestone-4/batch-verification/astra-review.md) |
| [One-second sugar cause](handoffs/astra-one-second-sugar-cause.md) | [Bounded cause classification](../evidence/milestone-4/one-second-sugar-cause/astra-review.md) |
| [Timing remediation](handoffs/astra-one-second-timing-remediation.md) | [Prospective prototype decision](../evidence/milestone-4/timing-remediation/review-decision.json); no full-case pass |

## Documentation audit — 2026-10-05

Source checkpoint: `2362fab5c2019b95d665669f13ff81b39a537b20`.
Confidence in this organization decision: 98%. The user authorized the audit,
simplification, audience separation, and reasonable centralization.

| Finding | Resolution |
| --- | --- |
| README mixes installation with agent diagnostics, architecture, and checkpoint details | Keep user instructions in README; collect developer workflow here |
| Milestone log repeats acceptance and mixes active work with old holds and next actions | Separate the active plan from dated history; link to the numerical contract for scientific gates |
| Reports say development is paused or no push remote exists after resumption and publication | Mark them as historical; current status and remotes have one owner |
| Old handoffs require manual model switches or use an earlier effort setting | Preserve the assignment record; current delegation comes from AGENTS |
| Scientific formulas and decisions recur in handoffs and progress reports | Keep the numerical contract authoritative; treat other occurrences as historical evidence |

Relocated document paths are recorded in Git. Original evidence manifests keep
their original paths; resolve a historical source citation at its recorded
commit, for example `git show <commit>:<original-path>`.
