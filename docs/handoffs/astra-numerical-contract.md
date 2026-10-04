# Bounded Astra numerical-contract review

Status: awaiting the user's switch to GPT-6 Astra at `xhigh`. No review decision is recorded yet. [milestone.md](../../milestone.md) remains authoritative for scope, acceptance, and progress.

## Requested outcome and boundary

Select and document one evidence-supported numerical contract for the Apple MLX port before Milestone 1 implementation. Resolve reference semantics, precision and tolerances, deterministic stimulus placement, and the full-network parity acceptance rule. This is a scientific/numerical review, not an MLX implementation assignment.

The user performs the model switch. Do not substitute another model or spawn a review agent. When the bounded review is resolved, request return to GPT-6.1 Sol at `xhigh` and stop for the user to switch back.

## Checkpoint

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

## Decision record — pending

No authority, precision policy, MLX tolerances, shared-stimulus adapter, or full-network acceptance thresholds have been selected by Astra. Replace this section with the review outcome, supporting evidence, and any precise unresolved probes. Put durable selected semantics in the baseline and acceptance/progress in `milestone.md`; keep this document as the bounded review record rather than duplicating the project plan.

## Return condition

Record the explicit contract and its evidence, or identify the exact additional reference probes needed before approval. Run and preserve relevant verification for any review changes, update `milestone.md`, and commit findings on `main` with a 3–8 word message. Do not claim approval while a required scientific decision is unresolved. Request return to GPT-6.1 Sol at `xhigh` with the checkpoint and next bounded work, then stop for the user's model switch. Sol begins Milestone 1 only after the contract is resolved.
