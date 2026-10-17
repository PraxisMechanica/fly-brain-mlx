# MLX fly-brain milestone

Updated 2026-10-16. Issue #9 tiered M5 singleton validation is complete.
The user authorized necessary tests without further approval pauses.

## Scope and results

This replaces the old 52-case completion plan for the scoped one-second
singleton claim. No additional long campaign is queued. Full-matrix, M5
full-network batch/ten-second and implemented upstream-backend claims remain
outside this scope; their gates remain intact.

Retained evidence: Eon `a3db62f`/Kisame `e417b33` source/six-pitfall audit;
eight NumPy64/Brian2 exact configurations (maximum phase error `2.78e-14 mV`);
full-network one/ten-second precision proof. The ten-second sugar trial1 has
171,973 spikes, identical counts and four reviewed one-step MLX shifts, first
at step 36,217. Historical M1 conclusions retain their original hardware/limits.

M5 passed 323 qualification tests without failures/errors/skips, the connectome
pulse, and five one-second three-engine sentinels with state/queue, paired
metrics and fresh repeats. The standalone-Python provenance failure was repaired;
preserve `executions/m5-observed-launch-01`.

The 363-job campaign completed: 30 independent trials per active experiment/cohort,
plus one silent control/cohort. All prospective gross-error gates passed;
maximum primary absolute statistic `2.240`, zero per-neuron outliers.
Nine of twelve 95% count-ratio intervals fit ±2%. P9 remains unresolved:
MLX-A/Brian2 ratio `0.9028`, interval `[0.8245,0.9910]`; MLX-B/Brian2 ratio `0.9498`,
interval `[0.8571,1.0529]`. Passing alarms does not establish equivalence.

## Cost, evidence and delivery

Campaign: 3.774 active hours/69.45 GiB, versus priced 4.91 hours/86.80 GiB.
Five sentinels: 0.865 hours/4.64 GiB. One CPU/one GPU worker reserved five CPU
cores/12.8 GiB for macOS/two agents/host work. Median whole-loop seconds per
biological second: MLX 50.23–55.91; Brian2 1.72–2.59, plus separately measured
build/setup. MLX singleton throughput is slower. Peak sampled tree RSS:
MLX 3.14 GiB, Brian2 3.69 GiB; MLX allocator 1.35 GiB, a separate scope.

Results: `executions/m5-statistics-01`, `m5-final-report-01`,
`m5-final-review-01`; coverage: `m5-continuation-02/qualification-coverage.json`.
Preserve these, both pilots, all trials/failures, the 57-file baseline bundle,
seven fixtures and original M1 retention/recovery evidence under their owners.
`AGENTS.md` owns retention. M1/`pr-split` remains paused/untouched.
Eon structure/README draft and benchmark CSV/memory sidecar are complete;
open no PR. Pinned arithmetic/data remain unchanged.
