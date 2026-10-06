# MLX fly-brain milestones

Audience: agents. Updated 2026-10-06 (Europe/Zurich).
This is the active plan, acceptance status, and next-work record.
[AGENTS.md](AGENTS.md) owns project policy; the
[numerical contract](docs/agent/numerical-contract.md) owns scientific semantics
and gates. The [agent index](docs/agent/README.md) maps all document owners.
The complete [historical milestone log](docs/agent/history/milestones.md)
preserves earlier decisions, failures, commands, and evidence. Historical holds
and next actions apply only to their recorded checkpoints.

## Objective and scope

Run the pinned FlyWire v783 leaky integrate-and-fire model locally on Apple
silicon with MLX, preserving model behavior, experiment setup, neuron/edge
identity, and existing spike outputs. Provide reproducible scientific evidence,
measured performance, and verified installation instructions.

The production runtime remains MLX-only. Brian2 and PyTorch serve independent
qualification. Do not add MaleCNS, new neuron models, plasticity, reinforcement
learning, a user interface, or a general simulation framework. Preserve all data,
evidence, and assigned work.

## Current agent goal — 2026-10-06

Complete rearchitecture, refactoring, and general cleanup, then prepare a verified
handoff to the prior implementation agent. This is the user's latest scope
amendment. Decision confidence: 99% at
`6d57cd1ff32f0eedf0151443538258ee015bf0ab`.

This agent owns the remaining architecture/dependency repairs, their required
quality enforcement, documentation cleanup, and preservation verification.
Scientific checks are in scope only when needed to prove a refactor preserves
behavior. New simulator features, numerical remedies, the remaining full-network
matrix, performance optimization, and Milestones 4–7 belong to the prior
implementation agent after handoff. The earlier whole-project percentage and
completion-time estimates do not measure this bounded goal.

Completion requires:

- Finish the authorized architecture repairs and complete applicable structural
  enforcement. Unresolved coverage or violations cannot be reported as a pass;
  preserve the strict contract and scientific acceptance gates.
- Keep the human README and agent documentation coherent, with one active owner
  for each instruction, decision, and next action.
- Pass the required local commit/push checks and behavior-preservation checks
  appropriate to each refactor. Record actual coverage, failures, skipped checks,
  and any remaining approval constraints.
- Push small coherent commits to `origin/main`; leave a clean working tree and
  preserve data, scientific evidence, incoming work, and suspended runs.
- Provide a concise handoff with delivered commits, architecture boundaries,
  verification, unresolved approvals and scientific limits, and the prior
  implementation agent's ordered next work. Do not continue implementation once
  this refactor/cleanup goal is verified and ready for handoff.

## Current state

- Architecture remediation completed on 2026-10-04; all seven recorded checks
  pass within that scope. [Release evidence](docs/agent/history/architecture-remediation.md#completion-evidence-and-limits).
- Milestones 0–3 are complete within their recorded envelopes. Milestone 4 is
  active. Milestones 5–7 have not started.
- The original arithmetic has **9/52 accepted cases**: all five sugar trials at
  0.1 seconds, plus P9, silenced sugar, two-class, and silent trial 0 at that
  horizon. Eight rasters match the reference exactly; sugar trial 1 has a separate
  reviewed acceptance. [Case evidence](docs/agent/history/milestones.md#milestone-4--full-network-parity).
  The remaining 43 cases and prescribed one-second batches/repeats are required.
- The one-second sugar case is rejected. Its spike-time F1 agreement score
  (the harmonic mean of precision and recall) is **0.7988149744142203**, below
  the unchanged **0.95** floor. [Complete failure proof](docs/evidence/milestone-4/one-second-sugar-metric-failure/completed-case/verification.json).
  Explaining its first fork does not waive this failure.
- The user resumed work on 2026-10-05; the current cleanup and enforcement
  holds below govern subsequent work. Earlier architecture and investigation
  holds remain historical. The preserved P9
  process 62191 remains designated suspended; do not resume or discard it
  without resolving its original-mode evidence. [Pause record](docs/evidence/execution-time-investigation/pause.json).
- The latest delivered refactor checkpoint is
  `54aea507158774760f8c57e077b1411dc52cdb1e` on `origin/main`, followed by the
  verified typed-storage correction in this source. Clock and actual-row repairs,
  pure comparison rules, owned command composition, native symbol/graph
  foundations, reviewed ownership and runtime-parent decisions are delivered.
  Required local commit/push hooks and each configured hosted job passed. The
  next RNG slice is verified in this source; its delivery evidence stays in the
  dated history and compact component record.
- Deliver small coherent commits directly to `main` through both installed hooks,
  under the user's latest delivery instruction. Preserve original refs and all
  incoming work. The non-production authorization in `AGENTS.md` covers the
  hosted cache; `QUALITY_CI_TEMP_DB_CACHE_APPROVED` is verified true.
- Complete 37-rule enforcement remains **ANALYSIS FAILED (COV002)**. Feature and
  numerical development remain held. The [quality coverage](docs/agent/quality-coverage.md)
  owns working mechanisms and missing analysis; [source ownership](docs/agent/architecture-ownership.md)
  owns the reviewed classifications and remaining findings. Green component
  checks grant no new scientific acceptance.
- Native structured-type export remains assigned, unintegrated work. The
  committed inactive session candidate `6e111545` and typed correction `a58be25e`
  pass 106 parent Metal cases and 66 value/package/canonical-hook cases. Complete
  pinned-run/four-trial memory proof and collector migration remain required
  before adoption. No new scientific acceptance is granted. The
  [checkpoint history](docs/agent/history/milestones.md#refactor-and-enforcement-checkpoint-2026-10-06)
  retains original test counts, failures, review decisions and delivery evidence.

## Parallel refactor ownership — 2026-10-06

The [assignment record](docs/agent/handoffs/parallel-refactor-20261006.md) owns
current worker scopes, committed handoffs and dependent integration order.
Independent components run concurrently; one writer owns each file. Workers
commit verified changes before handoff; the parent reconciles and pushes serially.

## Next work for this agent

1. Finish structural enforcement and its rejection/error/weakening fixtures.
   Complete native type/call/alias/effect/control-flow coverage, maintain exact
   reviewed inputs, and repair remaining findings. Preserve all existing metric,
   index and hook controls. Complete required gate/merge enforcement and verify
   each delivered revision through the hosted gate. Use the pinned
   [tool provenance](tools/code-quality/provenance.json) and
   [developer commands](docs/agent/development.md).
2. Complete the remaining qualification/execution boundary and other recorded
   ownership repairs, using the accepted boundary review and preservation gates.
   Do not change numerical policy or transfer scientific case acceptance.
3. Finish documentation consistency checks and prepare the handoff against the
   completion criteria above; foundation probes are not complete enforcement.

## Prior implementation agent's next work after handoff

1. Complete reference identity, sealing, and reuse under the
   [reviewed provenance contract](docs/evidence/execution-time-investigation/reference-reuse/astra-review.md).
   Build/runtime identity and complete tape/native checks are implemented;
   cache reuse remains disabled until its decisive qualification passes.
2. Finish applicable scientific qualification before enabling guarded exact-count
   reduction in normal execution. The 157 scalar cases, 24,576 pinned cases,
   complete layout, two fresh complete sugar native trajectories, and separate
   layout repeat match their retained oracle. [Full native proof](docs/evidence/execution-time-investigation/exact-count-reduction/full-native/parent-verification.json).
   The original reducer remains the default; broader required checks remain.
3. Measure an improved complete representative check. Finish the prerequisites
   for the [prospective voltage-increment prototype](docs/agent/numerical-contract.md#prospective-single-state-voltage-increment-prototype),
   then screen the failed one-second sugar case. Keep original arithmetic and
   references as oracles; no old case acceptance transfers to a changed mode.
4. Continue the complete Milestone 4 matrix and required batches only with
   qualified modes. Then complete benchmarking, reproduction, final scientific
   review, and handoff.

## Remaining constraints and evidence limits

The buffered reference writer, vectorized complete queue proof, and singleton
active-source PyTorch comparator have their own qualification. The original
PyTorch core remains pinned; active-source evaluation is qualification-only.
[Prospective decision and native proof](docs/evidence/execution-time-investigation/active-cpu-qualification/full-native/parent-verification.json).
The required complete four-trial certification remains separate.

The isolated increment prototype repairs its saved local predicate and repeats
exactly on Metal. The separately recorded candidate suite has 208 passes, zero
failures/errors/skips. [Preserved suite](docs/evidence/execution-time-investigation/already-running-suite/result.json).
Neither establishes a repaired full-network case. The original implementation's
nine accepted cases retain their original source and execution-mode scope.

Keep the 99 original-state one-step conversion limitations visible. The isolated
fan-in stored-state accounting exception does not change small-network gates or
the full-network Brian2 reference. [Recorded decision](docs/evidence/milestone-2/initial-state-cast/astra-review.md#recorded-engineering-decision).

A completed-horizon absolute failure may stop a screening run; it cannot count
as completed acceptance. Reference reuse requires verified engine-specific
inputs, sources, builds, modes, and complete native values or digest-verified
replay. Every acceptance case still needs two real fresh candidate runs and all
fixed, paired, causal, queue, repeat, and batch obligations.

Component speedups are measurements within their recorded scope. They do not
establish complete-pipeline throughput or a reliable completion date. Earlier
forecasts and conditional budgets remain in history; reassess after a complete
improved check and the numerical remedy are qualified. Profile before a custom
Metal kernel; deeper numerical/representation decisions use the bounded review
workflow in `AGENTS.md`.

## Milestone acceptance and completion evidence

| Milestone | State | Required outcome and evidence |
| --- | --- | --- |
| 0 — Reference baseline | Complete | Reproduce pinned equations, schedule, inputs, and original disagreements without guessing. [Reference record](docs/agent/history/reference-baseline.md), [reviewed contract](docs/agent/numerical-contract.md), [checkpoint evidence](docs/agent/history/milestones.md#milestone-0--reference-baseline). |
| 1 — Small MLX kernel | Complete within its envelope | Every prescribed synthetic case passes per-step state budgets, exact ordinary discrete/event parity, deterministic shared stimuli, and repeat/chunk/batch checks; precision counterexamples remain explicit. [Contract](docs/agent/numerical-contract.md#reviewed-precision-and-state-acceptance), [evidence](docs/agent/history/milestones.md#milestone-1--small-mlx-numerical-kernel). Compilation remains unqualified. |
| 2 — Connectome loading | Complete | Pinned mapping, orientation, original rows, signed counts, silencing, stable reversible grouping, actual device fields/events, prescribed fan-in cases, and controlled delivery pass. Preserve the original-state conversion limitations. [Evidence](docs/agent/history/milestones.md#milestone-2--connectome-loading). |
| 3 — Backend integration | Complete | Normal installation runs complete shortest sugar twice and the silent control; persisted stimuli and populated/typed-empty Parquet files are reproducible and consumed by existing comparison tools. Record execution phases separately. [Evidence](docs/agent/history/milestones.md#milestone-3--backend-integration). |
| 4 — Full-network parity | Active; 9/52 original-mode cases | Every prescribed case satisfies all absolute and no-worse-than-PyTorch metrics, explicit empty/undefined rules, complete native causal audit, exact fresh repeatability, and required sugar/P9 one-second four-trial comparisons. Report independently scored cases, pooled summaries, and 100 ms localization bins. [Frozen matrix and gates](docs/agent/numerical-contract.md#full-network-acceptance-fixed-before-validation), [history](docs/agent/history/milestones.md#milestone-4--full-network-parity). |
| 5 — Benchmark and profiling | Not started | Run the complete pinned dataset within local memory and preserve parity. Measure loading, initialization, compilation/warm-up, warm simulation, timestep rate, biological/wall-time ratio, peak unified memory, synchronization, and collection separately. Keep the correct oracle; adopt only material measured improvements under qualified numerical modes. |
| 6 — Reproducibility and upstream preparation | Not started | Complete pinned installation/reproduction instructions, examples, benchmark method, tolerances, limits, notices, and focused tests. Execute a clean Apple-silicon installation/test workflow. Obtain a final bounded scientific review of the contract, tests, claims, performance, fallback, hidden semantic changes, and exact versus statistical parity; verify and apply corrections. Prepare a focused upstream patch. |
| 7 — Finalization | Not started | Apply final corrections; run the complete required suite with no silent skips; inspect direct evidence for every requirement, commits, and working state. State numerical/performance limits accurately and prepare the final upstream handoff. |

## Documentation checkpoint

The human README, active plan, contracts, workflow and checkpoint history have
separate owners in the agent index. Earlier preservation counts and commands
remain in the [dated documentation record](docs/agent/history/milestones.md#documentation-checkpoint).
The refactor audit at `f2de8f0` verifies 743 local paths/anchors across 22 authored
documents; its four corrections keep current state separate from history.
Scientific contract, acceptance table, numeric limits and original evidence are
preserved. Application/scientific suites are not rerun for prose-only corrections.
