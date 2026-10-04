# Bounded numerical preservation review

Completed 2026-10-04 by the fresh-context subagent `/root/review_numerical_preservation`, explicitly using GPT-6 Astra at `xhigh`. The parent remained GPT-6.1 Sol. The assignment was read-only: inspect the architecture refactor for unintended changes to the qualified small-core contract and independent CPU reference semantics. It did not select a new accumulation strategy or duplicate the separate manual review.

Checkpoints: preserved source at `22c813e`; application refactor at `d98f5bf`. The review also inspected the fresh qualification artifacts and explicit precision/propagation wiring in the working tree.

## Decision

**Bounded pass.** The reviewer found no introduced numerical violation that requires correction before the architecture hold can be released.

- Twenty-seven numerical function bodies match after normalization of typing-only edits. Fourteen Brian2 parameters, equations, and the frozen PyTorch parameter table retain their values.
- The explicit execution factory preserves stable edge order, outgoing-only silencing, availability masks, delayed queues, compensated propagation, and reset behavior. It replaces a hidden registry and test monkeypatches without changing the recorded numerical result.
- Brian2 monitors and the event ledger remain independent oracles. The PyTorch reference retains its measured conductance-arrival/voltage-influence steps of 20/21 and its known differences from Brian2.
- Bootstrap sets and validates precision before loading MLX; qualification sets the same policy in its fresh child process. Configuration is injected into network construction.
- The fresh suite records 61 passed, zero failures, errors, or skips. The reviewer independently compared 1,044 arrays in 37 core/network artifacts and the 15 scalar factored arrays with the retained evidence. All array bytes match.
- All 157 factored scalar cases meet the unchanged one-step and trajectory budgets. Repeated and independently sized reductions are bit-identical. All four reference replays are byte-identical, with 43 spikes and the retained stimulus hash.

The parent independently verified [28 source/reference checks](source-preservation.json), [all 1,076 arrays in 39 artifacts, the replay traces, and incoming archive hashes](artifact-preservation.json), the complete test report, and scalar acceptance counts before integrating this decision.

## Limits

This was an evidence review; the reviewer did not rerun execution or install packages. The parent ran the fresh qualification and installation checks. The decision covers numerical preservation during architecture repair. It does not approve full-connectome loading, compiled arithmetic, custom kernels, production spike export, full-network parity, or performance. The retained serial/weight-casting and threshold-rounding limitations remain explicit. The earlier manual accumulation-design review retains its owner and scope.

Completion condition met: record this pass and the fresh scalar results, then complete the remaining application architecture checks before dependent feature development.
