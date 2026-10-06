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
- Quality tooling and the shared commit/push hooks are installed. At `b932298`,
  the standalone metric engine has **17 source-only passes**, zero failures,
  errors, or skips. [Report](docs/evidence/code-quality/metric-intent-tests.xml).
  At `003ac89`, **29 quality tests** pass with zero failures, errors, or skips,
  including 12 controlled hook checks for child failures, missing tools,
  unchanged boundary debt, staged defects, and actual push rejection.
  [Report](docs/evidence/code-quality/hook-intent-tests.xml). Apple-silicon
  [continuous integration](.github/workflows/quality.yml) is configured at
  `c053f05`. At `1376e40`, [hosted run 37328288754](https://github.com/PraxisMechanica/fly-brain-mlx/actions/runs/37328288754)
  passes every step and uploads both [metric reports](https://github.com/PraxisMechanica/fly-brain-mlx/tree/edfbb9dcfb477bf788740ca9096165518d21231a/docs/evidence/code-quality/ci-1376e40).
  The first hosted run passed its checks but excluded hidden evidence paths;
  the corrected uploader preserves the two reports. Their nine comparisons
  pass, covering 232 files / 25,207 nonblank lines, average/max complexity
  5.37 / 28 and health/maintainability 69.05 / 69.05. Five additional real import
  fixtures reject aliases, type-only imports, indirect paths and re-exports;
  weakening transitive enforcement stops detecting the indirect defect.
  Eight index-guard fixtures reject untracked/ignored source and typing stubs,
  accept staging repairs and non-source evidence, and prove that disabling the
  guard hides the defect. They use real source-only Git repositories; the
  pipeline probe controls only the downstream metric exit.
  The shared check now passes **49 quality tests**, zero failures/errors/skips;
  formatting, lint, strict typing, all three import contracts, and staged/full
  commit metric checks pass. [Test report](docs/evidence/code-quality/index-intent-tests.xml).
  [Recorded coverage limits and definite clock finding](https://github.com/PraxisMechanica/fly-brain-mlx/blob/edfbb9dcfb477bf788740ca9096165518d21231a/docs/agent/quality-coverage.md):
  the full 37-rule architecture result is **ANALYSIS FAILED (COV002)**.
  Keep feature/numerical work held while that required enforcement is incomplete.
- The user approved native GitHub stacking on 2026-10-06. Stack #7 merged
  into `main`: [local checks](https://github.com/PraxisMechanica/fly-brain-mlx/pull/5),
  [hosted checks](https://github.com/PraxisMechanica/fly-brain-mlx/pull/6), and
  [boundary coverage](https://github.com/PraxisMechanica/fly-brain-mlx/pull/8).
  The merged head is `5efda389aabf5fa46b176dffb7fef6c69572685d`.
  Original PRs 1–4 are closed; all original refs, incoming work, and evidence
  remain preserved. Bulk metric dumps are excluded from the review diffs.
- The latest 2026-10-06 instruction requests direct commits when the commit
  and push hooks can run the checks. Deliver the authorized refactor/cleanup
  changes directly to `main` with both hooks. Confidence in this delivery choice
  is 99% at `5efda389aabf5fa46b176dffb7fef6c69572685d`. The earlier proposed fourth PR
  is superseded. PR cleanup no longer requires waiting for the merged layers.
- The complete structural analyzer is still missing, so feature/numerical work
  remains held. The latest user amendment on 2026-10-06 releases the hosted-cache
  approval hold through the non-production authorization in `AGENTS.md`.
  Repository variable `QUALITY_CI_TEMP_DB_CACHE_APPROVED` is now verified true;
  hosted run 37468037333 passed every job step at
  `68bc087a56884cf0cff4f62c956806bec228cbad`. Its saved staged and actual-commit
  metric reports both pass. This proves the configured gate at that revision;
  it does not complete the structural catalog. Prior skips are not passes.
  Local checks preserve their cache outside fixture cleanup. All three
  reconstructed layers passed their
  native commit/push hooks.

- Quality work resumed at `876cb157b403c6e65d96aa3d411ae8686988cf06` under the
  user's instruction to continue and deliver through local hooks. Confidence in
  this scope is 95%. The first repair injects the same typed timing clock into
  the simulation service and result writer through bootstrap. Eleven focused
  tests and strict typing pass; the ambient-clock control is rejected. Numerical
  backend sources, spike schema, and report fields are unchanged. Test artifacts
  are retained. Full checker coverage remains incomplete; scientific/performance
  implementation is still held.

- At `23dac175679b8cbc6b102c4ecc143e9a85a34487`, the clock repair is committed
  and pushed with both configured hooks passing. The full source inventory
  contains 238 Python/stub files, including 60 retained evidence-source records.
  The bounded qualification-boundary reviewer used fresh `gpt-6-astra` at `xhigh`
  and returned a 94%-confidence prospective decision. Parent source inspection
  confirms its findings: retain qualification-owned independent expectations,
  expose neutral actual native observations through narrow ports, and replace
  private layout/closure introspection. The accepted review is recorded at
  `docs/evidence/code-quality/qualification-boundary-20261006/astra-review.md`.
  Start with the actual reduction-row capability; preserve core/ledger scheduling
  and validate native bytes/ownership. A rewritten observer or ledger requires
  the fresh transparency/integrity and complete-shortest-run proof in that review.
  No new scientific case acceptance or arithmetic mode is approved.

- The first boundary slice replaces private `partial.args[1]` layout recovery
  with a qualification-owned typed actual-row reader. Neutral host observations
  now live outside the concrete backend; row arrays preserve native bits in
  immutable detached storage. The bound reduction descriptor reports the actual
  exact-count guard/fallback choice. Eighteen native/value tests, seven real
  paired/repeat/batch/singleton tests, and five source-only graph/hook tests pass
  with no failures or skips. Four direct real-device comparisons reproduce all
  96 old-reader arrays' dtype, shape, and bytes. Full typing and lint pass.
  The core, reducer, and ledger files are byte-unchanged; existing layout,
  accumulation, advance, and original preparation statements are preserved.
  Fresh test outputs and `row-verification.json` in the boundary evidence folder
  retain the proof and initial sandbox/caller failures. No full pinned-network
  case was rerun, and no acceptance transferred. Remaining concrete execution,
  state, and observation-policy dependencies still need the complete port slice.

- At `68bc087a56884cf0cff4f62c956806bec228cbad`, finish the analyzer's Python
  declaration-inventory and native Pyright resolver foundations. Forty-one
  source-only fixtures pass with no failures/errors/skips; strict typing,
  formatting, and lint pass. Actual aliased/re-exported/type-only protocol calls
  resolve to their defining method. Coverage/framing/resolution weakening loses
  detection of the same defects. Discovery parses 249 Python/stub files and
  3,332 named declarations across the six explicit roots, including all sixty
  retained evidence-source files. The compact component proof is recorded at
  `docs/evidence/code-quality/architecture-foundations-20261006/verification.json`.
  These are foundations, not complete symbol/role/resource/effect classification
  or whole-application enforcement. The 37-rule result remains COV002.

- At `0a313d02b56d886542d130134346506106a5f926`, the analyzer foundations are
  committed and pushed with both native hooks passing. Hosted run 37471806648
  completes every job step successfully. Its scope is the configured gate,
  not complete structural enforcement.
- Separate pure comparison scoring/result construction from reader orchestration.
  The four scoring function ASTs, result body, and first-read/prepare ordering
  remain unchanged. All 81 original/new serialized fixture pairs match; the
  shared-buffer regression detects an intentionally reordered reader control.
  Seventy-nine focused application/file/CLI cases and six source-only hook cases
  pass with no failures/errors/skips. A fourth import contract rejects direct,
  aliased, type-only, transitive, and re-exported rule-to-service dependencies;
  weakening scope/transitive enforcement loses detection. Strict typing,
  formatting, lint, and all four import contracts pass. Numerical backend,
  qualification adapters, scientific contract, and data remain unchanged.
  Compact proof: `docs/evidence/code-quality/comparison-rules-20261006/verification.json`.
  No case acceptance transfers; the full structural result remains COV002.

## Next work for this agent

1. Finish quality enforcement before further performance implementation. Complete
   structural-rule ownership/type/call/effect coverage and rejection fixtures;
   resolve remaining findings after the recorded clock repair below.
   Verify remaining metric/index weakening cases and required merge enforcement.
   Verify each delivered revision through the configured hosted gate.
   Use the pinned standalone
   metric package and existing uv/MLX architecture. [Tool provenance](tools/code-quality/provenance.json)
   and [developer commands](docs/agent/development.md).
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

At `710a267`, centralize twelve agent documents and preserve their original text
apart from link rebasing and historical notices. During that edit, incoming
quality work commits `aebad54`, `b932298`, and `003ac89` remain preserved on their assigned
branch. The first documentation push is blocked by then-unindexed incoming test
files; the owner subsequently commits them. No hook is bypassed.

The reconstructed documentation layer separates the human README, active plan,
scientific contract, developer workflow, and dated history. Source checkpoint
`5efda389aabf5fa46b176dffb7fef6c69572685d`; confidence in this scope is 98%.
Current preservation checks cover twenty authored documents and 738 local
links/anchors with zero errors. Linked local contents and 43 exact external
destinations were opened and reviewed; historical citations retain their scope. Complete milestone/reference history, twenty
scientific table rows, 87 numeric inline expressions, and the coefficient code
block remain unchanged. All 831 original versioned data/evidence files retain
their identity and working contents. Native commit/push checks are required
before delivery. The former hosted-cache approval hold is released by the latest
user amendment; hosted verification results retain the revision scope above.

[Original documentation verification](https://github.com/PraxisMechanica/fly-brain-mlx/blob/edfbb9dcfb477bf788740ca9096165518d21231a/docs/evidence/documentation/organization-20261005/verification.json)
records the earlier 755-link check, fourteen parsed command examples, successful
help/task-list checks, and required hook pass at `a47cb1b`. Those results retain
their original checkpoint scope. The initial broken README anchor was repaired;
the CLI help check used a task cache after a sandbox cache error. No installation
or simulation was needed. Application/scientific suites were not rerun for this
documentation-only reapplication.
