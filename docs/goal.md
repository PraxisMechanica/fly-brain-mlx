Project: Add a correctness-verified Apple MLX backend to Eon Systems fly-brain

Primary reference:
https://github.com/eonsystemspbc/fly-brain

Default execution model:
- GPT-5.6 Sol
- reasoning effort: xhigh

Escalation model:
- GPT-6 Astra
- reasoning effort: xhigh

Objective:
Implement an Apple MLX backend for the repository’s whole-brain leaky
integrate-and-fire simulation. The backend must reproduce the established
Brian2 CPU ground truth closely enough to be scientifically useful and must run
the full FlyWire v783 connectome on Apple silicon.

This is an MLX array-compute project. Do not use MLX-LM.

The numerical backend varies. The neuron model, experiment definitions,
connectome ordering, activation and silencing semantics, timestep behavior,
delays and spike-output contract must remain invariant.

Scope:
- FlyWire v783.
- Existing leaky integrate-and-fire model.
- Existing activation and silencing experiments.
- An MLX backend integrated into the existing command-line interface.
- Numerical validation against Brian2 CPU.
- Performance measurement on Apple silicon.

Out of scope:
- MaleCNS v1.0.
- New neuron models.
- Plasticity or reinforcement learning.
- User-interface work.
- Rewriting the upstream architecture.
- Generalizing this into a new simulation framework.
- Performance optimization before correctness.
- Custom Metal kernels without profiling evidence.

Success criteria:
1. `python main.py --mlx --t_run 0.1 --n_run 1` works on Apple silicon.
2. MLX produces the existing spike-output schema.
3. Seeded runs are repeatable.
4. Small deterministic networks pass state-transition tests.
5. The complete FlyWire v783 model runs without CPU fallback for synaptic
   propagation.
6. Existing comparison tools can compare MLX with Brian2.
7. MLX parity with Brian2 is no worse than the existing PyTorch backend’s
   parity, within a documented tolerance.
8. Benchmarks distinguish initialization, compilation, warm simulation,
   result collection and peak memory.
9. Clean installation and reproduction instructions are verified.

──────────────────────────────────────────────────────────────────────────────
MODEL-HANDOFF PROTOCOL
──────────────────────────────────────────────────────────────────────────────

GPT-5.6 Sol owns routine inspection, implementation, testing, integration,
benchmarking and documentation.

GPT-6 Astra owns bounded decisions where a subtle mistake could produce a
plausible but scientifically incorrect result:

1. Authoritative numerical-contract review.
2. Full-network parity adjudication.
3. Selection or implementation of representation-changing optimizations and
   custom Metal kernels.
4. Final scientific-correctness review.

A model handoff is a stopping boundary, not a suggestion.

When GPT-5.6 Sol reaches an Astra gate:

1. Complete all currently authorized work that does not depend on Astra’s
   judgment.
2. Run and record the relevant tests.
3. Commit the completed work.
4. Write a handoff document under `docs/handoffs/`.
5. Request a handoff to GPT-6 Astra at xhigh reasoning.
6. Stop. Do not begin the gated work under Sol.

Use this exact request format:

HANDOFF REQUEST: GPT-6 Astra, xhigh

Reason:
<why Astra judgment is required>

Current state:
<completed commits, tests and measurements>

Read:
<files and commits Astra must inspect>

Astra deliverable:
<one bounded decision, review or implementation>

Return condition:
<what Astra must complete before requesting return to Sol>

If the environment cannot change models automatically, emit the request
verbatim and wait for the human to change the model. Never claim that a
handoff occurred when it did not.

When GPT-6 Astra completes its bounded component:

1. Write its findings and decisions into the designated handoff document.
2. Make any Astra-owned implementation changes.
3. Run the tests relevant to those changes.
4. Commit the completed work.
5. Request return to GPT-5.6 Sol at xhigh reasoning.
6. Stop. Astra must not absorb subsequent routine milestones.

Use this exact return format:

RETURN REQUEST: GPT-5.6 Sol, xhigh

Astra decision:
<decision and rationale>

Changes:
<files and commits>

Verification:
<commands and results>

Constraints carried forward:
<invariants Sol must preserve>

Next Sol milestone:
<the specific implementation step Sol should execute>

Astra may retain ownership only when a failed verification means its assigned
decision or implementation remains incomplete.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 0 — REFERENCE BASELINE
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Before adding MLX code:

- Pin the upstream commit.
- Run the smallest Brian2 CPU experiment.
- Read the Brian2, PyTorch and orchestration implementations.
- Document the exact equations and operation order.
- Record timestep, delay, threshold, reset, activation and silencing behavior.
- Record neuron ordering and connection direction.
- Document random-number generation and seed behavior.
- Record benchmark fields and spike-output schema.
- Identify any disagreement between existing backends.
- Record licensing implications.
- Produce `docs/mlx-port-baseline.md`.

Acceptance criterion:
The document contains enough information to implement the model without
guessing.

Do not resolve material disagreements between existing backends yourself.
Collect the evidence and proceed to Astra Gate A.

──────────────────────────────────────────────────────────────────────────────
ASTRA GATE A — NUMERICAL CONTRACT
Owner: GPT-6 Astra
──────────────────────────────────────────────────────────────────────────────

Astra must:

- Review `docs/mlx-port-baseline.md` and the relevant reference code.
- Resolve conflicts between Brian2, PyTorch, CUDA and published equations.
- Select the authoritative semantics explicitly.
- Define which properties require exact agreement.
- Define justified floating-point tolerances.
- Define full-network parity metrics and their acceptance rule.
- Record decisions in `docs/handoffs/astra-numerical-contract.md`.

Astra must not implement the MLX backend during this gate.

When the numerical contract is complete, Astra requests return to GPT-5.6 Sol.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 1 — SMALL MLX NUMERICAL KERNEL
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Implement synthetic-network tests for:

- Leak without input.
- Threshold crossing.
- Reset.
- One excitatory connection.
- One inhibitory connection.
- Simultaneous fan-in.
- Fan-out.
- Silencing.
- Deterministic external spike schedules.

Generate stochastic stimulus schedules outside both engines and feed identical
events to the reference and MLX implementations. Do not compare unrelated
random-number-generator streams.

Start with the simplest correct coordinate-list edge representation:
source indices, destination indices and weights.

Acceptance criterion:
Every timestep’s state matches the reference within the Astra-approved
tolerances.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 2 — CONNECTOME LOADING
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Load FlyWire v783 without running the full simulation.

Verify:

- Neuron count.
- Connection count.
- Neuron identifier-to-index mapping.
- Source and destination orientation.
- Weights.
- Delay representation.
- Silencing masks.
- Deterministic checksums or summaries.

Do not introduce a compressed sparse row representation merely because the
PyTorch backend uses one. Choose a representation only after the input mapping
is proven equivalent.

Acceptance criterion:
The MLX-ready representation is demonstrably equivalent to the upstream input.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 3 — BACKEND INTEGRATION
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Add an MLX runner following the existing backend interface:

- Add `--mlx`.
- Avoid importing CUDA-only dependencies when MLX is selected.
- Consume existing experiment definitions.
- Produce the existing Parquet spike schema.
- Record initialization, compilation, simulation and collection separately.
- Keep simulation state resident on the Apple graphics processor.
- Avoid complete CPU-device transfers per timestep.

Acceptance criterion:
A short existing experiment runs through the normal command-line interface and
produces output consumable by existing analysis tools.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 4 — FULL-NETWORK PARITY EVIDENCE
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Run identical experiments through Brian2 CPU, PyTorch and MLX.

Collect:

- Active-neuron overlap.
- Per-neuron firing-rate correlation.
- Total spike-count ratio.
- Spike-time agreement within the approved window.
- Repeatability across identical runs.
- The earliest timestep at which meaningful divergence appears.

Do not explain away discrepancies. Produce measurements and proceed to
Astra Gate B.

──────────────────────────────────────────────────────────────────────────────
ASTRA GATE B — PARITY ADJUDICATION
Owner: GPT-6 Astra
──────────────────────────────────────────────────────────────────────────────

Astra must determine whether:

- MLX satisfies the numerical contract.
- A difference is normal floating-point threshold sensitivity.
- A difference exposes a semantic or indexing defect.
- The approved tolerances need correction based on evidence.
- Additional focused tests are required.

If defects exist, Astra should specify the smallest corrective changes. Astra
may implement a fix only when diagnosis and correction cannot be separated
safely.

Record the decision in `docs/handoffs/astra-parity-review.md`.

Acceptance criterion:
Astra either approves parity or identifies concrete failing invariants and
required corrections.

After approval or bounded correction, Astra requests return to GPT-5.6 Sol.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 5 — COMPLETE-BRAIN BENCHMARK
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Run the complete FlyWire v783 model and measure:

- Load time.
- First-run compilation time.
- Warm simulation time.
- Timesteps per second.
- Biological time simulated per wall-clock second.
- Peak unified memory.
- CPU-device synchronization.
- Result-collection overhead.

Profile before proposing optimizations.

Acceptance criterion:
The full simulation completes, stays within available memory and preserves the
approved parity.

If ordinary MLX operations are adequate, continue with measured, local
optimizations under Sol.

If profiling suggests changing sparse representation, changing update order,
fusing scientific operations or writing a custom Metal kernel, proceed to
Astra Gate C before making that change.

──────────────────────────────────────────────────────────────────────────────
ASTRA GATE C — HIGH-RISK OPTIMIZATION
Owner: GPT-6 Astra
Conditional: enter only when profiling justifies it
──────────────────────────────────────────────────────────────────────────────

Astra must:

- Review the profile rather than speculate.
- Select the smallest optimization addressing the measured bottleneck.
- State which numerical invariants could be affected.
- Define regression tests before changing the implementation.
- Decide between:
  - compiled ordinary MLX operations;
  - destination-sorted segmented reduction;
  - active-neuron sparse propagation;
  - batched independent trials;
  - a custom Metal kernel.

Astra owns implementation of a custom Metal kernel or any optimization that
changes the numerical update structure.

The original correct backend must remain available as a regression oracle.

Acceptance criterion:
The optimization demonstrates a material measured improvement and passes the
same numerical-parity suite.

Record the decision and results in
`docs/handoffs/astra-optimization-review.md`, then request return to
GPT-5.6 Sol.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 6 — REPRODUCIBILITY AND UPSTREAM PREPARATION
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

Complete:

- Apple-silicon installation instructions.
- Pinned dependencies consistent with repository conventions.
- Example commands.
- Benchmark methodology.
- Numerical-tolerance documentation.
- Known limitations.
- Licence notices.
- Focused tests.
- A clean upstream-reviewable patch.

Run the documented clean-install and test workflow.

Then proceed to Astra Gate D.

──────────────────────────────────────────────────────────────────────────────
ASTRA GATE D — FINAL SCIENTIFIC REVIEW
Owner: GPT-6 Astra
──────────────────────────────────────────────────────────────────────────────

Astra performs a final review limited to:

- Numerical-contract compliance.
- Test adequacy.
- Unsupported scientific claims.
- Benchmark validity.
- Accidental CPU fallback.
- Hidden changes to update semantics.
- Whether the documentation distinguishes exact parity from statistical
  parity.

Astra should not broaden scope or refactor unrelated code.

Record findings in `docs/handoffs/astra-final-review.md`.

If corrections are required, identify exact actionable changes and request
return to GPT-5.6 Sol.

If approved, record approval and still request return to GPT-5.6 Sol so Sol can
apply routine corrections, run the final verification suite and prepare the
final handoff.

──────────────────────────────────────────────────────────────────────────────
MILESTONE 7 — FINALIZATION
Owner: GPT-5.6 Sol
──────────────────────────────────────────────────────────────────────────────

- Apply any final Astra-requested corrections.
- Run the complete approved verification suite.
- Confirm no test was silently skipped.
- Confirm the working tree and commits are understood.
- Summarize performance and numerical results without overstating them.
- Prepare the work for upstream submission.

The project is complete only when every success criterion is satisfied or an
unresolved criterion is explicitly reported as incomplete.