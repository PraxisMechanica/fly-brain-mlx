# MLX fly-brain milestone

Updated 2026-10-16. M5 bundle: `handoffs/README.md`. Preserve v783, arithmetic,
architecture and seven fixtures.

## Evidence lifetime

`AGENTS.md` owns retention. Preserve `executions/` and unclassified
`.quality-reports/`. Retention: 719 files unchanged (`executions/retention-20261015`).
Recovered 687 files/88,331,555 bytes verified against `5f7b0d7`:
`executions/tiered-validation-20261015/recovered-5f7b0d7`. That root retains audits
and failures; check compatibility before reuse.

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

M5: 57 transfer files verified. Pilot passed 15 jobs; five one-second Brian2/MLX
pairs match native events/counts; sugar repeats match. Selected qualification:
89 passes, 234 deselected; connectome pulse passed. Receipts:
`executions/m5-pilot-01`, `m5-pilot-check-03`, `m5-local-qualification-01`,
`m5-connectome-pulse-01`.

Pre-repair price (`executions/m5-plan-01`): 445 jobs, 5.83 hours/107.56 GiB,
including 25% and five reused trials. One CPU/one GPU; reserve five CPU cores/
12.8 GiB for macOS, two agents and GPU host work.

Observed sugar stopped before simulation: framework-Python provenance assumption.
Repair binds the actual runtime; verify and refresh the source-bound profile.
Preserve failed `executions/m5-observed-launch-01`. Full-state/ensemble acceptance
remains pending. Latest user authorizes necessary tests without further approval
pauses: retain 30 trials/active cohort, reduce silent to one/cohort (363 jobs).
M5 alone; M1 goal paused; preserve `pr-split`. Eon remains draft; open no PR.
