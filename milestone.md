# MLX fly-brain milestone

Updated 2026-10-15. Disposable logs and reusable evidence have separate lifetimes.
Next: price the ensemble campaign and draft Eon packaging.
Preserve v783 inputs, production arithmetic, architecture and seven fixtures.

## Evidence lifetime

Hooks clear only disposable `logs/`. Preserve legacy `.quality-reports/` until
classified. Scientific/reuse/failure evidence and caches belong in `executions/`,
protected without manifest entries. Failures use fresh directories. Removing an
entry cannot delete evidence; finish all consumers before considering removal.

Retention hooks and commit/push regressions pass. All 719 inventoried evidence
files survived unchanged; production source is unchanged. Receipts:
`executions/retention-20261015`.

Recovered 687 tracked files, 88,331,555 bytes, verified against every original Git
blob at `5f7b0d7`, under
`executions/tiered-validation-20261015/recovered-5f7b0d7`, outside source metrics.
Audit compatibility before reuse; recovery does not reaccept old arithmetic.
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

Independent NumPy64 passed eight configurations in `exact-02`: four
800-neuron/2,803-edge cases and four microfixtures. Two-class drive produced
2,480 spikes, including 196 propagated spikes. Maximum phase error is `2.78e-14 mV`.
Spikes, refractory/reset and delivery membership match exactly. Two-class targets
follow positive outgoing contact strength. Keep the failed first fixture.
This qualifies oracle logic; the ensemble tier remains pending.

Full-network NumPy64 matches Brian2 at one second (16,752 spikes) and ten seconds
(171,973), including counts, refractory state and pending queues. Maximum final
voltage error is `1.61e-12 mV`. MLX matches one second exactly; its four one-step
shifts at ten seconds preserve counts. The first difference matches the bound
roundoff review; oracle/context voltage differs by `7.11e-15 mV`.
See `precision-02/03` and `precision-03-review-binding.json`; native results were reused.

## Remaining work and holds

1. Price/preregister five experiments with 30 Brian2, 30 MLX-A and 30 independent
   MLX-B trials each. Report z-scores and Eon's metrics with justified thresholds.
2. Replace most of the 52-case campaign, propose retained sentinels, measure
   setup/simulation/memory, and draft the upstream structure/README. Open no PR.

User amendment: M5 Max/128 GB alone; notify when handoff is ready. Reserve OS
capacity; measure CPU/GPU concurrency instead of fixing 75%. Runner verification
and M5 pilots remain pending. Provisional M5 compute: 6–13 hours, assuming
1.5–2× M1 throughput; actual speed and retained storage remain unmeasured.
Get explicit approval before any job/campaign expected to exceed two hours.
The separate `pr-split` checkout's prior matrix remains its owner's work; preserve
its sources/process/outputs. Ensemble qualification and final adoption remain pending.
The retired assertion is repaired; constant/precision guards and hosted checks pass.
