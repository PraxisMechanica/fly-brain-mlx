# MLX fly-brain milestone

Updated 2026-10-16. M5 handoff: tracked `handoffs/README.md` and
`handoffs/m5-handoff-20261016.tar.gz`. Next: bounded M5 pilot and campaign price.
Preserve v783 inputs, arithmetic, architecture and seven fixtures.

## Evidence lifetime

Hooks clear disposable `logs/` only. Preserve legacy `.quality-reports/` until
classified. Scientific evidence, failures and caches belong in protected
`executions/`, independently of retention entries. Finish consumers before deletion.
Retention regressions passed; 719 inventoried files survived unchanged. Receipts:
`executions/retention-20261015`.

Recovered 687 files (88,331,555 bytes), verified against Git `5f7b0d7`, in
`executions/tiered-validation-20261015/recovered-5f7b0d7`. Audit compatibility before
reuse; recovery does not reaccept arithmetic. That execution root preserves
`reuse-verification`, the failed `exact-01` fixture and current tier proofs.

## Verified scientific state

Twelve sugar cases remain compatible: ten 0.1/1-second cases and ten-second trials
0/1. Artifacts, 108 scientific checks, 132 metrics, 1,488 source comparisons and
build identities were rechecked without simulation. Ten-second trials have
170,752 exact events and 171,973 events with four reviewed one-step MLX shifts,
respectively; first difference: step 36,217, row 106,477.

Source audit: Eon `a3db62f`, Kisame `e417b33`, all requested files/six pitfalls.
Constants agree; dataset, Brian2, delivery, channels and accumulation differ.

NumPy64/Brian2 passed eight `exact-02` configurations: four connected
800-neuron/2,803-edge cases and four microfixtures. Two-class drive yielded
2,480 spikes/196 propagated; maximum phase error `2.78e-14 mV`. Spikes,
refractory/reset and delivery match. The ensemble remains pending.

Full-network NumPy64 matches Brian2 at one/ten seconds (16,752/171,973 spikes),
including counts, refractory and pending queues. Maximum final voltage error:
`1.61e-12 mV`. MLX matches one second; ten-second shifts preserve counts. The
bound roundoff review agrees with the oracle within `7.11e-15 mV`. Native
results were reused; see `precision-02/03` and `precision-03-review-binding.json`.

## Remaining work and holds

M5 Max/128 GB alone: measure resources, setup/simulation/memory and price 450
one-second trials. The archive contains preregistration, sentinels and Eon
structure/README drafts. Open no PR. After approval, run 30 Brian2/30 MLX-A/30
independent MLX-B trials per experiment; report z-scores/Eon metrics and complete
scientific mode gates. Runner checks passed (19 tests); M5 qualification remains
pending. Provisional compute: 6–13 hours assuming 1.5–2× M1 throughput; actual
speed/storage remain unmeasured. Get explicit approval before work expected over
two hours. The M1 goal is paused. Preserve the separate `pr-split` owner's
sources/process/outputs. Ensemble qualification and final adoption remain pending.
