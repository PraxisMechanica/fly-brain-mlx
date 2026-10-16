# MLX fly-brain milestone

Updated 2026-10-15. Current priority: separate disposable logs from reusable
evidence before resuming the user's tiered-validation and Eon candidate package.
Preserve v783 inputs, production arithmetic, architecture and seven fixtures.

## Evidence lifetime

Only disposable output belongs in `logs/`, which hooks clear after successful
checks. Preserve legacy `.quality-reports/` until classified. Scientific inputs, spikes, native
states, provenance, verification results, reusable caches and unresolved failures
belong in `executions/`, which hooks never delete, even without manifest entries.
Failures use fresh directories. Removing a retention entry cannot delete evidence.
Explicitly finish all verification/reuse consumers before considering its removal.

The tracked historical recovery contains 687 files, 88,331,555 bytes, verified
against every original Git blob at `5f7b0d7`. It lives under
`executions/tiered-validation-20261015/recovered-5f7b0d7`, outside source metrics.
Recovery does not reaccept old numerical modes. Audit compatibility before reruns.
Current verification logs moved from `logs/tiered-review` into that execution
root's `reuse-verification`; the failed exact command log is in `exact-01`.

## Verified scientific state

The twelve accepted sugar cases remain compatible: ten 0.1/1-second cases and
ten-second trials 0/1. Original artifacts, 108 scientific checks, 132 metric gates,
1,488 source comparisons and build identities were rechecked without simulations.
Ten-second trial 0 has 170,752 exact events. Trial 1 has 171,973 events and four
reviewed one-step shifts, first at step 36,217/neuron 106,477.

The source audit covers Eon pin `a3db62f` and Kisame `e417b33`, including every
requested file and six parity pitfalls. Constants agree; dataset, Brian2 version,
delivery masking, channels and accumulation differ.

The independent NumPy64 prototype passed four semantic fixtures and the ordinary
800-neuron/2,803-edge case: 3,138 exact spikes, five propagated spikes and maximum
phase error `2.78e-14 mV`. Its two-class coverage gate failed for zero propagated
spikes. Diagnostic inspection found all eight fast-class targets inhibitory;
a connectivity-based target selection is prospective. No gate was relaxed and no
later-tier simulation launched. Keep the failed inputs and original source hashes.

## Remaining work and holds

1. Finish retention routing, focused hook/cleanup verification and delivery.
2. Complete the exact tier with informative recurrent two-class activity.
3. Compare full-network MLX32 and NumPy64 on fixed input; reuse compatible native
   runs. Record counts, first divergence and causal limits.
4. Price/preregister five experiments with 30 Brian2, 30 MLX-A and 30 independent
   MLX-B trials each. Report z-scores and Eon's metrics with justified thresholds.
5. Replace most of the 52-case campaign, propose retained sentinels, measure
   setup/simulation/memory, and draft the upstream structure/README. Open no PR.

Original estimate: 40–64 hours and 49 GiB; replacement pricing remains pending.
Get explicit approval before any job/campaign expected to exceed two hours.
The separate `pr-split` checkout's prior matrix remains its owner's work; preserve
its sources/process/outputs. This checkout is detached from `1e33d98`. Scientific
completion, prototype adoption and the whole original goal remain unverified.
