# Bounded bucketed execution review

Assignment: fresh-context `gpt-6-astra` at explicit `xhigh`, task `/root/review_bucketed_execution`, incoming `main` checkpoint `61cb371`. The parent remains Sol. This read-only review concerns the newly implemented bucketed engine; it does not duplicate the completed manual accumulation-design assignment. No source edits, dependency changes, commits, nested agents, or model switches were authorized.

The question was whether actual event gathering, bucket padding, count reduction, neuron-order recovery, integration, receiving, reset, and queue transitions preserve the [selected numerical contract](../../../mlx-port-baseline.md). Evidence supplied: the source, all 79 scientific test results, 55 trace artifacts, complete host mapping, the 24,576 isolated fan-in cases, and the completed 157 adapted scalar cases. Completion required a bounded correctness decision, evidence, limitations, and exact remaining Milestone 2 checks.

## Decision

**The implementation passes the bounded source and numerical review. No blocking correctness defect was found. Milestone 2 remains open until complete pinned-layout and device checks pass.**

The reviewer confirms original edge identities, explicit false padding, the trial axis, unchanged factored reduction and operation sequence, original neuron order, strict threshold, delivery-time receiving, reset/channel order, and the 18-step delay with a 19-slot per-edge queue. Host silencing retains row identities; production counts originate in integer connectivity. Compilation remains disabled and execution uses explicit Metal streams.

## Evidence examined and additional checks

- All 55 trace hashes and four source hashes match. The reviewer rechecks 270 phase/state arrays across 18 bucketed traces against retained references. Fixed budgets and discrete equality pass; greatest phase-state error is `0.000026732656579 mV`.
- Additional read-only Metal checks cover 17 one-hot masks, bucket widths 1/2/4/8, nonidentity target order, empty targets, zero counts, signed-zero copies, and individual versus batched bits.
- A reported 120-step three-trial execution includes duplicate edges, self-connections, outgoing silencing, overlapping channels, and refractory state. Every state/trace array matches the existing factored oracle byte for byte: 180 spikes, 604 due events, 534 accepted, 70 discarded. These extra checks were performed in memory; they do not replace the retained live-reference suite.
- All 157 scalar artifacts and source hashes pass independent checks of accurate/ordered references, both original-state budgets, exact count expansions, zero copies, repeatability, and standalone results. Maximum one-step budget fraction is `0.0236594749621527`. Inputs and output/count-component bits match the retained prototype. The empty negative-zero ordered reference differs in sign from the previously padded reference; numerical values agree and output bits remain correct.

## Parent verification and decision

Sol ran the retained 79-test live qualification and [157-case scalar command](scalars/bucketed-scalars.json), and independently verified all scalar inputs, artifact/source hashes, literal ordered and accurate references, exact count expansions, both budgets, repeats/standalone bits, zero copies, and prototype output/component bits. [Verification](scalars/verification.json). The original numerical oracle is unchanged. Full Ruff, strict Pyright, three import contracts, and 53 application tests pass.

Sol accepts the bounded decision and resumes the required qualification. The reviewer's extra in-memory checks are reported as such; Sol did not repeat that separate 120-step check. No user decision about low-level state precision is required.

## Required next checks and limits

1. Replay all 24,576 prescribed pinned cases through `make_layout`/`accumulate`, with both stored-state one-step and original-state trajectory references, all orders, repeats, standalone count components, and all 99 original-state conversion limitations retained.
2. Verify every complete-device field against the pinned host representation. Compare actual gathered event masks with host predictions across every occupied and padded leaf. Count totals alone cannot establish membership.
3. Execute a complete-connectome pulse. Compare all due/accepted/discarded masks and pending queues at every step; require arrival at `k+18`, first voltage influence at `k+19`, and exact unaffected-neuron state. Preserve silenced/zero-edge identities.
4. Record these results and update the current checkpoint before completing Milestone 2.

The reviewer did not rerun live Brian2, the 79-test suite, or static checks; it inspected retained evidence and performed the stated additional device checks. This decision makes no full-network parity, performance, compilation, production-export, or complete-installation claim.
