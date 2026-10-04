# Bounded Astra accumulation-design review

Status: requested; awaiting the user's switch to GPT-6 Astra at `xhigh`. No accumulation design has been selected or approved. [milestone.md](../../milestone.md) owns the project plan and acceptance status.

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
| [Private core](../../code/mlx_core.py) | Current ordered per-edge device additions, per-edge Boolean delayed-event queue, and exact write gating |
| [Qualification source](../../tests/test_mlx_core.py) | `test_large_cancellation_is_an_asserted_accumulation_limit_not_a_parity_pass`, independent reference phases, and ordinary qualification cases |
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

Use the existing environment and locked requirements. The reproduction command for the current suite is:

```sh
.venv/bin/python scripts/qualify_mlx_core.py --output data/results/<fresh-review-directory>
```

Do not weaken acceptance to accommodate an unsuccessful prototype. If ordinary operations cannot satisfy the fixed requirements, record precise failed candidates and the next evidence needed for a separately bounded kernel review.

## Decision record — pending

Replace this section with the selected strategy, alternatives examined, commands/results, diagnostic artifacts, limitations, and exact implementation/qualification instructions for Sol. Put durable numerical decisions in the baseline and progress/acceptance in `milestone.md`; keep this as the bounded review record.

## Return condition

The accumulation strategy and its numerical evidence are explicit, or an exact remaining blocker/probe is documented without claiming approval. Commit assigned findings/probes on `main`, update `milestone.md`, and request return to GPT-6.1 Sol at `xhigh` with the checkpoint and next action. Stop for the user to switch. Preserve existing data and outputs; no database deletion or public/persisted schema change is authorized by this review.
