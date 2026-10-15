# MLX fly-brain milestone

Updated 2026-10-15. The numerical contract owns scientific acceptance; the agent
index owns document navigation. Git retains earlier checkpoints.

## Scope and execution limits

Continue implementation from the latest `origin/main` in
`/Users/ocasta/.codex/worktrees/pr-split/fly-brain`. Keep production MLX-only on
Apple silicon, uv-managed and database-free. Implementation stays in this chat;
`AGENTS.md` owns the user's failure-only Astra escalation rule.
Preserve pinned inputs, independent references, tolerances and every scientific
acceptance gate.

The development guide owns batching, validation frequency and execution budgets.
Decision: validate complete, diagnosable batches before dependent work; use focused
checks for concrete uncertainties, hooks/CI for routine checks and stable sources
for full qualification. Confidence: 95% at `1105716`.
No new throughput target blocks acceptance.

## Current implementation and evidence

All five experiments, canonical persisted replay, six-column Parquet output,
typed empty output, comparison JSON/CSV, paired collectors and matrix/batch
controllers exist. Channel class/amplitude and qualification source, compiler,
header, input and executable provenance are recorded. The candidate evaluates the
coupled float32 voltage solution using the reviewed host-`expm1` increment,
unchanged `b,c` and old synaptic state. Compensated reduction and uncompiled Metal remain;
the changed evaluation order needs full-network qualification. A source-neuron delay
queue expands to unchanged original edges at delivery.

Current native tests directly verify phase bytes, all 19 queue slots,
due events, faults, repeats, chunks and standalone/batch behavior. The three
independent reference sources, their protection records and all seven independent
regression fixtures retain their reviewed bytes. Required spike columns and
scientific acceptance gates are unchanged.

Current local scientific qualification: **320/320 passed in 245.16 seconds**,
with zero failures/errors/skips. Fixed queue-format consumers verify every native
source slot and original-edge expansion. Earlier failed raw diagnostics remain
retained. Six current audits passed in 240.32 seconds, including both 157-case
scalar paths, both 24,576-case fan-in paths, complete device rows and pulse.
All 223 bound archive hashes were verified under
`executions/implementation-20261014-matrix/local-audits-4af07fb`.

Shared scaling preserves all 2,355 retained arrays across 157 scalar cases exactly.

All five current sugar/1,000-step trials pass with exact Brian2 spikes and fresh
engine repeats: 953.07 seconds combined, maximum 196.25 seconds per case.
The latest engine-free resumption preflight verifies ten retained accepted cases;
its incomplete-matrix exit 1 is preserved. Evidence:
`preflight-increment-02` under the matrix root.

All five one-second sugar trials pass fixed/paired metrics and fresh native
repeats. MLX matches Brian2 activity and per-neuron counts, with timing F1 **1.0**.

| Trial | Brian2/MLX spikes each | First spike difference | Complete execution (seconds) |
| --- | ---: | --- | ---: |
| 0 | 16,752 | Step 9588, neuron 10133 | 1,447.08 |
| 1 | 17,476 | None | 1,615.28 |
| 2 | 16,801 | None | 1,669.23 |
| 3 | 16,779 | None | 1,550.56 |
| 4 | 16,732 | Step 3660, neuron 10133 | 1,554.21 |

Trials 0 and 4 are accepted after bound parent causal reviews. Each differs by
one spike shifted one step. Common-history budgets, native repeats, context-array
records, original artifact hashes, canonical inputs and source compatibility pass.
Host reconstructions are bit exact, with zero decomposition residual. Voltage
gaps of 0.00001857 and 0.00000784 mV lie within the unchanged 0.00145 mV budget.
Raw unaccepted reports remain unchanged. Derived records are
`checkpoint-8b1facc-sugar-10000-0/verified-case.json` and
`matrix-increment-01/verified-sugar-10000-4.json` beneath
`executions/implementation-20261014-matrix`.
First paired replay fell from 1,576.93 seconds on `c53af8a` to about 704.27 seconds:
55% less time, 2.24 times faster. The old failed timing F1 was 0.798815; its partial
raw evidence remains retained. Changed arithmetic requires fresh affected cases.
**Candidate acceptance is 10/52; all prescribed batch comparisons remain.**

Current production workflows passed under `workflows-current-01` in the matrix
root. Sugar/100 steps/two trials produced 100 spikes, exactly matching two native
Brian2 prefixes; silent/one step produced typed empty output. Six-column schema,
integer times, identities, canonical inputs, source/input hashes and comparison
JSON/CSV passed. Simulation times were 19.53 and 9.87 seconds, concurrent with
the engine-free preflight. These are bounded workflow proofs, not matrix acceptance.

## Remaining plan and completion

1. Complete the remaining 42 cases, starting with ten-second sugar trial 0.
   Required local evidence matches current source/test bytes; do not rerun
   unchanged suites.
2. Keep sources stable. Source queues reduced storage 287→2.6 MB;
   sparse due verification and shared scaling preserve observed phase bytes.
   Observed one-second throughput is 70–83 ms/step. Further optimization must
   justify its implementation and requalification cost.
3. Preserve verified CPU overlap, first-replay scoring and owned worker cleanup.
   Diagnose a failed gate using retained native evidence and the smallest replay
   before launching another full-network execution.
4. Complete sugar/P9 four-trial batches, causal audits, pooled metrics, 100 ms
   localization and provenance. Record results and limitations, push all changes,
   pass required checks and release outputs after their verification consumers finish.

Progress: **45%**: inventory 10 points, workflows 8, current local evidence 8,
implementation 10 and 10/52 of 49 matrix points. Batches and delivery retain
10 and 5 points; their acceptance remains incomplete.
The working target is **3–5 days of agent elapsed execution**, with a
**90%-confidence remaining estimate of 3–14 days**, assuming continuous Mac
availability. Remaining cases require 1,176,000 steps per engine, twice with
repeats. At 80 ms/step, remaining paired execution projects about 2.2 days before
batches, diagnosis and repairs. CPU overlap is demonstrated; longer horizons remain
unverified.
