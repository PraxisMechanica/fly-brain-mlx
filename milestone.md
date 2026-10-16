# MLX fly-brain milestone

Updated 2026-10-15. Evidence root:
`executions/implementation-20261014-matrix`; paths below are relative.

## Scope and implementation

Worktree: `/Users/ocasta/.codex/worktrees/pr-split/fly-brain`, `origin/main`.
Preserve all gates, pinned inputs, protected references, seven fixtures and
practical architecture. `AGENTS.md` owns execution policies.

Simulation, comparison, canonical replay and qualification workflows exist.
Production uses float32 threshold-relative voltage, stable synaptic decay and
transient compensated integration. The contract specifies its order; no
correction state persists. Accumulation and source queues are unchanged.

Delivered `2031e77`: hooks, push and exact-revision CI pass. Evidence:
`compensated-voltage-candidate-01/delivery.json`.

## Current scientific evidence

Ten-second sugar trial 1 qualifies after bound parent causal review:
**171,973 spikes per engine**, with four one-step shifts. Native reconstruction
explains finite-precision state error within budget; every metric and fresh
repeat passes. Evidence:
`matrix-compensated-voltage-01/reviews/sugar-100000-1/review-decision.json`.

The full ten-second sugar trial-0 case passes every gate and fresh repeats for
all engines: **all 170,752 reference spikes match exactly**, timing F1 **1.0**.
No spike or common-history budget differences occur. Completion takes **12,710.06
seconds**. Native archives and complete digest files repeat identically.
Evidence: `matrix-compensated-voltage-01/cases/sugar-100000-0/case.json`.

**Local scientific inventory: all 323 checks covered**, with **222 fresh passes
and 101 unchanged reference passes verified and reused**. Fresh groups contain
210/6/6 tests, with exact disjoint node coverage and zero failures/errors/skips.
Two broader commands hit their 300-second limits; both remain unaccepted.
Only affected checks were subsequently run. Five unchanged accumulation/layout
audits are source/input/device compatible; all 221 retained archive hashes verify.
The changed-integration connectome pulse passes fresh, with two archive hashes
verified. The 99 original-state conversion and other contract limitations remain.
Evidence: `compensated-voltage-candidate-01/local-verification.json`,
`unchanged-reference-verification.json` and `audit-verification.json` there.

Fresh CLI workflows pass under `workflows-compensated-voltage-01`: two sugar
trials match Brian2 prefixes; silent output is typed empty. Schemas, provenance
and comparison JSON/CSV pass. Post-run verification corrects a prematurely hashed
diagnostic transcript; scientific artifact bindings verify.

**Previous arithmetic: 10/52 accepted** (sugar trials 0–4 at 0.1 and 1 second).
**Current arithmetic: 12/52 accepted**; numerical changes required new qualification.
All ten shorter sugar cases pass without spike or state-budget differences.
Ten-second trials 0 and 1 qualify as described above.
Evidence: `preflight-compensated-voltage-01/matrix.json`.

## Remaining plan and completion

1. **Done:** candidate delivery with required hooks and exact-revision CI.
2. **Next step: complete all 52 paired cases**, fresh repeats for all engines,
   causal audits, pooled/localized metrics and sugar/P9 one-second four-trial
   comparisons. Resume only verified compatible evidence. Stop failed gates and
   diagnose their causes before continuing; a first spike difference alone is
   not a failed timing metric.
3. Record results and limitations, commit and push, pass delivery checks, finish
   clean and release outputs after their verification consumers end.

Progress: **47%**: inventory 10, workflows 8, candidate 10, local acceptance 8,
matrix 11. Remaining matrix, batch and delivery gates are unverified. Routine
tests belong to hooks and CI; scientific runs reuse compatible retained evidence.

Remaining elapsed execution time: working estimate **40–64 hours**;
**90%-confidence planning range: 36–112 hours**, including further repair and
requalification risk. This is engineering judgment, assuming continuous Mac
availability. Two completed ten-second cases project **32.93 hours** for remaining
paired steps; other cases, batches and system swapping add uncertainty. Evidence:
`matrix-compensated-voltage-01-launch.json`.
Storage preflight projects 49 GiB; doubled allowance and batches fit 115 GiB free.
