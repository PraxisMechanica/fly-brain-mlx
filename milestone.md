# MLX fly-brain milestones

This is the authoritative project plan, acceptance criteria, and progress record. Updated 2026-10-04 (Europe/Paris). It consolidates the supplied charter, milestone specification, startup evidence, and subsequent user amendments.

## Development hold — architecture compliance

Status: **architecture remediation authorized by the user on 2026-10-04; further feature development remains halted**. Apply the `python-design` and `software-design` skills. The user requires an MLX-only application, removal of Conda and NVIDIA backend support, and removal of non-essential dependencies. This instruction supersedes the older preservation and investigation-only instructions below.

Implement and verify the authorized architecture repairs. Do not advance connectome loading, numerical optimization, or full-network integration during this work. Preserve numerical semantics, existing data/output contracts, scientific evidence, and incoming work. Remove the inherited non-MLX runtime and installation workflows. Brian2 and PyTorch remain qualification-only dependencies because the numerical contract requires their comparisons. Further feature development requires completion of the architecture acceptance checks below.

Investigation complete: [architecture audit and remediation proposal](docs/architecture-audit.md). The implementing agent read both design skills but did not implement the required application architecture and approved Python stack. The audit records that implementation omission, the [current-versus-approved technology inventory](docs/architecture-audit.md#current-technologies-and-approved-target), and the required repairs. The [static evidence](docs/evidence/architecture-audit/checks.json) records a two-file configured Pyright pass versus 881 diagnostics across nine authored files and five Ruff import-order diagnostics; these are not claims of 881 runtime defects. No application remediation or numerical execution occurred during the audit.

Dependency scope clarified on 2026-10-04: the proposal uses one uv project, lockfile, and supported environment, with MLX as the application engine. Brian2 and PyTorch remain qualification dependencies required by the reviewed contract. No Conda workflow or installation of the other NVIDIA backends is needed for this goal. No database infrastructure exists or is proposed; SQLModel, Alembic, database repositories, and transaction units of work are excluded. The [dependency-scope check](docs/evidence/dependency-scope-20261004.json) verifies installed-package compatibility only; a clean project installation remains open. This changes the remediation proposal, not the application.

Current work is architecture remediation only. The [implementation record](docs/architecture-remediation.md) defines the boundaries, dependency scope, work steps, and verification. The [incoming-work archive](docs/evidence/architecture-remediation/incoming-review-work.json) preserves the unfinished scientific review before refactoring. All hold-release checks remain open:

- [ ] Declare ownership and allowed imports for all application-owned code; resolve every audit finding or record an explicit user-approved exception.
- [ ] Verify uv-managed package installation, pinned dependency resolution, normal imports without application path injection, and side-effect-free domain/service imports.
- [ ] Enforce dependency boundaries; inject configuration, execution engines, and output collaborators instead of hidden globals and runner/orchestrator back-references.
- [ ] Pass full-scope Ruff and the documented typing policy, with strict public boundaries and narrowly scoped third-party limitations.
- [ ] Verify thin entrypoints, independent run configurations, and existing input/output contracts; classify unit, reference integration, and Metal qualification tests.
- [ ] Requalify preserved scientific suites and deterministic replays after relevant refactors, using fresh evidence and unchanged acceptance budgets, with no skipped required checks.
- [ ] Record the final Python/software architecture review and all completion evidence here before lifting the hold or advancing milestones.

The complete definitions are in the [audit acceptance checks](docs/architecture-audit.md#acceptance-checks-for-lifting-the-hold). This hold supersedes older instructions to preserve a defective application structure, while numerical semantics, source provenance, evidence, data, existing external contracts, and unrelated code remain preserved. The manual accumulation review is now idle and acknowledges the hold; its unfinished work is preserved, not finalized by this audit.

## Objective and execution

Develop a scientifically validated Apple MLX backend for the [Eon Systems fly-brain simulation](https://github.com/eonsystemspbc/fly-brain), preserving the existing FlyWire v783 leaky integrate-and-fire model's numerical behavior, activation and silencing experiments, and output contracts. Run the complete connectome locally on Apple silicon and provide reproducible correctness evidence, measured performance, and verified installation instructions. This is an MLX array-compute project, not an MLX-LM language-model project.

Implementation owner: GPT-6.1 Sol at the reasoning effort selected by the user (currently `max`). The user controls parent-model changes. Future bounded scientific, numerical, and difficult kernel-design reviews use GPT-6 Astra subagents at `xhigh`, following [the current delegation rule](AGENTS.md#active-project-specification). Keep the already assigned manual accumulation-design review with its current owner and recorded return procedure.

Do not implement MaleCNS, new neuron models, plasticity, reinforcement learning, a user interface, or a generalized simulation framework. Do not rewrite upstream architecture or port every existing backend. Optimize only after correctness is established. No custom Metal kernel without profiling evidence. Honor [AGENTS.md](AGENTS.md), including schema approval and database preservation requirements.

## Implementation and evidence rules

The numerical backend varies; the model, experiment definitions, neuron ordering, connection direction, weights, delays, activation, silencing, thresholds, reset, and timestep semantics must remain invariant under the reviewed contract.

- Read and run the reference before adding MLX code. The bounded review selects pinned Brian2 2.8.0 CPU float64 as ground truth; the [reviewed contract](docs/mlx-port-baseline.md#reviewed-discrete-contract) resolves material inconsistencies. Do not blend contradictory backend behavior.
- Extend the existing backend interface with a small validated numerical core. Preserve upstream structure, tools, callers, and unrelated code.
- Generate stochastic stimulus schedules outside the engines and feed identical events to each. Equal seed values across unrelated generators do not prove equal stimuli.
- Keep simulation state resident on the Apple graphics processing unit. Do not transfer complete state to the CPU each timestep. Retain the simple correct implementation as an oracle if optimized kernels are introduced.
- Verify one milestone before proceeding to the next. Update this file after significant steps with exact commands, test results, measured outcomes, unresolved issues, and supporting artifact links. Commit verified work incrementally on `main`.
- Distinguish tolerance-bounded small-network continuous state with exact ordinary-fixture discrete parity from full-network event/statistical parity. Keep the separately asserted threshold-rounding limitation explicit. Do not declare acceptance thresholds after seeing results, explain away discrepancies, or infer scientific validity from a successful run alone.

Each review assignment must contain the reason for deeper review, current checkpoint and commits, exact evidence and files to inspect, one bounded requested outcome, and a completion condition. Use [the bounded subagent skill](skills/bounded-subagent/SKILL.md) with the model and effort specified by this project's delegation rule for future reviews. Sol awaits the result, verifies the evidence, records the decision, and commits integrated work before continuing dependent implementation. The earlier manual handoffs retain their historical completion records.

## Completion requirements

Every requirement remains open until the evidence below is recorded and inspected:

1. `python main.py --mlx --t_run 0.1 --n_run 1` runs on Apple silicon.
2. MLX outputs the existing Parquet spike schema and works with existing comparison tools.
3. Seeded runs are repeatable with identical externally generated stimulus schedules.
4. Small deterministic networks match an approved reference at every timestep, including leak, threshold, reset, excitation, inhibition, simultaneous fan-in, fan-out, delay, and silencing.
5. The full pinned FlyWire v783 dataset runs without CPU fallback for synaptic propagation.
6. Full-network numerical parity with Brian2 is no worse than PyTorch under an explicitly approved metric, stimulus protocol, and tolerance.
7. Benchmarks separate initialization, compilation/warm-up, warm simulation, result collection, memory, and synchronization costs; report steady-state timesteps per second and biological simulation time per wall-clock second.
8. A clean Apple-silicon installation and documented reproduction workflow are executed successfully.
9. Final scientific review, required corrections, and complete verification are recorded without silently skipped tests or overstated claims.

## Milestone 0 — Reference baseline

Status: complete for reference evidence; the numerical-contract review is also resolved below.

Acceptance: `docs/mlx-port-baseline.md` documents enough implementation-level detail to reproduce the pinned Brian2 model without guessing. Relevant tests and experiments provide direct evidence for the stated behavior. Material disagreements are collected for review, not silently resolved.

Required work:

- [x] Pin and import upstream while preserving its source and licence notices.
- [x] Read Brian2, PyTorch, and orchestration code.
- [x] Reproduce the shortest supported Brian2 CPU experiment.
- [x] Record equations, exact discrete integration, operation order, timestep, delay, threshold, reset, refractory behavior, activation, and silencing.
- [x] Record neuron ordering, connection direction, data counts, random-number and seed behavior.
- [x] Record benchmark fields, spike-output schema, comparison-tool contracts, and backend disagreements.
- [x] Record licensing and publication/source distinctions.
- [x] Run focused reference-contract tests and preserve raw evidence.
- [x] Finish the baseline document and the bounded numerical-contract handoff.

Evidence completed:

- Upstream commit: `a3db62f9436074e485c0278290c2164ed6150808`; [pin record](docs/upstream-pin.json).
- Import commit: `4466b37`; upstream implementation matches the pinned tree. Only project documentation and ignore patterns differ at import.
- Experiment commit: `295994b`.
- Consolidation commit: `396f169`; reference-contract evidence commit: `5489ae0`.
- Command: `.venv/bin/python scripts/run_reference_baseline.py --output data/results/mlx-reference-20261004`.
- Brian2 2.8.0, NumPy 1.26.4, Python 3.10.14; full resolved reference environment in `requirements-reference.txt`.
- Full-data sugar experiment: 21 stimulated neurons at 200 Hz, 0.1 seconds, one trial, 0.1 ms timestep; 1,518 spikes and 321 active neurons.
- Measured build: 12.742 seconds; simulation: 1.348 seconds; spike extraction: 0.329 seconds; total accounted time: 16.824 seconds. This is one unseeded reference run, not a repeatability or MLX-performance claim.
- [Raw result and schema](docs/evidence/milestone-0/brian2-baseline.json), [log](docs/evidence/milestone-0/brian2-baseline.log), [input summary and hashes](docs/evidence/milestone-0/input-summary.json).
- Measured inputs: 138,639 neurons, 15,091,983 connection rows. The original approximate five-million figure does not describe the pinned connectivity file.
- [Reference baseline contract](docs/mlx-port-baseline.md) records the exact observed model, ordering, data/output contracts, comparison tools, differences, and licence notices.
- `.venv/bin/python -m pytest -q tests/test_reference_contract.py --junitxml=docs/evidence/milestone-0/reference-tests-final.xml --disable-warnings`: nine passed, zero skipped/failures/errors, 136 dependency warnings, 2.84 seconds. [Final test report](docs/evidence/milestone-0/reference-tests-final.xml).
- [Generated update, schedule, and delay diagnostic](docs/evidence/milestone-0/reference-schedule.json): Brian2 recurrent conductance arrives at step 18 and affects voltage at step 19; PyTorch's measured arrival/influence steps are 20/21.
- [Publication equations and source provenance](docs/evidence/milestone-0/publication-source.json) were retrieved from the Europe PMC full-text interface and distinguish the original v630 study from this v783 dataset.
- The inspection harness reproduced the retained schedule/delay evidence exactly. All 71 local links in the README, milestone, baseline, and handoff documents passed verification. `git diff --check` passed; the diff against the upstream pin for numerical source, data, original scripts, environments, and licences is empty.
- [Bounded Astra review request](docs/handoffs/astra-numerical-contract.md) records the checkpoint, evidence, required decisions, and return condition. No review decision is implied by Milestone 0 completion.

Resolved scientific review:

- Brian2's coupled linear integration, threshold-before-stimulation scheduling, frozen/gated refractory state, outgoing-only silencing, and step-18 delivery/step-19 voltage effect are authoritative. PyTorch remains the comparison baseline with its known numerical differences.
- A firing neuron immediately blocks incoming writes even when its refractory duration is zero; the review refined the earlier reset-only explanation with a pre-reset observation.
- Float32 policy, state tolerances, exact discrete invariants, threshold-rounding treatment, deterministic stimuli, and full-network acceptance are fixed in the [reviewed baseline](docs/mlx-port-baseline.md#reviewed-precision-and-state-acceptance). The full-network gate requires both fixed floors and no worse than PyTorch for every primary metric/case.

## Numerical-contract handoff

Status: resolved. Contract approved for Milestone 1 implementation/qualification; the user returned execution to GPT-6.1 Sol at `xhigh`. This is not approval of an MLX implementation or full-network result.

Review checkpoint (2026-10-04):

- Probe/evidence commit: `4b7ea63`, following incoming checkpoint `6deca27`. `.venv/bin/python scripts/probe_numerical_contract.py --output data/results/mlx-numerical-review-20261004` completed all assertions. It probes linear float32 error, threshold rounding, cancellation, and deterministic external replay; it does not implement a backend.
- A 10,000-step linear diagnostic against Brian2 float64 measured maximum float32 voltage/synaptic errors of 0.000381470/0.000218289 mV. A quarter-unit-in-the-last-place threshold offset changes the float32 spike decision; a 4,097-event cancellation case changes the sum from 0.275 to 0.25 mV with adverse ordering. These are explicit precision limitations, not parity passes.
- Two NumPy runtime replays and two independently built C++ standalone replays produced identical complete state/discrete traces and 43 spikes each under the same 1,000-step, three-channel event schedule. Schedule regeneration, save/load, duration prefix, and trial separation checks passed.
- [Probe measurements](docs/evidence/milestone-0/numerical-contract.json), [compressed raw reference trace and events](docs/evidence/milestone-0/numerical-contract-replay.npz), and [probe source](scripts/probe_numerical_contract.py) are retained. Fresh standalone builds and four raw traces remain in the probe output directory; no existing output was removed.
- `.venv/bin/python -m pytest -q tests/test_reference_contract.py --junitxml=docs/evidence/milestone-0/reference-tests-contract-final.xml --disable-warnings`: 12 passed, zero skipped/failures/errors, 162 dependency warnings, 17.97 seconds. Added tests settle same-step recurrent/native-Poisson input gating, refractory-boundary arrival, and replay equivalence with guaranteed native Poisson input. The preceding 11-test and 12-test runs are preserved; the final refinement adds native Poisson input to the pre-reset gating test.
- All 92 local links/Markdown anchors across the README, milestone, baseline, and handoff passed verification. The compressed evidence matches each of the four retained raw traces and the stimulus hash. Original upstream file changes remain limited to the pre-existing `.gitignore` and README changes; numerical source/data are untouched. `git diff --check` passed.

Deliverable completed: the [bounded review record](docs/handoffs/astra-numerical-contract.md#decision-record--resolved) records selected semantics, evidence, limits, and remaining qualification. The [baseline](docs/mlx-port-baseline.md#reviewed-discrete-contract) holds the durable specification. No numerical backend or public interface was implemented in this review.

Return condition met: reference semantics and acceptance decisions are explicit and evidence-supported. No further reference probe blocks Milestone 1. Actual MLX precision/compilation/repeatability, high-fan-in accumulation, the full-network matrix, and future public/empty-output schema changes remain unverified or unapproved as specified in the handoff. The user must switch back before implementation resumes.

## Milestone 1 — Small MLX numerical kernel

Status: complete for the reviewed small-network envelope, uncompiled Metal mode. Compilation and full-connectome accumulation are not qualified.

Acceptance: every timestep's voltage and synaptic state meet the [reviewed budgets](docs/mlx-port-baseline.md#reviewed-precision-and-state-acceptance): isolated one-step error ≤`2e-5 + 2e-6*abs(reference)` mV and trajectory error ≤`1e-3 + 1e-5*abs(reference)` mV. Ordinary fixtures require exact spike/reset/refractory/delay-event state, with no timing slack. Test strict equality and neighboring representable values, and assert the separate near-threshold rounding limitation rather than claiming universal float64 spike equivalence. Run every enumerated synthetic case, shared deterministic stimuli, and repeated identical runs without skips.

Start with source indices, destination indices, and weights. Keep model state on the Apple graphics processing unit. Use externally generated stochastic schedules shared with the reference. Do not load the full connectome or add a custom Metal kernel at this milestone.

Startup checkpoint (2026-10-04):

- Review checkpoint `4fcb224` was clean. The active session metadata confirms GPT-6.1 Sol at `xhigh`; no model was switched or substituted by the agent.
- Installed MLX/MLX-Metal 0.32.3 into the existing Python 3.10.14 environment; [MLX requirements](requirements-mlx.txt) and [qualification tools](requirements-dev.txt) are pinned. Existing reference dependency versions were preserved.
- `MLX_ENABLE_TF32=0` GPU smoke test succeeded on Apple M1 Max, macOS 15.3.1, architecture `applegpu_g13s`, 34,359,738,368 bytes unified memory. Device operations returned `[2.0, 3.0]` for `[1, 2] + 1`.
- The sandbox cannot expose a Metal device; the GPU smoke process was authorized outside the sandbox. Actual qualification must use the same access, without CPU fallback. No core correctness or milestone acceptance is inferred from this smoke test.

Initial implementation checkpoint:

- [Private core](code/mlx_core.py) uses explicit Metal streams, float32 state, integer last-spike steps, a Boolean 19-slot per-edge queue, exact availability/reset/input gating, and ordered edge/channel additions. This deliberately small oracle does not claim a scalable connectome accumulation method.
- [Qualification suite](tests/test_mlx_core.py) compares independent Brian2 phase monitors plus a spike-derived event ledger with complete MLX state/event traces. Ordinary fixtures require the approved threshold margins, exact discrete parity, state budgets, and bit-identical repeats. The threshold rounding counterexample is an asserted limitation.
- `.venv/bin/python scripts/qualify_mlx_core.py --output data/results/mlx-milestone1-20261004-01`: 40 passed (12 reference, 28 MLX qualification), zero skipped/failures/errors, 251 dependency warnings, 31.79 seconds. [Initial report](docs/evidence/milestone-1/initial-tests.xml), [measurements](docs/evidence/milestone-1/initial-measurements.json), [result](docs/evidence/milestone-1/initial-result.json), and [log](docs/evidence/milestone-1/initial-qualification.log) are preserved. Complete traces remain in the fresh output directory.
- Ruff and Pyright passed for the authored core/qualification runner. The initial run left explicit long-trace repeatability, coincident recurrent delivery, fresh-state pending-queue reset, and large-cancellation coverage to finish; these are closed in the final checkpoint below.

Final qualification checkpoint (2026-10-04):

- Implementation checkpoint `03f5b40` followed dependency pin `af06fa8`. All work remained on `main`; existing numerical runners, comparison tools, data, licences, and public/persisted contracts were preserved.
- `.venv/bin/python scripts/qualify_mlx_core.py --output data/results/mlx-milestone1-20261004-final`: **43 passed** (12 reference and 31 MLX qualification), zero skipped/failures/errors, 256 dependency warnings, 42.81 seconds. [Final result](docs/evidence/milestone-1/final/result.json), [test report](docs/evidence/milestone-1/final/tests.xml), [log](docs/evidence/milestone-1/final/qualification.log), [measurements](docs/evidence/milestone-1/final/measurements.json), and [artifact hashes](docs/evidence/milestone-1/final/manifest.json) are retained. All 19 compressed diagnostic/state/event artifacts are preserved beside them. Earlier fresh output directories remain untouched.
- Six isolated linear cases satisfy the one-step budget. Two complete 10,000-step Metal traces were bit-identical; maximum voltage/synaptic error against Brian2 was **0.000381470/0.000218289 mV**, within the fixed trajectory budgets. [Complete linear traces](docs/evidence/milestone-1/final/linear-10000.npz).
- Every ordinary firing-network case satisfies state bounds at pre-threshold, pre-reset/post-input, and end phases, safe reference threshold margins, and exact spikes, availability, last-spike steps, due/accepted/discarded events, channel decisions, and per-edge pending queues. Each was repeated bit for bit. Maximum recorded phase-state error among these cases was **0.000045944 mV**; no timing or discrete-state tolerance was used.
- Coverage includes rest/empty output, exact reset/freeze, strict equality/neighbor predicates, excitation/inhibition, balanced and duplicate-edge fan-in, 32 simultaneous edges, fan-out/self-delay/multiple wraps, refractory loss/release and release-at-arrival, same-step recurrent loss at ordinary and zero refractory durations, outgoing-only silencing with retained incoming activity/spiking, overlapping channels/zero-rate activation, trial reset, chunked continuation, and standalone-vs-batched independent trials.
- The 1,000-step retained schedule has the approved byte hash and duration prefix; the 43-spike MLX replay meets the complete retained Brian2 state/discrete evidence as well as independent live phase monitors. Three batched trials match individually initialized trials bit for bit. Chunk boundaries preserve pending edges and state exactly. [Replay evidence](docs/evidence/milestone-1/final/retained-replay.npz), [batch evidence](docs/evidence/milestone-1/final/batched-trials.npz), [chunk evidence](docs/evidence/milestone-1/final/chunked-continuation.npz).
- The quarter-unit-in-the-last-place threshold case explicitly asserts the approved precision-dependent spike difference. The 4,097-event cancellation diagnostic is also an **asserted limitation**, outside the ordinary envelope: ordered serial float32 and `mx.sum` both yield **0.25 mV** versus **0.275 mV**, exceeding **0.00100275 mV**. Interleaved serial addition yields 0.275000006 mV, demonstrating order sensitivity rather than approving a general accumulation method. [Raw accumulation evidence](docs/evidence/milestone-1/final/accumulation-limit.npz). Passing these diagnostic assertions does not mean the adverse numerical case passed parity.
- `.venv/bin/ruff check code/mlx_core.py tests/test_mlx_core.py scripts/qualify_mlx_core.py` passed; `.venv/bin/pyright` passed strict checks for the authored core/runner; `UV_CACHE_DIR="$PWD/.uv-cache" uv pip check --python .venv/bin/python` confirmed all 41 installed packages are compatible. Authored diffs passed whitespace checks. Existing numerical source/data match the upstream pin.
- The core keeps neural state and propagation on explicit Metal streams, with host-only setup/coefficient construction and integer loop control. Qualification collects traces after execution; its per-step synchronization is for correctness evidence and makes no throughput claim. No compilation, custom kernel, connectome load, public MLX command, production output, full-network parity, clean installation, or performance result is claimed.

## Accumulation-design handoff

Status: reopened by the user's request to attempt the preferred passing-strategy outcome. The same manually assigned Astra owner is continuing; no review agent or parent-model switch is involved. A factored-scale prototype passes the scalar gates; firing-network qualification and the final design decision are in progress.

Milestone 1 is complete at `52f8427`. The [bounded accumulation review](docs/handoffs/astra-accumulation-design.md#decision-record--concluded-with-blocker) records the candidate reduction, failed alternatives, exact casting blocker, conditional representation guidance, and next audit. A production accumulation design must meet the existing budgets before choosing a full-connectome propagation representation. No custom kernel, tolerance waiver, backend integration, or full-data benchmark is approved by this handoff.

Review diagnostic checkpoint (2026-10-04):

- Incoming checkpoint `1757aa8`, clean `main`. Active session metadata confirms GPT-6 Astra at `xhigh`; no model substitution or review agent was used.
- `MLX_ENABLE_TF32=0 .venv/bin/python scripts/probe_mlx_accumulation.py --output data/results/mlx-accumulation-review-20261004-final` completed all diagnostic assertions on the Apple M1 Max Metal device. [Probe](scripts/probe_mlx_accumulation.py), [measurements](docs/evidence/accumulation-review/accumulation.json), and [complete raw inputs/results](docs/evidence/accumulation-review/accumulation.npz) are retained; source and artifact hashes were verified. The initial `-01` output remains intact.
- All **125 scalar diagnostics** produced an exact two-component representation of the sum of their stored float32 inputs and the correctly rounded final float32 sum. High/low components and final results repeated bit for bit and matched independently run, minimally padded standalone reductions. The original adverse case returned **0.2750000059604645 mV** instead of 0.25 mV.
- This is **not an accumulation parity pass**: only **109/125** cases meet the original-weight float64 one-step budget, and **119/125** meet the trajectory budget. All failures are retained individually. In particular, 128 copies of `[2405, -2404, -1]*0.275 mV` have near-zero float64 sum but a **0.003124237060546875 mV** sum after individual float32 weight casts, exceeding the unchanged **0.001 mV** trajectory floor even with exact subsequent addition. Ordinary reductions can accidentally cancel this input error; that does not qualify them.
- Ruff and strict Pyright passed for the new probe. The qualified small core, its existing tests, upstream runners, dependencies, and production contracts are unchanged. The existing 43-test suite was not rerun in this diagnostic-only step; its retained Milestone 1 result is not a test result for this candidate. No full-data loading, custom kernel, compilation, or benchmark was performed.

Decision checkpoint:

- Probe/evidence commit `0084fe0`. The [durable precision record](docs/mlx-port-baseline.md#accumulation-review-reduction-candidate-and-weight-cast-blocker) separates weight-cast error from reduction error and preserves all fixed budgets. The candidate is supported for further diagnostics only; six measured trajectory failures preclude strategy approval. Independent-process repeatability and full propagation remain untested.
- The return condition is met through the documented-blocker branch. After the user's switch, Sol may begin the [precisely specified Milestone 2 host-side input audit](docs/handoffs/astra-accumulation-design.md#exact-next-work-for-sol-milestone-2-input-audit), preserving data and existing numerical code. Mapping, per-source cast-error extrema, and representative pinned-data masks provide evidence for the next bounded numerical decision. The audit cannot dismiss the retained synthetic failures or authorize rollout by itself.
- Final documentation verification: all 138 local links/anchors across the README, milestone, baseline, and handoffs passed. The retained arrays independently reproduced the exact cast-input sums, correctly rounded outputs, and bitwise repeated/standalone comparisons; evidence hashes matched. Ruff, strict Pyright, and `git diff --check` passed. The diff against incoming `1757aa8` for existing core/tests/runners/dependencies is empty. Both review commits remain local because no user-owned push destination is configured.

Reopened review checkpoint (2026-10-04):

- Incoming checkpoint `71400e3` includes the user's new delegation workflow, which explicitly preserves this manual review's owner. The user asked this owner to attempt a passing strategy. The earlier blocker and evidence remain recorded; the next input audit is deferred until this attempt concludes.
- [Factored-scale probe](scripts/probe_mlx_factored_accumulation.py): keep signed integer connectivity exactly in float32, reduce it with the compensated tree, then use compensated products with high/low float32 components of the shared `0.275` scale and combine current synaptic state before final rounding. This tests the factoring alternative already contemplated by the numerical contract. No per-edge extra weight component, float64 device state, tolerance change, or production-core change is introduced.
- `MLX_ENABLE_TF32=0 .venv/bin/python scripts/probe_mlx_factored_accumulation.py --output data/results/mlx-factored-review-20261004-01`: **157/157** scalar cases pass both original-float64 one-step and trajectory budgets, including all retained 125 cases and 32 new cases. Count expansions are exact; repeated components/results and independently sized standalone results are bit-identical. Maximum measured one-step budget fraction is **0.023660**. [Measurements](docs/evidence/factored-accumulation/scalars/factored.json) and [complete scalar inputs/results](docs/evidence/factored-accumulation/scalars/factored.npz) are retained. Ruff and strict Pyright pass for the new probe. This checkpoint does not yet approve firing-network behavior or connectome rollout.

## Milestone 2 — Connectome loading

Status: not started. Read-only mapping and precision audit is the next work after the user's return to Sol; production accumulation and propagation-layout selection remain blocked by the review above.

Acceptance: MLX input arrays are demonstrably equivalent to upstream in neuron count, connection count, identifier-to-index mapping, source/destination orientation, weight scaling, delays, silencing masks, and deterministic checksums. Raw input counts and hashes collected in Milestone 0 are baseline evidence only; no MLX conversion is yet verified.

Prove the mapping before introducing another sparse representation. Follow the [bounded input-audit instructions](docs/handoffs/astra-accumulation-design.md#exact-next-work-for-sol-milestone-2-input-audit). Qualify signed high-fan-in accumulation against original float64 weights and repeatability, including both the retained 4,097-event reduction diagnostic and the new coherent weight-cast failures, without relaxing either budget. The choice of an accurate/repeatable full-network strategy is not yet validated. Prepare the next bounded Astra handoff with actual pinned-data casting evidence before implementing a propagation strategy or changing weight precision.

## Milestone 3 — Backend integration

Status: not started.

Acceptance: the normal command-line interface runs the shortest MLX experiment, consumes existing experiment definitions, avoids CUDA-only imports, writes the existing spike schema, and produces outputs consumable by the analysis tools. Record initialization, compilation, simulation, and collection separately. Preserve device-resident state and avoid complete CPU-device transfers each timestep.

Present and obtain explicit approval for any required application programming interface or database schema change before writing dependent code, as required by `AGENTS.md`.

## Milestone 4 — Full-network parity

Status: not started.

Acceptance: execute the [frozen 52-case matrix and protocol](docs/mlx-port-baseline.md#full-network-acceptance-fixed-before-validation) through Brian2, the pinned PyTorch numerical core with common experiment setup/replay, and MLX. Sugar and p9 cover 0.1/1/10 seconds with five paired trials; silenced sugar and two-class stimulation cover 0.1/1 seconds with five trials; silent controls cover both shorter durations. Repeat each case and execute the specified batch checks.

Every case must satisfy active Jaccard ≥0.95, relative total count error ≤0.02, normalized neuronwise count error ≤0.05, common-support rate correlation ≥0.99 when defined, and one-to-one timing F1 ≥0.95 within 1 ms. MLX must also be no worse than PyTorch on **every** primary metric for that case, with the documented empty/undefined rules. Require deterministic replay and an explained first divergence; aggregate averages cannot rescue failures. These thresholds precede all full-network MLX results. Obtain a bounded Astra parity adjudication if interpretation is required; do not relax the frozen criteria retrospectively.

## Milestone 5 — Complete-brain benchmark and profiling

Status: not started.

Acceptance: the full pinned dataset completes within local memory, preserves approved parity, and has measured load time, first-run compilation, warm simulation, timesteps per second, biological-time/wall-time ratio, peak unified memory, synchronization, and collection overhead.

Profile before optimizing. Candidate experiments include edge-list gather/multiply/scatter-add, `mx.compile`, destination-sorted reduction, active-neuron propagation, and batched independent trials. Sol may perform measured local optimizations that preserve the approved update structure. Sparse representation changes, scientific-operation fusion, update-order changes, and custom Metal kernels require a bounded Astra handoff with regressions defined first. Preserve the correct baseline as an oracle and reject optimizations without material measured improvement.

## Milestone 6 — Reproducibility and upstream preparation

Status: not started.

Acceptance: pinned dependencies, Apple-silicon installation instructions, example commands, benchmark methodology, numerical tolerances, known limitations, licence notices, and focused tests are complete. Execute the documented clean-install/test workflow and prepare a focused upstream-reviewable patch.

Obtain a bounded final Astra scientific review covering contract compliance, test adequacy, claims, benchmark validity, CPU fallback, hidden semantic changes, and the distinction between exact and statistical parity. Sol verifies the returned evidence and applies any precise requested corrections before finalization.

## Milestone 7 — Finalization

Status: not started.

Acceptance: final corrections are applied; the complete approved verification suite has run with no silent skips; all completion requirements above have direct recorded evidence; commits and working tree are understood; and numerical/performance conclusions accurately state their limits. Prepare the final upstream handoff.

## Current checkpoint and constraints

Next work: the current manual Astra owner completes the user's requested second attempt at the preferred accumulation-design outcome. The factored-scale scalar prototype passes; qualify firing-network behavior and finalize the bounded decision before requesting return to Sol. Milestone 1 is complete for its tested envelope; Milestone 2 has not started. The existing qualified core and production contracts remain unchanged.

A private small-network MLX core is qualified within the reviewed envelope. The integrated MLX backend, full-network parity, speed, peak memory, and clean installation remain unverified. Existing simulation results and generated standalone artifacts are preserved. Reruns require a fresh output directory; both harnesses refuse an existing destination.

Delegation setup (2026-10-04): [the versioned bounded subagent skill](skills/bounded-subagent/SKILL.md) is installed through a symlink at `~/.codex/skills/bounded-subagent`, with automatic discovery enabled. At the user's request, model and reasoning effort are resolved from user instructions or project rules rather than fixed in the reusable skill. The bundled `quick_validate.py` passed; the installed link, file contents, and parsed interface metadata were verified. A read-only `gpt-6-astra` subagent at explicit `xhigh` completed the workflow review and four hypothetical dispatch checks: an explicit Sol/high pair, the project's Astra/xhigh pair, missing choices without defaults, and explicitly requested inheritance. It found no material defects. These were instruction/tool-contract checks, not four live dispatches. Sol retains the user's selected `max`; the existing manual assignment and scientific evidence remain with their owner. This setup did not start Milestone 2 or run additional numerical checks.

Git remote `upstream` is the public reference repository. No user-owned push destination has been supplied; local commits have not been pushed. Do not assume permission or write access to the upstream repository.
