# Initial-state casting decision

Reviewed at `4e91c4241a4f9dba0858aad1386841cff8527100` on 2026-10-04 by fresh-context `/root/review_initial_state_cast`, explicitly GPT-6 Astra at `xhigh`. Read-only; no files changed, packages installed, fresh Metal execution, or suite rerun by the reviewer. The parent remains Sol.

## Decision

The original-state one-step gate remains **failed**. The approved reducer cannot recover initial-state information lost when the state becomes one float32 value. At the review checkpoint, dependent implementation awaited an explicit contract decision. The subsequent [engineering decision](#recorded-engineering-decision) resolves that hold without reclassifying the original failure.

The reviewer independently checked both artifact hashes, all 31 selected targets, the target's rows against the mapped input, its source mask, all three orders/leaves, accurate and ordered references, integer expansions, and repeated result bits. The accepted signed count sum is 2,871. Exact source-function replay with NumPy float32 operations reproduces the saved Metal output word `0xb7cccccd` in all three orders. The result is the correctly rounded float32 value of the accurate stored-state sum.

| Component | Signed error in mV |
| --- | ---: |
| Initial float32 cast | -2.441406240905053e-5 |
| Remaining arithmetic against stored-state reference | -4.2299497238218464e-13 |
| Total against original-state reference | -2.4414062832045502e-5 |
| Allowed absolute difference | 2.0000000000000066e-5 |

The error exceeds the budget by 22.07% and fails against all three ordered original-state references too. The trajectory comparisons pass. Near this initial value, float32 spacing is 6.103515625e-5 mV; the current cast is already nearest. An information-loss check exhibits two original states that map to the same stored value but require disjoint output intervals. A transition receiving only that value and the same events cannot satisfy both. Rounding the event total separately might erase this one cancellation, but changes the approved sequence and does not give a general correction.

The parent independently verified the artifact/result bits, exact error decomposition, correctly rounded stored-state reference, unchanged-budget failure, and a pair of colliding initial states with disjoint required outputs. [Parent verification](parent-verification.json). No failed gate has been reclassified.

## Proposed human decision

Recommended smallest amendment, pending approval **at the review checkpoint**:

> For the isolated high-fan-in audit, apply the unchanged one-step budget to float64 accumulation starting from the identical stored float32 initial state supplied to MLX, using the original float64 weights. Retain every prescribed original state and all original-state accurate and ordered comparisons. Report initial conversion separately, and continue to require the unchanged trajectory budget against the original state. Preserve original-state one-step failures as recorded conversion limitations, never as passes. This exception does not change the other small-network gates or the full-network Brian2 reference.

This was a proposed contract amendment, not an interpretation already allowed by the casting-inclusive rule. The review directed the parent to obtain the human decision before dependent implementation.

If the human retains the original gate, additional initial-state information must instead be authorized and qualified. A low component consumed by the first transition is one possible direction, but changes the current input/state representation and is not approved or qualified by this review.

## Recorded engineering decision

On 2026-10-04 the user reaffirmed that the agent must execute this project using its best engineering judgment and that the user has no opinion on low-level precision choices. This delegates the decision to the implementation owner; it is not a user selection of a numeric representation.

Sol adopts the exact amendment above, supported by the completed Astra review and independent parent verification. Accumulation must meet the unchanged one-step budget against accurate and ordered references starting from the same stored state; conversion remains separately visible. Every original-state comparison is retained, and both original-state trajectory comparisons remain mandatory. The recorded original-state one-step failures remain failures labelled conversion limitations. No arithmetic, tolerance value, event rule, other small-network gate, or full-network criterion changes.

The rationale is that the one-step arithmetic check must compare engines receiving identical representable state. The original-state trajectory check still constrains total error, including conversion. Adding persistent or transient correction state to satisfy a diagnostic starting from unavailable precision would change the implementation without improving the established full-network acceptance requirement. The complete prescribed matrix must now be measured before the selected representation proceeds.

## Limits and next action

The full actual-data target/mask/state/order matrix remains unqualified. No tolerance value, representation, operation order, kernel, or full-network acceptance rule changed. Preserve the original failure and execute the complete matrix with this explicit input-state accounting before implementing the approved bucket representation.
