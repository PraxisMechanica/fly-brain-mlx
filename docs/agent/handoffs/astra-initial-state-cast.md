# Bounded initial-state casting review

Historical review brief. Holds, process states, model-switch instructions, package counts, and remote availability below describe the recorded checkpoint. For current work, read [milestone.md](../../../milestone.md) and [AGENTS.md](../../../AGENTS.md). Original review ownership and scientific evidence are preserved.

Assignment: fresh-context GPT-6 Astra subagent at explicit `xhigh`. Sol retains the parent chat. This is a new failed-gate review after the completed manual accumulation review; it does not duplicate or reassign that owner. Follow [the bounded subagent skill](../history/bounded-subagent.md).

## Checkpoint and question

Architecture release `d834713`; completed manual handoff integrated at `8b7fdb7`; pinned input mapping verified at `d0231a9` on `main`. The new selector and failure artifacts are committed in the review-request checkpoint. Read [project rules](../../../AGENTS.md) and [milestone.md](../../../milestone.md) first.

Resolve whether the unchanged float32 state contract, mandatory original-state cancellation cases, and isolated one-step budget including initial casting can all be satisfied for this measured case. Give a concrete contract-preserving next action, or identify the exact human decision required. Distinguish state conversion error from accumulation error. Do not waive the failed gate or relabel a different reference as accepted without an explicit recorded decision.

## Evidence to inspect

- [Reviewed precision/state contract](../numerical-contract.md#reviewed-precision-and-state-acceptance): isolated one-step `2e-5 + 2e-6*abs(reference)` mV, including initial casting; float32 between-step state.
- [Selected factored design and mandatory actual-data audit](astra-accumulation-design.md#minimal-representation-and-exact-next-milestone-2-work), including the linked older states/masks/orders prescription. Cancellation state is `-fsum(active_weights)` when its magnitude is at most 1024 mV.
- [All selected targets and errors](../../evidence/milestone-2/source-patterns/patterns.json), complete arrays beside it; [selector/source masks](../../../src/fly_brain/qualification/input_patterns.py).
- [Pinned mapping proof](../../evidence/milestone-2/input-mapping/installed-command.json): every original row and both index directions verified; actual counts are exact float32 and within arithmetic guards.
- [Measured failing case](../../evidence/milestone-2/initial-state-cast/initial-cast.json) and `initial-cast.npz` beside it: complete original edges, sources, signed counts, float64 weights, source mask, original/stored initial values, three orders, padded leaves, count components, reference values, actual results, and repeated results.
- [Unchanged approved arithmetic](../../../src/fly_brain/simulation/backend/accumulation.py), retained 157 scalar/61 scientific acceptance results, and [prior preservation review](../../evidence/architecture-remediation/astra-preservation-review.md).

Target 11645 (identifier 720575940611563310), `negative-error` mask: 4,268 incoming edges, 1,998 accepted, absolute accepted-count sum 11,559. Initial float64 state `-789.5250000000001 mV` casts to `-789.5250244140625 mV`. All three Metal orders give `-2.441406286379788e-5 mV`. Original-initial-state accurate reference is `-3.175237850427948e-14 mV`; error `2.4414062832045502e-5 mV` exceeds the one-step floor `2.0000000000000066e-5 mV`. The separately labelled stored-initial-state accurate reference is `-2.441406244080291e-5 mV`, only about `4.23e-13 mV` from the device result. The trajectory budgets pass. Execution uses the pinned MLX/MLX Metal 0.32.3, M1 Max, precision policy zero, and disabled compilation. Repeated results are bit-identical.

## Required outcome and limits

Read-only review. Independently verify the arrays, masks, reference sums, casting decomposition, and source operation sequence as needed. Determine whether a compliant implementation change can remove this error while retaining float32 persistent state and the original specified initial/reference state. If the requirements conflict, explain the conflict and propose the smallest exact clarification/amendment for the human to consider. Keep original-state failure evidence visible and distinguish proposed rules from approved ones.

No implementation, tolerance change, new state representation, custom kernel, full-connectome execution, or performance work. Do not declare actual-data qualification complete: only this decisive case has run, and the full selected matrix remains pending. No model substitution or inherited parent effort. Do not spawn another agent or contact the separate manual chat.

Complete when the parent receives a bounded decision, its supporting checks, limits, and exact next action. Sol verifies and records the result before dependent implementation.
