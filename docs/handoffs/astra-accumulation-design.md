# Bounded Astra accumulation-design review

Current architecture note (2026-10-04): numerical statements and measured historical commands below retain their original scope. Source links now resolve to the installed package or the retired-source record. Use the current uv commands in [README](../../README.md) for reproduction; the standalone scripts and Conda workflows are retired. The architecture hold and later milestones are governed by [milestone.md](../../milestone.md). This note does not change scientific limits or the manual review's owner.

Status: bounded review concluded with a measured input-precision blocker. The compensated tree is a supported diagnostic candidate, **not an approved full-connectome accumulation strategy**. Return to GPT-6.1 Sol at `xhigh` for the precisely bounded input audit below. [milestone.md](../../milestone.md) owns the project plan and acceptance status.

## Requested outcome

Select an accurate, deterministic float32 accumulation strategy for future full-connectome synaptic propagation, supported by finite Metal diagnostics under the existing numerical contract. The measured ordinary operations fail the retained adverse example. Resolve this numerical/representation judgment before Sol chooses a connectome propagation layout.

Keep the review bounded to the accumulation strategy and its qualification plan. Add only small standalone diagnostic prototypes/tests if needed. Leave the qualified small core and all upstream runners unchanged. Full-data loading, backend integration, optimization, and complete-brain benchmarking belong to later milestones. A custom Metal kernel is not approved without the profiling evidence required by the project plan.

The user controls models. Do not switch/substitute models or spawn a review agent. Once resolved, request return to GPT-6.1 Sol at `xhigh` and stop for the user's switch.

## Checkpoint and evidence

- Branch `main`; Milestone 1 completion commit **`52f8427`**, following initial core `03f5b40`, dependency pin `af06fa8`, and reviewed contract `4fcb224`.
- Upstream pin `a3db62f9436074e485c0278290c2164ed6150808`; existing numerical source, data, licences, and public/persisted contracts are unchanged.
- Private uncompiled Metal core is qualified only within the approved small-network envelope. Final suite: **43 passed**, zero skipped/failures/errors, 256 dependency warnings, 42.81 seconds. Ordinary phase states meet fixed budgets; discrete/event state and repeated traces are exact.
- MLX/MLX-Metal 0.32.3, NumPy 1.26.4, Brian2 2.8.0, Python 3.10.14; Apple M1 Max, macOS 15.3.1; `MLX_ENABLE_TF32=0`. The sandbox hides Metal, so actual GPU diagnostic execution needs authorized access outside it. CPU fallback is unsupported.
- Milestone 2 has not started. No integrated MLX backend, full-network parity, clean installation, performance, or compilation result is claimed. No user-owned push destination is configured; commits remain local.

Read [AGENTS.md](../../AGENTS.md), [milestone.md](../../milestone.md), and the [reviewed precision/accumulation contract](../mlx-port-baseline.md#reviewed-precision-and-state-acceptance), then inspect:

| Evidence | Purpose |
| --- | --- |
| [Private core](../../src/fly_brain/simulation/backend/core.py) | Current ordered per-edge device additions, per-edge Boolean delayed-event queue, and exact write gating |
| [Qualification source](../../tests/qualification/test_mlx_core.py) | `test_large_cancellation_is_an_asserted_accumulation_limit_not_a_parity_pass`, independent reference phases, and ordinary qualification cases |
| [Measured outcomes](../evidence/milestone-1/final/measurements.json) | Actual Metal values, fixed budget, repeatability, and rounding-scale diagnostic |
| [Raw cancellation weights](../evidence/milestone-1/final/accumulation-limit.npz) | Complete ordered and interleaved float64 source weights |
| [Final report](../evidence/milestone-1/final/tests.xml), [result](../evidence/milestone-1/final/result.json), [artifact hashes](../evidence/milestone-1/final/manifest.json) | Verification provenance and preserved complete small-network traces |
| [Original numerical review](astra-numerical-contract.md) | Resolved model semantics and the explicit high-fan-in qualification requirement |

## Concrete failure to resolve

The retained example has 4,097 events with signed connectivity `[2405 repeated 2048, 1, -2405 repeated 2048]`. Edge weights are connectivity times 0.275 mV, constructed in host float64 and cast once to float32.

| Accumulation | Measured result |
| --- | --- |
| Exact real sum | 0.275 mV |
| Ordered serial Metal float32 | 0.25 mV; repeated bit-identically |
| Ordinary `mx.sum` | 0.25 mV |
| Interleaved serial Metal float32 | 0.2750000059604645 mV |
| Allowed trajectory error at this result | 0.00100275 mV |

The ordered/library error is 0.025 mV, exceeding the budget. Interleaving demonstrates order sensitivity; it does not select a general reduction or prove accuracy for actual fan-in. `sum(abs(weights))=2708992.275 mV` and the retained rounding-scale diagnostic do not enlarge the tolerance. The diagnostic test asserts this limitation; its passing status is not parity approval for this case.

## Required decisions and verification

1. Choose a deterministic accumulation strategy using supported full-float32 MLX operations where feasible. Specify reduction order, float32 accumulator state (including any correction components), target grouping, and how a fixed configuration reproduces identical results. Compare against float64 and the reviewed budgets; distinguish individual weight-cast error from reduction error.
2. Preserve direction, signed weights, duplicate edges/event multiplicity, due steps, silencing, threshold/reset order, and discarded-event decisions. Specify the minimal future representation Sol should implement and exactly which existing numerical invariants its conversion must prove. Do not silently coalesce events or change thresholds, amplitudes, precision policy, stimulus timing, or tolerances.
3. Run finite synthetic diagnostics covering the retained adverse ordering, balanced/unbalanced mixed signs, different event counts/orders, zeros/silenced weights, repeated runs, and standalone-vs-batched execution. Require every scalar result to meet the unchanged bound; no mean-error rescue. Reordering/compensation is a candidate requiring evidence, not an automatic approval. Preserve outputs in fresh destinations.
4. Define the exact next Milestone 2 qualification, including representative signed fan-in patterns from the pinned data, comparison against float64, repeatability, and regression of the entire small-network suite after any core replacement. This review can approve a design supported by finite evidence; it cannot declare the unloaded connectome or a future implementation qualified.

Use the single uv project and lockfile. The reproduction command for the current suite is:

```sh
uv run --locked --group qualification fly-brain qualify --output data/results/<fresh-review-directory>
```

Do not weaken acceptance to accommodate an unsuccessful prototype. If ordinary operations cannot satisfy the fixed requirements, record precise failed candidates and the next evidence needed for a separately bounded kernel review.

## Decision record — concluded with blocker

Review date: 2026-10-04. Incoming `main` checkpoint `1757aa8`; probe/evidence commit `0084fe0`. Session metadata confirmed GPT-6 Astra at `xhigh`. No model was substituted and no agent was spawned.

**Decision:** an uncompiled, fixed adjacent-pair tree with two float32 accumulator components resolves the retained reduction failure. It cannot qualify the complete strategy under the existing single-cast weight policy: accurate addition exposes a separate, measurable weight-cast error. Do not implement a production propagation layout or replace the qualified core yet. The return condition permits an exact blocker; no tolerance, fixture, or precision rule is waived to manufacture approval.

### Diagnostic candidate and ordering

The [standalone probe](../../src/fly_brain/qualification/adapters/accumulation_probe.py) implements `two_sum(a,b)` as:

```text
s = float32(a+b)
z = float32(s-a)
e = float32(float32(a-float32(s-z)) + float32(b-z))
```

`TwoSum` preserves the rounding residual of two inputs under its arithmetic assumptions; see [Ogita, Rump and Oishi, Algorithm 3.1](https://www.tuhh.de/ti3/paper/rump/OgRuOi05.pdf). This does not prove the whole tree exact: its correction merges also round. The measurements below test that tree directly.

For each destination/trial, leaf zero is the current post-integration synaptic state, followed by each accepted incoming weight in its fixed edge order. Blocked events and padding contribute zero. Pad to a power of two; set every leaf's low component to zero. Merge adjacent nodes left to right at each level:

```text
(s,e) = TwoSum(left.high, right.high)
c = float32(float32(left.low + right.low) + e)
(high,low) = TwoSum(s,c)
```

Round `high+low` only at the root to produce float32 synaptic state. Correction components are temporary accumulation state, not extra precision carried between timesteps. Including existing state in the tree matters; collapsing an event sum before adding it to an oppositely signed state is a distinct, unqualified operation sequence.

Every array operation runs on an explicit Metal stream. Host work constructs inputs, float64 references, and evidence only. The probe disables `mx.compile`; [MLX compilation](https://ml-explore.github.io/mlx/build/html/usage/compile.html) fuses and optimizes graphs, so this evidence does not approve reassociation or compilation of the residual formulas. No atomics, generic reduction inside the compensated tree, custom kernel, half precision, or hidden CPU propagation is used. `MLX_ENABLE_TF32=0` remains required by the [MLX precision guidance](https://ml-explore.github.io/mlx/build/html/usage/precision.html).

### Finite results and failed alternatives

Command:

```sh
MLX_ENABLE_TF32=0 .venv/bin/python scripts/probe_mlx_accumulation.py --output data/results/mlx-accumulation-review-20261004-final
```

All diagnostic assertions completed on the pinned MLX 0.32.3 / Apple M1 Max environment. [Measurements](../evidence/accumulation-review/accumulation.json) and [complete inputs, masks, references, components and outputs](../evidence/accumulation-review/accumulation.npz) are retained, with source/artifact hashes. The initial `-01` output remains untouched. This is a 125-case diagnostic, not 125 passing scientific-parity tests.

Coverage: the retained ordering, reversal, interleaving and seeded permutation; 17 size points from zero to 8,193, including power-of-two boundaries; balanced paired inputs up to 16,386 events; positive/negative and unbalanced signs; masked/silenced and all-blocked inputs; pre-existing state; and coherent weight-cast drift at 3/96/384/6,144 events in three orders. Synthetic randomness uses NumPy's explicitly selected PCG64 (permuted congruential) generator with seed `20261004`. The file retains the exact generated arrays.

- All 125 high/low expansions equal the float64 accurate sum of the **stored** float32 inputs in these diagnostics; all final values equal its correctly rounded float32 value. Both components and final values repeat bit for bit. Independently evaluated standalone rows with their minimum power-of-two widths match the common-width batch, including all-blocked state preservation.
- Against the **original** float64 inputs, only 109/125 satisfy the unchanged one-step budget and 119/125 satisfy the trajectory budget. Each comparison checks both `math.fsum` and ordered float64 addition, with every failure reported. The accurate sum of cast inputs is an error-decomposition reference, not a substitute scientific reference.
- Original ordering: compensated `0.2750000059604645 mV`; ordinary pairwise tree and library sum both `0.25 mV`. The seeded permutation gives `0.2734375 mV` for the ordinary methods. Interleaving helps particular reductions but does not qualify a strategy.
- Most decisively, `[2405,-2404,-1]*0.275` has an original float64 sum near zero, but its once-cast weights sum to `0.00002440810203552246 mV`. Even this three-event case exceeds the `0.00002 mV` one-step floor. Repeating it 128 times gives `0.003124237060546875 mV`, exceeding the `0.001 mV` trajectory floor; 2,048 copies give `0.04998779296875 mV`. These errors persist under the compensated reducer in every tested order. Ordinary reductions sometimes erase the cast error accidentally, and fail elsewhere; such cancellation cannot establish correctness.
- Four existing-state cancellation cases also exceed the one-step budget because a single cast weight has lost more precision than the final near-zero result permits. No reducer of the same stored values fixes that loss merely by summing more accurately.

Ruff and strict Pyright pass for the probe. Source/artifact hashes and copied evidence were verified. No core or existing test changed, so the 43-test simulation suite was not rerun; its prior result applies only to the unchanged qualified core. No full-data loading, end-to-end propagation, compilation, independent-process repeat, performance test, or custom-kernel profiling was performed. Same-process repeated evaluations and standalone/batched comparisons are the repeatability evidence here.

### Representation guidance, conditional on resolving the blocker

The smallest candidate layout is a stable permutation of original edge rows grouped by destination. Keep original edge IDs, source/destination indices, signed connectivity, and host float64 weights in conversion evidence. Within each target retain original row order and all duplicates. Targets may be bucketed by `next_power_of_two(in_degree+1)` to avoid padding every target to the global maximum. Leaf zero holds current state; one leaf per edge preserves multiplicity; remaining leaves are explicit padding. A fixed bucket layout and tree order must be independent of trial batching, active-event density, and scheduling.

This is guidance for a later reviewed candidate, not permission to implement the production layout now. Do not coalesce duplicate edges, omit zero/silenced events from the event ledger, factor the weight scale, or introduce weight-residual components as an unrecorded change. Keep the current delay representation until a separately verified change is needed. Exact due/accepted/discarded masks are determined by the existing schedule before reduction; unavailable and firing neurons must preserve the approved freeze/reset behavior. Outgoing-only silencing changes weights, not spike emission or incoming acceptance.

### Exact next work for Sol: Milestone 2 input audit

After the user's model switch, Sol may start **read-only host-side mapping and precision evidence**, writing only fresh diagnostic outputs and documentation. Do not change the numerical core or public/persisted contracts. This audit provides the missing evidence for the next bounded numerical decision; it does not make the failed synthetic cases pass.

1. Revalidate both pinned input hashes and counts, int64 identifier order, identifier/index consistency, source/destination orientation, signed integer connectivity, duplicate rows, zeros, and once-cast weights against upstream construction. Preserve a reversible original-row permutation and deterministic checksums. Report minimum/maximum signed connectivity, incoming edge degree, and per-target absolute weight sum. Loading actual data belongs to this next milestone, not this review.
2. For every edge compute `e_i=float64(float32(w_i))-w_i` from the authoritative host float64 weight. Report per-target sums of positive/negative errors and absolute errors. Also group errors by **source and destination for audit only**, because duplicate edges from one source share one due spike. For each target, summing positive source-group errors and summing negative ones gives achievable extrema over source-subset masks, assuming those sources spike together; preserve the corresponding masks. This grouping must not coalesce production events. Apply outgoing silencing before the same audit when validating a silenced case.
3. Select the union of the 16 targets with greatest degree, greatest absolute weight sum, greatest positive cast-error extremum, and greatest negative-error magnitude; include the first target by index at degree quantiles 0/50/90/99/100 percent using NumPy `quantile(..., method='nearest')`. Resolve ties by neuron index and record exact IDs. For each, test no events, all sources, sources with positive/negative total incoming weight, both error-extremum masks, and 16 seeded masks at each source probability 0.001/0.01/0.1/0.5. Generate in ascending unique-source order with `PCG64(SeedSequence([20261004,783,target_index,probability_index,replicate]))`, with the last two indices starting at zero. Masks act on sources, preserving all duplicate-edge membership.
4. Replay these arrays through this diagnostic candidate with current state 0 and ±1024 mV, plus a cancellation state `-fsum(active_weights)` when its magnitude is ≤1024 mV. Test original, reversed and seeded-permuted edge order; use `PCG64(SeedSequence([20261004,784,target_index]))` for one fixed permutation per target, independent of masks/states. Preserve inputs/results. Compare original float64 ordered and accurate sums, cast-input accurate sums, and device results separately under both unchanged scalar budgets. Repeat and compare standalone/batched results. Report every scalar failure, not aggregate success rates. A conservative error bound alone is neither a pass nor a failed measured case; evaluate its associated masks and result-dependent budgets.
5. Include the retained 125-case suite, particularly every cast-drift failure, in the next review. Do not dismiss these examples because the pinned data might lack an identical target. Prepare a bounded Astra handoff with the mapping evidence, attainable cast-error patterns, and exact failed cases. The next decision must examine whether exploiting the exact signed connectivity/common scale or explicitly retaining float32 weight residuals can meet all existing gates. Factoring requires the existing numerical qualification; extra weight components require an explicit precision-policy decision. Neither change is approved here. A custom kernel cannot repair input precision simply by adding the same rounded numbers faster, and remains unapproved without profiling.

After a strategy is actually approved and implemented, Milestone 2 must prove every edge/weight/mask mapping and qualify signed fan-in under the fixed budgets. Any core replacement must rerun the entire small-network suite with all ordinary phase-state/discrete, near-threshold, repeated-trace, batching, chunking, and delay-ledger assertions; no skips or silently relaxed comparisons. Full-network statistical acceptance remains a later independent gate.

## Return condition

Met through the **exact remaining blocker** branch: accurate reduction of once-cast weights does not meet all source-reference budgets. Evidence, candidate operation order, limitations, and the next bounded pinned-data audit are explicit. Return to GPT-6.1 Sol at `xhigh` for that audit, then request a new bounded scientific review before selecting or integrating a propagation strategy. Stop for the user's switch. Preserve existing data and outputs; no database deletion or public/persisted schema change is authorized by this review.
