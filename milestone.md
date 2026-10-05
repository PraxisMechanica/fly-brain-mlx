# MLX fly-brain milestones

Audience: agents. Updated 2026-10-05 (Europe/Paris).
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
evidence, and assigned work. User approval requirements for database deletion
and application programming interface or database schema changes still apply.

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
- Development resumed by the user's 2026-10-05 instruction. Architecture and
  investigation holds in historical reports are superseded. The preserved P9
  process 62191 remains designated suspended; do not resume or discard it
  without resolving its original-mode evidence. [Pause record](docs/evidence/execution-time-investigation/pause.json).
- Quality tooling and the shared commit/push hooks are installed. At `b932298`,
  the standalone metric engine has **17 source-only passes**, zero failures,
  errors, or skips. [Report](docs/evidence/code-quality/metric-intent-tests.xml).
  At `003ac89`, **29 quality tests** pass with zero failures, errors, or skips,
  including 12 controlled hook checks for child failures, missing tools,
  unchanged boundary debt, staged defects, and actual push rejection.
  [Report](docs/evidence/code-quality/hook-intent-tests.xml). Rejecting weakened
  checks, continuous integration, and complete architecture-rule coverage remain open.
- The recorded 2026-10-05 workflow amendment uses coherent review branches and
  stacked pull requests. The incoming quality work is on `codex/quality-gates`.
  Preserve that assignment; publish verified increments to the user-owned
  `origin`. [Workflow amendment](docs/agent/history/milestones.md#development-resumed--measured-performance-remediation).

## Next work

1. Finish quality enforcement before further performance implementation. Verify
   attempts to weaken checks beyond the completed controlled hook proof; add continuous
   integration and complete structural-rule coverage. Use the pinned standalone
   metric package and existing uv/MLX architecture. [Tool provenance](tools/code-quality/provenance.json)
   and [developer commands](docs/agent/development.md).
2. Complete reference identity, sealing, and reuse under the
   [reviewed provenance contract](docs/evidence/execution-time-investigation/reference-reuse/astra-review.md).
   Build/runtime identity and complete tape/native checks are implemented;
   cache reuse remains disabled until its decisive qualification passes.
3. Finish applicable scientific qualification before enabling guarded exact-count
   reduction in normal execution. The 157 scalar cases, 24,576 pinned cases,
   complete layout, two fresh complete sugar native trajectories, and separate
   layout repeat match their retained oracle. [Full native proof](docs/evidence/execution-time-investigation/exact-count-reduction/full-native/parent-verification.json).
   The original reducer remains the default; broader required checks remain.
4. Measure an improved complete representative check. Finish the prerequisites
   for the [prospective voltage-increment prototype](docs/agent/numerical-contract.md#prospective-single-state-voltage-increment-prototype),
   then screen the failed one-second sugar case. Keep original arithmetic and
   references as oracles; no old case acceptance transfers to a changed mode.
5. Continue the complete Milestone 4 matrix and required batches only with
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

At `710a267`, centralize twelve agent documents and preserve their original text
apart from link rebasing and historical notices. During that edit, incoming
quality work commits `aebad54`, `b932298`, and `003ac89` remain preserved on their assigned
branch. The first documentation push is blocked by then-unindexed incoming test
files; the owner subsequently commits them. No hook is bypassed.

The current documentation task separates the human README, active plan,
scientific contract, developer workflow, and dated history. Source checkpoint
`2362fab5c2019b95d665669f13ff81b39a537b20`; confidence in the organization
choice is 98%. Scientific criteria and recorded artifacts remain unchanged.
All 752 local links/anchors across nineteen authored documents pass. The full
milestone/reference history, twenty scientific table rows, 87 numeric inline
expressions, and the coefficient code block are preserved. All fourteen
application command examples parse; help and task-list commands succeed. The
831 original versioned data/evidence files retain their identity and working
contents. Required hook evidence will be recorded after the commit.
