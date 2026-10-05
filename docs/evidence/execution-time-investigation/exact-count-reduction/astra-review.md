# Guarded exact count reduction

Fresh-context reviewer `/root/review_exact_count_reduction`, GPT-6 Astra at `xhigh`, checkpoint `7e702c6`. One performance follow-up to the implemented accumulation design; no change to the manual original design review or its ownership. Read-only review, no edits or executions.

Approve implementation/qualification, confidence 98%; adoption remains conditional. Use `mx.sum(counts, axis=-1)` and `mx.zeros_like(count_high)`. Keep every subsequent scale-high/scale-low product, residual, final 16-leaf compensated tree and zero-total initial-state copy unchanged. Keep the original reducer as the selectable oracle.

Guard at preparation: after outgoing-only silencing, every destination's sum of absolute original integer counts is at most 2^24, calculated with safe host integer arithmetic. Include duplicates and every potentially accepted incoming edge. A current net total, active subset or largest single count is insufficient. Retain representation and 2^40 outer validation; use the original reducer outside the new envelope. Future masks remain Boolean and trial axes independent; enforce accumulator dtype/geometry without host-scanning device values.

Every integer partial sum then has magnitude at most 2^24 and is exactly representable in float32. The original tree's high is the exact count and its low is positive zero. The pinned maximum is 69,948. Prepared zeros/padding are positive zero; verify cancellation/native zero signs explicitly. Zero totals must copy initial bits, including negative zero. Do not remove the low-component products, expand the envelope, reassociate external-input additions, or replace the float32 reduction with an unmeasured representation.

Reviewer and parent inspect the retained complete layout: 693,195 exact high counts, positive-zero lows/zero highs, and preserved zero-total initial bits; archive hash matches. The reviewer inspects 157 scalar cases: 132 satisfy the all-count bound; 25 need original fallback, including intentional nonzero count-low cases.

Before enabling, verify below/at/above-bound cases, cancellation, `[2^24,1]` fallback, signed zeros, duplicate/zero/silenced edges, empty/padded targets, Boolean-mask rejection, every high/low/result byte. Run all 157 scalars with explicit mode selection; all 24,576 pinned cases and 99 existing conversion limitations; all 15 complete device bucket widths/masks with repeats, standalone and batched trials, and fresh-process replay. Run applicable scientific/closed-recurrent checks with the candidate active; two fresh complete one-second sugar runs must match oracle native states, spikes, required queues and observer/ledger evidence. Include silenced, empty/overlapping channels, chunking and four trials.

Metal precision remains zero and compilation disabled. Bind selected mode, source, input, build and hardware. Retained oracle bytes/digests can certify exact same-engine equality, but cannot establish cross-engine tolerance. The known sugar timing failure must remain failed if reproduced. All 52 obligations stay open; old nine acceptances do not transfer to a new mode. Measure a representative whole check before claiming whole-run speedup.

[Parent verification and prospective decision](prospective-decision.json); [component evidence](../mlx-components/result.json).
