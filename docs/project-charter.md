# Apple MLX backend for Eon Systems fly-brain

## Status and provenance

This document preserves the useful project specification from the user's pasted planning material. It is a proposed charter, not authorization to begin implementation. The user will supply the active goal separately.

Primary reference: <https://github.com/eonsystemspbc/fly-brain>

The upstream repository has not yet been inspected, fetched, run, or pinned in this workspace. Its capabilities, dataset sizes, command examples, output formats, and licence details below are planning claims to verify during reference work. This workspace is not yet a checkout of the upstream source.

## Initial target and rationale

Start with one backend port for one validated model: the Eon Systems fly-brain implementation using FlyWire v783.

The supplied plan describes upstream as having:

- A canonical Brian2 central processing unit (CPU) implementation used as ground truth.
- Several Compute Unified Device Architecture (CUDA) backends.
- Approximately 138,000 neurons and 5 million synapses from FlyWire v783.
- Shared benchmark inputs and spike-output formats.
- Existing parity-comparison tools.

These existing reference and comparison facilities are the proposed basis for validating MLX.

## Objective and design force

Implement an Apple MLX backend for the repository's whole-brain leaky integrate-and-fire simulation. The backend must reproduce the established Brian2 CPU ground truth closely enough to be scientifically useful and run the full FlyWire v783 connectome on Apple silicon.

This is an MLX array-compute project. It does not use MLX-LM language models.

The numerical backend varies; the neuron model, experiment definitions, connectome ordering, activation and silencing semantics, timestep behavior, delays, and spike-output contract remain invariant. Verify success against the existing Brian2 ground truth and comparison tools.

## First-project scope

- FlyWire v783 only.
- The existing leaky integrate-and-fire model only.
- Activation and silencing experiments already supported upstream.
- One MLX backend integrated into the existing command-line interface (CLI).
- Numerical validation and performance measurement on Apple silicon.

Out of scope:

- MaleCNS v1.0 support.
- New neuron models.
- Plasticity or reinforcement learning.
- User-interface work.
- Rewriting the upstream architecture.
- Porting every CUDA backend.
- Performance optimization before correctness.
- A generalized neural-simulation framework.

## Implementation rules

1. Read and run the reference implementation before writing the MLX backend.
2. Treat Brian2 CPU as numerical ground truth unless evidence shows a documented upstream inconsistency.
3. If existing backends disagree, document the conflict and select one reference. Do not average contradictory behavior.
4. Generate deterministic external stimulus schedules and feed identical schedules to the reference and MLX implementations. Do not assume random number generators produce identical sequences across frameworks.
5. Preserve neuron ordering, connection direction, weights, delays, threshold behavior, reset behavior, activation, silencing, and timestep semantics.
6. Extend the existing backend interface without refactoring unrelated code. Before any application programming interface (API) or database schema change, follow the explicit approval requirements in `AGENTS.md`.
7. Keep MLX state resident on the graphics processing unit (GPU) during simulation. Do not transfer complete state to the CPU every timestep.
8. Add a custom Metal kernel only after profiling proves ordinary MLX operations insufficient.
9. Keep an unoptimized, obviously correct implementation as a regression oracle if an optimized kernel is later introduced.
10. Complete and verify one milestone before starting the next. The supplied plan recommends separate goals for milestones; the proposed first assignment below groups Milestones 0 and 1, to be completed sequentially if selected by the user.
11. After each milestone, report what changed, what was verified, exact commands executed, measured results, and remaining uncertainty.
12. Make a small, descriptive commit after each completed milestone. Follow `AGENTS.md` for branch and push requirements.

## Final success criteria

- `python main.py --mlx --t_run 0.1 --n_run 1` works on Apple silicon.
- The MLX backend writes the same spike-output schema as existing backends.
- Seeded MLX runs are repeatable.
- Small deterministic networks pass precise state-transition tests.
- Full FlyWire v783 runs complete without CPU fallback for synaptic propagation.
- Existing ground-truth comparison tools can compare MLX with Brian2.
- MLX parity with Brian2 is no worse than the existing PyTorch backend's parity, within a documented and justified tolerance.
- Benchmarks separately report initialization, compilation/warm-up, simulation, result collection, peak memory, and steady-state timesteps per second.
- Installation and reproduction instructions work on a clean Apple-silicon environment.

## Milestone 0: Establish the reference

Deliverables:

- Pin the upstream commit.
- Reproduce the smallest Brian2 CPU experiment.
- Identify the exact equations and update order.
- Document timestep, delays, thresholds, reset, activation, silencing, and neuron indexing.
- Record the existing benchmark and output contracts.
- Record the upstream licence implications.
- Produce `docs/mlx-port-baseline.md`.

Acceptance criterion: another engineer could implement the model from that document without guessing.

No MLX implementation in this milestone.

## Milestone 1: Build a tiny MLX numerical kernel

Implement only small synthetic networks covering:

- One isolated neuron demonstrating leak.
- Threshold crossing and reset.
- One excitatory connection.
- One inhibitory connection.
- Multiple inputs arriving simultaneously.
- Fan-out from one source.
- Silenced neurons and connections.
- A deterministic externally supplied spike schedule.

Use a simple coordinate-list representation initially: source indices, destination indices, and weights. Correctness matters more than speed.

Acceptance criterion: every timestep's voltage, spikes, and reset state match a small NumPy or Brian2 oracle within declared tolerances.

## Milestone 2: Port connectome loading

Load the existing FlyWire v783 data without running a full simulation.

Verify:

- Neuron count.
- Connection count.
- Neuron identifier-to-index mapping.
- Source and destination orientation.
- Weight values.
- Silencing masks.
- Checksums or deterministic summaries of converted arrays.

Only introduce compressed sparse row (CSR) or another representation when the full input mapping is proven correct.

Acceptance criterion: the MLX-ready representation is demonstrably equivalent to the upstream representation.

## Milestone 3: Add the backend adapter

Add an MLX runner following the existing backend shape:

- Add `--mlx`.
- Avoid importing CUDA-only dependencies when MLX is selected.
- Accept existing experiment definitions.
- Produce the existing Parquet spike schema.
- Record compilation, simulation, and collection time separately.

Acceptance criterion: a short existing experiment runs through the normal CLI and produces consumable output.

## Milestone 4: Establish numerical parity

Run the same deterministic experiments through Brian2 CPU, PyTorch, and MLX.

Compare:

- Active-neuron overlap.
- Per-neuron firing-rate correlation.
- Total spike-count ratio.
- Spike timing within the upstream tolerance window.
- Repeatability across identical runs.

Long simulations may diverge after tiny floating-point differences cross a threshold. Require strict parity for isolated state transitions and statistical/event parity for full-network runs.

Acceptance criterion: MLX performs at least as well against Brian2 as the existing PyTorch backend, within a predeclared tolerance.

## Milestone 5: Run the complete FlyWire brain

Run the approximately 138,000-neuron, 5-million-synapse model, subject to verification of the actual dataset counts.

Measure:

- Load time.
- First-run compilation time.
- Warm simulation speed.
- Timesteps per second.
- Biological simulation time per wall-clock second.
- Peak unified memory.
- Frequency and volume of CPU-device synchronization.

Acceptance criterion: the full simulation completes locally, stays within available memory, and produces valid parity results.

## Milestone 6: Optimize based on profiling

Only now profile and optimize the dominant cost.

Candidate experiments:

1. Full edge-list propagation using gather, multiply, and scatter-add.
2. Destination-sorted segmented reduction.
3. Sparse active-neuron propagation.
4. `mx.compile` around the timestep function.
5. Batched independent trials.
6. A custom Metal kernel if measured overhead justifies it.

Every optimization must run the same regression suite as the baseline.

Acceptance criterion: a measured improvement with unchanged correctness. Remove optimizations that do not materially help.

## Milestone 7: Make it reproducible and upstream-ready

Finish:

- Apple-silicon installation instructions.
- Pinned dependencies.
- Example commands.
- Benchmark methodology.
- Known numerical differences.
- Known performance limitations.
- Licence notices.
- Focused tests.
- A clean patch suitable for upstream review.

## Deferred follow-on project: MaleCNS v1.0

Only after the first engine is correct should another project add the newer MaleCNS model, described in the supplied plan as approximately 167,000 neurons and 25.6 million synapses. Verify those figures when that project begins.

Begin as a data adapter:

1. Document the MaleCNS schema.
2. Map it into the proven internal representation.
3. Identify genuine semantic differences.
4. Extend the engine only where those differences require it.
5. Repeat small-network, full-network, and performance verification.

This is deferred context, outside the first project.

## Proposed first goal, pending user selection

The original planning material suggested the following first assignment. It is retained for reference and has not been started:

> Complete Milestones 0 and 1 of the MLX fly-brain project only.
>
> Inspect and run the Eon Systems fly-brain reference implementation. Pin the upstream commit and document the exact numerical contract in `docs/mlx-port-baseline.md`. Then implement a minimal Apple MLX leaky integrate-and-fire timestep for synthetic test networks only.
>
> Do not load the full FlyWire connectome, modify the CLI, optimize performance, introduce custom Metal kernels, or port MaleCNS.
>
> The milestone is complete only when deterministic tests cover leak, threshold/reset, excitation, inhibition, simultaneous fan-in, fan-out, and silencing, and compare every timestep against a simple reference implementation.
>
> Report the exact commands, test results, numerical tolerances, unresolved differences, and the next smallest milestone. Commit the verified work, but do not begin full-connectome integration.

The planning material attributes this decomposition to software-design guidance: use a small backend adapter with a validated numerical core rather than a new generalized simulation architecture.
