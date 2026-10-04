# Bounded Astra numerical-contract review

Status: bounded review resolved on 2026-10-04. The numerical contract is approved for Milestone 1 implementation/qualification; no MLX implementation or full-network parity has been approved. Awaiting the user's return to GPT-6.1 Sol at `xhigh`. [milestone.md](../../milestone.md) remains authoritative for scope, acceptance, and progress.

## Requested outcome and boundary

Select and document one evidence-supported numerical contract for the Apple MLX port before Milestone 1 implementation. Resolve reference semantics, precision and tolerances, deterministic stimulus placement, and the full-network parity acceptance rule. This is a scientific/numerical review, not an MLX implementation assignment.

The user performs the model switch. Do not substitute another model or spawn a review agent. When the bounded review is resolved, request return to GPT-6.1 Sol at `xhigh` and stop for the user to switch back.

## Incoming checkpoint

- Branch: `main`; upstream pin `a3db62f9436074e485c0278290c2164ed6150808`.
- Source import: `4466b37`; successful reference experiment: `295994b`; document consolidation: `396f169`; reference contract and verification: `5489ae0`.
- Upstream numerical source, data, scripts, environment files, and licences match the pinned tree. No MLX backend or numerical contract has been approved or implemented.
- The full-data Brian2 2.8.0 sugar experiment ran for 0.1 seconds, one trial, at 0.1 ms timesteps: 1,518 spikes and 321 active neurons. This was one unseeded run, not a reproducibility or parity result. Simulation took 1.348 seconds; build took 12.742 seconds; total accounted time was 16.824 seconds.
- Nine focused reference tests passed, zero skipped/failures/errors; 136 dependency warnings. The inspection harness reproduced the retained schedule and delay trace exactly.
- Existing results and generated artifacts remain preserved. Any new output destination must be fresh. No database deletion is authorized.
- No user-owned push remote is configured; commits are local. The public `upstream` remote is a reference source, not an assumed push destination.

## Evidence to inspect

Read the [working rules](../../AGENTS.md), [authoritative milestones](../../milestone.md), and [reference baseline](../mlx-port-baseline.md) first. The baseline links the relevant implementations and explains the measured disagreements.

| Evidence | Purpose |
| --- | --- |
| [Brian2 runner](../../code/run_brian2_cuda.py), [original paper model](../../code/paper-phil-drosophila/model.py), [orchestration](../../code/benchmark.py) | Actual equations, parameters, scheduling declarations, experiment definitions, and silencing |
| [PyTorch runner](../../code/run_pytorch.py) | Existing comparison baseline and its differing integration, delay, stimulus, and refractory behavior |
| [Focused tests](../../tests/test_reference_contract.py), [final test report](../evidence/milestone-0/reference-tests-final.xml) | Executable reference observations and verification results |
| [Schedule and delay trace](../evidence/milestone-0/reference-schedule.json), [inspection harness](../../scripts/inspect_reference_contract.py) | Generated integration/refractory/reset code, schedule, stimulus placement, and cross-backend delay observations |
| [Baseline result](../evidence/milestone-0/brian2-baseline.json), [log](../evidence/milestone-0/brian2-baseline.log), [run harness](../../scripts/run_reference_baseline.py) | Full-data execution, actual output schema, environment, timing boundaries, and reproducible command |
| [Input counts and hashes](../evidence/milestone-0/input-summary.json) | Pinned v783 data size and ordering/weight evidence |
| [Publication equations and provenance](../evidence/milestone-0/publication-source.json) | Continuous model and outgoing-output elimination; original publication used v630 |
| [Spike comparator](../../code/compare_spike_outputs.py), [reference comparator](../../code/compare_backend_to_brian2.py), [ground-truth comparator](../../code/compare_ground_truth.py) | Current metrics, time normalization, timing window, and undefined/empty-metric treatment |

Additional GeNN/NEST source links and licence notices are in the baseline. Review them where needed to resolve a disputed contract; porting those backends is outside this assignment.

## Decisions required

1. **Authority and invariants.** Confirm or reject Brian2 CPU as the authoritative discrete reference with reasons. Resolve outgoing-only silencing versus README/other-backend behavior. Specify the exact integration, threshold strictness, refractory release/frozen state/input loss, delay indexing, spike timestamps, stimulus slot, and reset interaction. Treat the demonstrated reset-local `w=0` behavior as evidence, not an untested synaptic-weight mutation.
2. **Precision and small-network tolerances.** Specify the supported MLX precision strategy and justified absolute/relative bounds for per-timestep states. Define spike/queue/refractory equality requirements, treatment of near-threshold rounding and summation order, and diagnostic cases that expose meaningful errors. The existing 1e-11 mV analytical test bound describes Brian2 float64 observations; it is not an approved MLX float32 tolerance. Request focused precision probes if evidence is insufficient; do not invent successful results.
3. **Common stimuli and repeatability.** Define the externally generated stimulus representation, generation/replay protocol, activation classes/rates, timing placement, and repeatability checks for both reference and MLX. Equal cross-framework seeds alone do not establish identical events. Proposed changes to an application programming interface or persisted output schema must follow the human-approval requirement in `AGENTS.md`; this review does not authorize those changes.
4. **Full-network acceptance before results.** Specify experiment coverage, durations/trials, shared schedules, metric definitions, timing window, undefined/empty cases, and explicit acceptance thresholds. Include the goal's requirement that MLX parity with Brian2 be no worse than PyTorch under the same stimuli. Define how fixed criteria and the paired PyTorch comparison interact, how divergence is localized, and when to reject or investigate a run. Existing comparison-tool heuristic labels are evidence about tooling, not scientific acceptance.

Measured differences motivate this review: Brian2 integrates exactly and applies stimulus after threshold; PyTorch uses Euler integration and applies stimulus before threshold. Their observed recurrent arrival/influence steps are 18/19 versus 20/21. PyTorch's refractory counter does not gate voltage or threshold, and silencing behavior varies across implementations. A plausible spike raster cannot settle these discrepancies.

## Decision record — resolved

Review base: `main` at `6deca27`. Focused diagnostic/evidence commit: `4b7ea63` (`Probe numerical precision and deterministic replay`). All changes in this assignment are documentation, reference tests, and a standalone numerical diagnostic; no upstream backend, interface, output contract, or data has been modified.

The durable specification is in the baseline's [reviewed discrete contract](../mlx-port-baseline.md#reviewed-discrete-contract), [precision policy](../mlx-port-baseline.md#reviewed-precision-and-state-acceptance), [stimulus protocol](../mlx-port-baseline.md#shared-stimuli-and-repeatability-protocol), and [full-network acceptance](../mlx-port-baseline.md#full-network-acceptance-fixed-before-validation). These sections supersede the earlier pending-review language and legacy comparator heuristics.

| Decision | Outcome and evidence |
| --- | --- |
| Authority | Pinned Brian2 2.8.0 CPU float64, exact coupled linear integration, strict threshold, frozen refractory state, threshold-before-input schedule, and outgoing-only silencing. Original model, generated schedule, publication, and direct tests agree; other backends' disagreements are not blended into the port. |
| Same-step gating | Firing immediately disables incoming writes even at zero refractory duration. New pre-reset probes resolve the previous imprecise “overwritten by reset” description. Ordinary release is step 22 after a step-0 spike; delivery at 21 is lost and at 22 is accepted. |
| Delays and time | Exact integer event steps; a spike at `k` delivers at `k+18` after integration and first affects voltage at `k+19`. Spike labels are the current step, not the completed integration endpoint. Queue/refractory/event membership is exact. |
| Precision | MLX float32 in mV with full-precision reductions, host float64 coefficient construction/cast, and reduced-precision matrix operations disabled. One-step bound `2e-5 + 2e-6*abs(reference)` mV; trajectory bound `1e-3 + 1e-5*abs(reference)` mV within the stated small-network envelope. Masks, integer state, reset/freeze rules, and ordinary fixture spike trains remain exact. |
| Threshold limits | Quarter-ULP rounding can change a strict comparison. No threshold epsilon is permitted. Ordinary fixtures require a safe reference margin and exact spikes; a separately asserted rounding counterexample records the limitation. Full-network roundoff classification never waives a metric gate. |
| Accumulation | Order-dependent cancellation is demonstrated. Require deterministic repeatability and measured accuracy; a generic reduction/atomic scatter has no blanket approval. The high-fan-in accumulation implementation must be qualified before Milestone 2 completes. |
| Stimulus | External per-channel Bernoulli bits from pinned NumPy PCG64 generation; fixed step/channel order, independent trial seeds, immutable byte hashes, duplicate-channel preservation, correct replay slot. Brian2 NumPy/C++ replay and native guaranteed-input equivalence are verified. |
| Full-network gate | Freeze the 52-case paired matrix plus repeats/batch checks before results. Require Jaccard ≥0.95, count error ≤0.02, neuronwise normalized error ≤0.05, rate correlation ≥0.99, 1 ms timing F1 ≥0.95, **and** no worse than the pinned PyTorch core on every primary metric/case. Empty/undefined handling and earliest-divergence diagnosis are explicit. |

The [new probe](../../scripts/probe_numerical_contract.py) is a finite diagnostic, not a candidate backend. It runs six uncoupled linear trajectories, a threshold predicate counterexample, a cancellation sum, and a three-neuron reference replay. It neither loads the connectome nor benchmarks it. [Raw numerical findings](../evidence/milestone-0/numerical-contract.json) and [compressed complete replay state/events](../evidence/milestone-0/numerical-contract-replay.npz) are retained. The original four JSON traces, schedule, and two fresh standalone builds remain under `data/results/mlx-numerical-review-20261004`.

Executed verification:

```sh
.venv/bin/python scripts/probe_numerical_contract.py --output data/results/mlx-numerical-review-20261004
.venv/bin/python -m pytest -q tests/test_reference_contract.py --junitxml=docs/evidence/milestone-0/reference-tests-contract-final.xml --disable-warnings
git diff --check
```

- All diagnostic assertions passed. Over 10,000 steps, maximum float32 voltage error was `0.000381470 mV` and synaptic-state error `0.000218289 mV`; these are NumPy precision measurements, not MLX device results.
- Four reference replays were bit-identical across complete state and event traces, including two independently compiled C++ executions; 43 spikes per replay. Their raw trace hashes all equal `8c6bb12955fc88507cb360d3092f0d4b3fe89fd90d0d60de815aea4d8ec2fab2`.
- [Final test report](../evidence/milestone-0/reference-tests-contract-final.xml): 12 passed, zero skipped/failures/errors, 162 dependency warnings, 17.97 seconds. Earlier 11-test and 12-test reports are retained; adding native Poisson input to the pre-reset gating test motivated the final run. Matplotlib cache/font warnings and the setuptools private-function warning appeared during the diagnostic process; neither prevented execution.
- All 92 local document links/Markdown anchors passed verification. The compressed trace and stimulus match all four raw traces and their recorded hashes. Original upstream numerical source/data remain unchanged; `git diff --check` passed.
- The source inspection confirmed Brian2's threshold flag write and integer `timestep` conversion. Official MLX documentation supplied the float64 device restriction and reduced-precision opt-out; links and access date are in the baseline. No MLX dependency was installed in this review.

## Approval boundaries and remaining qualification

No reference-semantic or small-network acceptance decision remains unapproved. Sol can begin Milestone 1 after the user switches back. Approval means that the target and acceptance criteria are fixed, not that the not-yet-written backend meets them.

The following are explicitly **unapproved as implementation/validation results**, with exact evidence still required:

1. Actual MLX precision/device behavior: pin a compatible release and run coefficient, one-step, 10,000-step linear, strict-threshold, reduction, and repeated-run tests in uncompiled mode; qualify compilation separately. No implicit CPU fallback or relaxed bounds.
2. High-fan-in accumulation: test the retained 4,097-event cancellation example and signed fan-in patterns from the pinned data against float64 with the same accuracy/repeatability rules before connectome acceptance. If ordinary operations cannot satisfy them, request a bounded accumulation-design review; no custom kernel or tolerance waiver is preapproved.
3. General small-network parity: implement and run every enumerated case, including fan-out, duplicate edges, multiple delay wraps, inhibition, silencing behavior, class overlap, chunking, and batching. The 12 reference tests are not claimed as the complete Milestone 1 suite.
4. Full-network parity: construct the common-setup replay adapters and execute the frozen matrix, repeatability checks, primary metrics, and divergence audit. No performance or parity outcome is inferred from this review.
5. Public interface/persisted production schema: present the actual current and proposed contracts for human approval before changing them. Shared replay's internal semantics are settled; its future public exposure and empty-output schema policy are not approved by this document. They do not block private in-memory Milestone 1 tests.

No database was opened or deleted by these probes, no existing output was overwritten, and no original source was refactored. Only `upstream` is configured as a reference remote; no user-owned push destination is available. The local commits are retained and the push remains outstanding rather than publishing into the reference repository.

## Return checkpoint and next action

Request the user's switch to **GPT-6.1 Sol at xhigh**, then stop. Resume on `main` at the final review commit reported in chat; read the reviewed baseline sections and `milestone.md`. Next bounded action: Milestone 1's small, uncompiled MLX core and exact-step qualification suite, using the fixed coefficients, event schedule, precision bounds, and reference replay. Do not start full-data loading, integration, optimization, or benchmarking until the corresponding milestone gate is reached.

## Return condition

Record the explicit contract and its evidence, or identify the exact additional reference probes needed before approval. Run and preserve relevant verification for any review changes, update `milestone.md`, and commit findings on `main` with a 3–8 word message. Do not claim approval while a required scientific decision is unresolved. Request return to GPT-6.1 Sol at `xhigh` with the checkpoint and next bounded work, then stop for the user's model switch. Sol begins Milestone 1 only after the contract is resolved.
