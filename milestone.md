# MLX fly-brain milestone

Updated 2026-10-15. The numerical contract owns acceptance; the agent index owns
navigation. Detailed evidence remains under the registered root
`executions/implementation-20261014-matrix`; paths below are relative to it.

## Scope and implementation

Worktree: `/Users/ocasta/.codex/worktrees/pr-split/fly-brain`, `origin/main`.
Preserve all gates, pinned inputs, protected references, seven fixtures and
practical architecture. `AGENTS.md` owns execution policies.

Simulation, comparison, canonical replay and qualification workflows exist.
Production uses float32 threshold-relative voltage, stable synaptic decay and
transient compensated integration. The contract specifies its order; no
correction state persists. Accumulation and source queues are unchanged.

Delivery baseline: `810359d`. Current commit, push and CI evidence belongs in
`compensated-voltage-candidate-01/delivery.json` when those checks finish.

## Current scientific evidence

The ten-second sugar trial-0 screen at `810359d` fails timing F1 **0.4705927123**.
Synaptic-increment arithmetic also fails, with optimistic F1 at most **0.93406**.
Native-bound diagnosis identifies inherited voltage-operation rounding. See
`decay-first-difference-03` and
`decay-timing-continuation-01/timing-upper-bound.json`.

The current whole-network ten-second screen matches **all 170,752 reference
spikes exactly**, timing F1 **1.0**, and satisfies every primary metric gate.
Six continuous native chunks take **1,279.66 seconds**; scoring takes **1.82
seconds** without another simulation. Evidence: `voltage-first-difference-01`
through `-06`, `voltage-timing-screen-01`. This screen grants no case acceptance.
Native target/linear probes pass. A bundled prototype hit its 295-second guard;
only missing work reran, passing in 27.82 seconds.

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
Those passes remain recorded for that implementation. **Current arithmetic:
0/52 accepted**; changed numerical updates require renewed MLX qualification.

## Remaining plan and completion

1. Deliver the candidate with required hooks and exact-revision CI.
2. **Next step: complete all 52 paired cases**, fresh repeats for all engines,
   causal audits, pooled/localized metrics and sugar/P9 one-second four-trial
   comparisons. Resume only verified compatible evidence. Stop failed gates and
   diagnose their causes before continuing; a first spike difference alone is
   not a failed timing metric.
3. Record results and limitations, commit and push, pass delivery checks, finish
   clean and release outputs after their verification consumers end.

Progress: **36%** (inventory 10 points, workflows 8, candidate 10, local acceptance
8). Matrix, batch and final delivery acceptance remain. Routine tests belong to
hooks and CI; scientific runs use bounded scope and compatible retained evidence.

Remaining elapsed execution time: working estimate **48–72 hours**;
**90%-confidence planning range: 40–120 hours**, including further repair and
requalification risk. This is engineering judgment, assuming continuous Mac
availability. Previous paired throughput projects **38–45 hours** of required
qualification; revise after measuring the new candidate's paired cases.
Storage preflight projects 49 GiB; doubled allowance and batches fit 192 GiB free.
