# Required one-second batch verification decision

Completed read-only review: `/root/review_full_batch_verification`, fresh-context GPT-6 Astra at explicit `xhigh`, assignment `52a8784`. Decision confidence: **99%**, based on source inspection. Astra ran no simulations or tests and changed no files. Sol independently inspected the relevant source and verified the retained actual short-batch evidence before accepting this method.

## Accepted method

Run actual four-trial batches for sugar and P9 at **10,000 steps**, trial identities `(0, 1, 2, 3)`, and repeat each from fresh state. Bind each trial's canonical event bytes, target/rate order, input pins, neuron mapping, source hashes, hardware, versions, precision, compilation mode, and CPU threads to its matching independently verified one-second singleton. Trial 4 remains independent. These batches add no accepted cases to the frozen 52-case matrix.

Use existing MLX `observe`, `core.initial_state(network, 4)`, `EventLedger(..., 4)`, `trial_block`, and `phase_hash`. Require all **313 blocks**, including the final 16 rows. Explicitly reject a wrong ledger shape or any false flag: `observe` records the flags and does not reject them itself. Compare every trial's native phase digest, actual boundary queue digest, each actual due-mask digest, complete spike raster, and final native arrays with its corresponding singleton. All 30 ledger checks cover exact discrete behavior, finiteness, and all 19 physical queue slots.

Execute the unchanged original CPU model with **four rows in its actual matrix multiplication**. Joining four singleton outputs cannot substitute for a batch. Existing `torch_collect.collect` already supports this geometry and fresh-state observation. Require all **10,001 snapshots**, from initial step -1 through 9999, with each trial's digest over native `g`, `delay_buffer`, `spikes`, `v`, and `refrac`, plus full final arrays and spike coordinates. Its physical queue is a float32 neuron-payload buffer. The consumed row is slot zero of the preceding snapshot; signed cancellation prevents inferring original-edge membership from nonzero payloads. Preserve all 19 slots and the existing CPU schedule; do not compare this buffer directly with Brian2's edge queues.

Require bit-identical first/repeat batch native states, phase/queue/due digests, final array dtype/shape/bytes, spikes, and counters. Tolerance cannot rescue a repeat mismatch. A fresh MLX state and ledger are required; CPU `observe` calls `state_init()` for each execution.

Exact native batch/singleton agreement across every block or snapshot, together with complete raster and queue agreement, is sufficient. Bind and reuse the matching independently verified singleton's Brian2 causal evidence. Brian2 remains an independent C++ standalone trial per fresh state; an invented four-trial reference model or repeated reference execution is unnecessary for this exact route.

## Differences remain unresolved until observed

A differing digest proves neither a tolerance pass nor a tolerance failure. Obtain fresh actual batch/singleton observations for every differing block or snapshot, rerun from canonical fresh state unless a checkpoint method is separately qualified, and bind the observations to the original native digests and queue/raster evidence. Matching blocks remain covered by exact digests. Use host float64 for comparison while preserving native precision and shape; MLX/CPU values are already in millivolts and Brian2 native volts are multiplied by 1,000 only for numerical comparison.

Apply the unchanged trajectory bound `1e-3 + 1e-5*abs(x_singleton)` millivolts elementwise to batch/singleton continuous state, including floating CPU queue payloads. Spikes, masks, counters, clocks, event identities, and each engine's reset/freeze invariants remain exact. Record complete coverage, worst error relative to the bound, and first failing context. A same-engine batch/singleton spike difference fails the exact event requirement; the Brian2/MLX explained-roundoff policy cannot waive it.

If MLX batch state differs from its singleton, obtain the affected actual Brian2 phase observations and perform the original causal audit for the batch. Two individually bounded differences do not prove the original Brian2 bound by a triangle inequality. `CausalAudit` alone is not a batch/singleton validator because it stops continuous-state comparison after its first spike difference.

Keep observation memory bounded by the current block and engine state. Write digests incrementally and retain final arrays, spikes, and required discrepancy witnesses. Do not retain full phase/queue histories. One-second memory use is not yet measured.

## Minimum implementation and verified scope

Add an internal MLX batch collector and a batch/singleton verifier around existing observers; reuse CPU collection unchanged. Keep single-case `paired_collect`, `paired_causes`, `case_execution`, and reports intact. Verify complete step/trial coverage, exact native comparison, swapped/missing-trial refusal, and explicit unresolved status for differing digests on the four-trial fixture before full executions.

Sol verifies [all 13 reviewed source hashes](source-verification.json) against `52a8784`. The reviewed sources are `mlx_observer.py`, `mlx_ledger.py`, `paired_observer.py`, `paired_collect.py`, `paired_causes.py`, `torch_observer.py`, `torch_collect.py`, `torch_reference.py`, `replay_evidence.py`, `stimuli.py`, and the numerical `core.py`, `bucketed.py`, and `accumulation.py`.

The [executed parent proof](executed-verification.py) verifies the retained actual 0.1-second four-trial MLX execution against all four now-completed singleton observations. [Verification](parent-verification.json) confirms all 32 native phase/queue/due blocks and all 13 final fields match for each trial, with native dtype/shape/bytes and canonical stimulus identity preserved. This extends the earlier trial-0-only check; it does not supply batch repetition, a CPU batch, the required one-second horizon, or any new case acceptance. The historical memory proof and its original claims remain unchanged.

Accepted engineering decision: proceed with the minimal internal collector/verifier and its fixture qualification. No core, tolerance, model, reference, schema, execution-mode, matrix, or performance change is approved.
