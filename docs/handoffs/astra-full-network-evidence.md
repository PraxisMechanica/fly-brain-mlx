# Bounded full-network evidence review

Owner: fresh-context GPT-6 Astra at `xhigh`; parent remains GPT-6.1 Sol at the user's selected effort. Read-only review. The earlier manual accumulation assignment is complete and must not be duplicated.

Checkpoint: `42c59f0` on `main`, clean tree before this assignment. Milestones 0–3 are complete within their recorded scope. The normal ten-package installation executes the complete shortest sugar experiment twice with byte-identical schedules and spike files; the complete silent control has zero events. Application/scientific suites have 66/80 passes, zero skips/failures/errors. Full-network scientific parity and complete state/queue repeatability remain open.

## Bounded question

Select the minimum scientifically adequate evidence-capture method for Milestone 4's full-network causal audit and deterministic replay on this 32 GiB Apple M1 Max. It must inspect every relevant neuron/timestep before the first different spike, identify an earlier state-budget violation if present, and preserve actual-engine repeat evidence. Sampling chunk endpoints cannot establish the earliest violation; matching spike files cannot establish complete state/queue repeatability.

Review the following proposed direction before dependent implementation:

- Keep the pinned Brian2 2.8.0 C++ standalone float64 model, original row order/weights, replay placement, compiler flags, and fresh initial state. Preserve the frozen PyTorch CPU core and shared experiment setup/replay. Do not repair or retune either reference.
- Add observers only. For Brian2, consider existing `StateMonitor` objects at pre-threshold and end phases, bounded consecutive `Network.run` chunks, and C++ standalone `insert_code` that emits each completed monitor block through a binary pipe and clears only monitor storage. The parent consumes each block while advancing the existing MLX engine on identical events, and records errors/digests/first-cause evidence. Numerical state, synaptic delivery, and runtime counters must remain untouched.
- MLX retains the qualified update and explicit Metal stream. Capture bounded blocks of actual phase/state arrays and transfer once per block, with per-trial complete state/event/queue checksums and final state. Avoid a complete state transfer every timestep. This is qualification instrumentation, not a replacement production runner or performance claim.
- Prove observer/chunk transparency against uninstrumented Brian2 C++ and MLX on small cases and the complete shortest case before relying on it. State, event, clock, and queue evidence must come from the actual engine where available; distinguish a reconstructed event ledger from an observed runtime queue.
- Alternatives are welcome if smaller and equally complete. A shadow integrator, sampled endpoints, or a raster alone cannot silently substitute for required actual-reference evidence. Specify exactly which observations are necessary and how hidden Brian2 queue state is handled without overstating the proof.

## Fixed requirements and scope

Read `AGENTS.md`, `milestone.md`, and `docs/mlx-port-baseline.md`, especially shared replay, precision/threshold handling, and the frozen 52-case matrix. Every case repeats twice per engine. Sugar/P9 also have four-trial batch checks at one second. All absolute and no-worse-than-PyTorch gates remain unchanged. The original-state conversion limitations remain recorded; their narrow isolated-accumulation exception does not apply to full-network reference semantics.

The reference matrix needs about 1.23 million timesteps per engine before repeats and batches. Complete all-neuron traces over the ten-second cases exceed practical memory/disk limits. The machine has 32 GiB unified memory and about 263 GiB free disk at assignment time. Normal shortest MLX execution takes about 49–52 seconds; this is observed integration timing, not a qualified benchmark. CPU references are optional uv qualification dependencies; MLX remains the sole production backend. No database exists.

Relevant source/evidence:

- `src/fly_brain/qualification/adapters/{brian_reference,brian_replay,replay_probe,torch_reference}.py`.
- `src/fly_brain/simulation/backend/{core,bucketed,runner}.py`, `simulation/{models,experiments,stimuli,storage}.py`.
- `docs/evidence/milestone-0/numerical-contract-replay.npz` and the retained replay/reference records.
- `docs/evidence/milestone-2/buckets/astra-execution-review.md`, device-layout and connectome-pulse evidence.
- `docs/evidence/milestone-3/{integration,production-sugar,production-sugar-repeat,production-silent}`.
- Installed Brian2 source: `.venv/lib/python3.10/site-packages/brian2/devices/cpp_standalone/device.py` and code-generation templates. Use official primary documentation if additional lookup is needed.

## Deliverable and completion

Return one selected approach or one precise unresolved blocker, supported by source locations and narrowly scoped read-only checks. Identify the required observer/chunk transparency tests, minimum fields/phases, repeat/batch evidence, and exact next implementation step. Separate verified API/source facts from hypotheses. Do not edit project files, commit, push, spawn another agent, change acceptance thresholds, implement kernels, or continue the larger project. Stop when this evidence-design question is resolved; do not request a parent-model switch.

Sol independently verifies the cited evidence, records the decision, and commits it before dependent instrumentation. Pure acceptance-metric work remains independent of this bounded review.
