# MLX fly-brain milestones

This is the authoritative project plan, acceptance criteria, and progress record. Updated 2026-10-04 (Europe/Paris). It consolidates the supplied charter, milestone specification, startup evidence, and subsequent user amendments.

## Objective and execution

Develop a scientifically validated Apple MLX backend for the [Eon Systems fly-brain simulation](https://github.com/eonsystemspbc/fly-brain), preserving the existing FlyWire v783 leaky integrate-and-fire model's numerical behavior, activation and silencing experiments, and output contracts. Run the complete connectome locally on Apple silicon and provide reproducible correctness evidence, measured performance, and verified installation instructions. This is an MLX array-compute project, not an MLX-LM language-model project.

Implementation owner: GPT-6.1 Sol at `xhigh`. The user controls all model switches. Request a bounded handoff to GPT-6 Astra at `xhigh` for scientific interpretation, numerical correctness, or difficult kernel design requiring deeper judgment. Stop for each requested switch and resume from the recorded checkpoint. Astra must request return to Sol when its assigned component is resolved.

Do not implement MaleCNS, new neuron models, plasticity, reinforcement learning, a user interface, or a generalized simulation framework. Do not rewrite upstream architecture or port every existing backend. Optimize only after correctness is established. No custom Metal kernel without profiling evidence. Honor [AGENTS.md](AGENTS.md), including schema approval and database preservation requirements.

## Implementation and evidence rules

The numerical backend varies; the model, experiment definitions, neuron ordering, connection direction, weights, delays, activation, silencing, thresholds, reset, and timestep semantics must remain invariant under the reviewed contract.

- Read and run the reference before adding MLX code. The bounded review selects pinned Brian2 2.8.0 CPU float64 as ground truth; the [reviewed contract](docs/mlx-port-baseline.md#reviewed-discrete-contract) resolves material inconsistencies. Do not blend contradictory backend behavior.
- Extend the existing backend interface with a small validated numerical core. Preserve upstream structure, tools, callers, and unrelated code.
- Generate stochastic stimulus schedules outside the engines and feed identical events to each. Equal seed values across unrelated generators do not prove equal stimuli.
- Keep simulation state resident on the Apple graphics processing unit. Do not transfer complete state to the CPU each timestep. Retain the simple correct implementation as an oracle if optimized kernels are introduced.
- Verify one milestone before proceeding to the next. Update this file after significant steps with exact commands, test results, measured outcomes, unresolved issues, and supporting artifact links. Commit verified work incrementally on `main`.
- Distinguish tolerance-bounded small-network continuous state with exact ordinary-fixture discrete parity from full-network event/statistical parity. Keep the separately asserted threshold-rounding limitation explicit. Do not declare acceptance thresholds after seeing results, explain away discrepancies, or infer scientific validity from a successful run alone.

Each handoff must contain the reason for deeper review, current checkpoint and commits, exact evidence and files to inspect, one bounded requested outcome, and a return condition. The user performs the requested model switch. Astra records decisions and relevant verification, commits any assigned changes, and requests return to GPT-6.1 Sol at `xhigh` before subsequent routine work.

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

Status: resolved. Contract approved for Milestone 1 implementation/qualification; awaiting the user's return to GPT-6.1 Sol at `xhigh`. This is not approval of an MLX implementation or full-network result.

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

Status: not started.

Acceptance: every timestep's voltage and synaptic state meet the [reviewed budgets](docs/mlx-port-baseline.md#reviewed-precision-and-state-acceptance): isolated one-step error ≤`2e-5 + 2e-6*abs(reference)` mV and trajectory error ≤`1e-3 + 1e-5*abs(reference)` mV. Ordinary fixtures require exact spike/reset/refractory/delay-event state, with no timing slack. Test strict equality and neighboring representable values, and assert the separate near-threshold rounding limitation rather than claiming universal float64 spike equivalence. Run every enumerated synthetic case, shared deterministic stimuli, and repeated identical runs without skips.

Start with source indices, destination indices, and weights. Keep model state on the Apple graphics processing unit. Use externally generated stochastic schedules shared with the reference. Do not load the full connectome or add a custom Metal kernel at this milestone.

## Milestone 2 — Connectome loading

Status: not started.

Acceptance: MLX input arrays are demonstrably equivalent to upstream in neuron count, connection count, identifier-to-index mapping, source/destination orientation, weight scaling, delays, silencing masks, and deterministic checksums. Raw input counts and hashes collected in Milestone 0 are baseline evidence only; no MLX conversion is yet verified.

Prove the mapping before introducing another sparse representation. Qualify signed high-fan-in accumulation against float64 and repeatability, including the retained 4,097-event cancellation diagnostic, without relaxing the state budget. The choice of an accurate/repeatable full-network reduction is not yet validated. Representation changes requiring scientific or kernel judgment require a bounded Astra handoff.

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

Obtain a bounded final Astra scientific review covering contract compliance, test adequacy, claims, benchmark validity, CPU fallback, hidden semantic changes, and the distinction between exact and statistical parity. Astra requests return to Sol after approval or precise requested corrections.

## Milestone 7 — Finalization

Status: not started.

Acceptance: final corrections are applied; the complete approved verification suite has run with no silent skips; all completion requirements above have direct recorded evidence; commits and working tree are understood; and numerical/performance conclusions accurately state their limits. Prepare the final upstream handoff.

## Current checkpoint and constraints

Next work: the user returns to **GPT-6.1 Sol at `xhigh`**. Resume from the [completed bounded review](docs/handoffs/astra-numerical-contract.md#return-checkpoint-and-next-action), then begin Milestone 1's small, uncompiled MLX core and qualification suite under the reviewed contract. Stop for the model switch; no implementation in the review turn.

No MLX backend has been written. No MLX parity, speed, peak memory, or installation claim is verified. Existing simulation results and generated standalone artifacts are preserved. Baseline reruns require a fresh output directory; the harness refuses an existing destination.

Git remote `upstream` is the public reference repository. No user-owned push destination has been supplied; local commits have not been pushed. Do not assume permission or write access to the upstream repository.
