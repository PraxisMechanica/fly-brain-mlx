# Execution-time investigation

Development remains paused at the user's request on 2026-10-05. The project goal is paused and the existing P9 process is suspended with its state preserved. The first investigation was read-only. The subsequent user instruction authorizes the bounded performance diagnostics below, completed without changing application source, dependencies or acceptance gates. No new full qualification case/matrix or production optimization was executed. The [pause record](evidence/execution-time-investigation/pause.json) binds the suspension to checkpoint `a4920ef`.

## The 105-minute check: findings and required action

The routine verification workflow has substantial avoidable cost. I built and used it without first measuring the cost of its dense scans and detailed recording. The measurements now identify those costs; 105 minutes is not a justified routine requirement of the goal.

One biological second contains **10,000 sequential 0.1-millisecond steps**. This check executes MLX, Brian2 and original CPU PyTorch twice each: **60,000 engine steps**, plus setup, native state/event/queue recording, cause analysis, repeat verification and reporting. It is a complete acceptance audit, not a single simulation step. The recorded 104.7 minutes is the time of that whole pipeline; about 56 minutes begins with the first CPU execution and includes capture/final processing.

### 1. Which evidence is necessary?

The [fixed contract](mlx-port-baseline.md#full-network-acceptance-fixed-before-validation) requires full-network agreement, two actual fresh executions per fixed engine/mode, native repeatability and queue/event validity, the 52 separately scored cases, prescribed batch checks and earliest relevant causal/budget evidence. Keep those requirements.

It does not require all three engines to run again for every candidate or every code/document edit. A completed one-second MLX spike-time F1 below 0.95 rejects that candidate regardless of PyTorch. The current pipeline waits until both paired executions and both CPU executions finish before scoring; this unnecessarily delays rejection. A screen must label unperformed acceptance/diagnostic work. It cannot declare acceptance or reject merely from a provisional partial-horizon score.

### 2. Different execution methods and measured alternatives

Use verified, immutable reference results and compare new MLX candidates against them. Separate a one-run completed-horizon spike screen from the complete audit of a stable candidate. Preserve the two real reference executions rather than calling two slices/reports fresh executions. Reuse requires an engine-specific source/build/input identity; current globally loaded-module hashes cannot simply be ignored.

Current Brian2 phase digests establish native repeatability but cannot reconstruct float64 values, evaluate float32/float64 tolerance, or exclude an earlier budget violation. A reusable reference record therefore needs raw complete relevant-prefix phase values, or deterministic replay verified against retained native digests. CPU native spike/final/digest records already retain more of the evidence needed for their comparisons. Missing reference coverage must be supplied, not assumed.

| Bounded diagnostic | Measured result | Limit |
| --- | --- | --- |
| Original CPU multiply on busiest saved step | **157.675 ms**; default transposed form **154.457 ms** | Changing orientation alone does not fix the bottleneck. |
| Built-in CPU explicit-sum kernel | **57.048 ms**, about **2.76×** faster | Native bytes agree on four selected patterns; this is an unqualified additional evaluator. |
| Active-source gather/sum with existing NumPy | **0.649 ms**, about **243×** faster on the saved active input | Reads **1,906** selected edges; dense/all-firing synthetic rows are slower. No whole-case speedup is claimed. |
| Unchanged MLX step at saved endpoint | Production **32.143 ms**; observed **73.486 ms** | One endpoint, synchronized component timing; not a GPU hardware trace or horizon average. |
| Separate MLX proof/reduction components | Ledger **39.449 ms**; accumulation **25.686 ms**; queue update **5.956 ms** | Inputs are already evaluated. These are not exclusive portions of the whole step and must not be added to it. |
| Host MLX capture components | Due hash/scan **9.830 ms/step**; queue hash **127.049 ms/boundary**; phase hash **95.256 ms/block** | Hash block uses 32 copies of one endpoint; scan volumes are logical bytes, not measured transfers. |
| Reference serialization, same 261.75 MB payload | Original **1.266 s**; buffered Boolean rows **0.909 s**; buffered/native checksum **0.228 s** | All nine payload digests/checksums agree; about **5.55×** improvement is serialization-only, not a new physical replay. |

The [CPU diagnostic](evidence/execution-time-investigation/cpu-multiply/verification.json), [active-source diagnostic](evidence/execution-time-investigation/active-source-rows/verification.json), [MLX components](evidence/execution-time-investigation/mlx-components/verification.json), and [writer diagnostic](evidence/execution-time-investigation/reference-writer/verification.json) retain exact executed sources, results and independent archive/source/input checks. A separate [failed CSR-by-CSR attempt](evidence/execution-time-investigation/unavailable-csr-product/failure.json) remains explicit: this installed CPU wheel rejects nonempty products. No extra framework or package was installed.

The active-source alternative is a materially different workload. Across the retained original one-second CPU raster, 17,062 spikes imply **2,612,441** outgoing edge visits, compared with **150,919,830,000** visits for a full scan each timestep. The simple prototype includes active-source discovery, gather, accumulation and dense output construction. Selected native output bytes agree before and after the unchanged 0.275 scale. Finite integral weights and the independently verified 69,948 incoming absolute-count bound make these integer sums exact, but source mapping, signed-zero/silencing coverage and full trajectory/mode preservation still require qualification. The [frozen PyTorch path](mlx-port-baseline.md#full-network-acceptance-fixed-before-validation) remains unchanged; this result does not authorize its replacement.

A broad Python-to-C++ rewrite is not the first remedy. The original CPU cost is already in C++, and the MLX production graph builds in about **3.44 ms** of its 32.14 ms step; most time remains in synchronized native evaluation. Narrow native MLX/Metal reduction or queue work can follow a sufficient profile and a separate correctness qualification. The delayed-source ring and native chunk/replay approaches below remain candidates, not adopted proof shortcuts.

### 3. Required frequency

| Work | When to run it |
| --- | --- |
| Focused deterministic scientific regression | Each affected numerical/scheduling/execution change, before bulk work. |
| Known-failure completed-horizon screen | Each plausible numerical remedy; one new MLX execution can reject an absolute failure. |
| Two fresh Brian2/PyTorch reference executions | Once per complete immutable engine/input/configuration identity. Repeat after relevant source, input, parameters, build, device, thread/mode or capture-coverage invalidation. |
| Full native MLX audit and prescribed batch comparison | A stable candidate in each changed numerical/execution mode, before acceptance. Two actual MLX executions; preserve every case's gates. |
| Full 52-case qualification | Stable candidate before full-network acceptance; rerun affected evidence after material numerical/execution changes. |
| Scoring/report corrections | Recompute from preserved native data when sufficient; rerun engines only for missing or invalid execution evidence. |
| Documentation-only changes | Relevant documentation/install checks; no automatic rerun of the entire brain. |

Approved ten-second sugar/P9 prefixes remove about **8.94%** of base steps, while retaining all independently scored cases and real boundary witnesses. They help, but are not the main performance remedy.

### 4. First-principles budget and the smell test

The [executed budget calculation](evidence/execution-time-investigation/check-runtime-budget.py) and [results](evidence/execution-time-investigation/check-runtime-budget.json) distinguish physical work, component extrapolation and desired workflow. One run updates about **1.386 billion neuron-steps**. The current CPU kernel also visits about **151 billion stored edges**, even for zero or sparse spikes. Its measured multiply implies **52.6 minutes for two runs**, explaining most of the recorded 56-minute CPU/capture/final phase. Two current MLX observed runs plus due/queue/phase host work extrapolate to approximately **30 minutes**. Original reference phase serialization adds substantial cost: about 81.8 GB of phase bytes and 4.159 billion one-byte Boolean writes per trial.

These terms produce a coarse **93.6-minute** work accounting before remaining setup, CPU state/capture, reference model/monitor/parsing and report costs. The terms are not exclusive wall-time shares: endpoints may differ, producers/consumers can overlap or wait, and contention changes timing. They explain why the current implementation can take 105 minutes. They do not justify its work choices.

**105 minutes fails the smell test as a routine candidate-validation workflow.** It is a consequence of scanning inactive connections, heavy recording/proof and rerunning fixed reference work. It is not evidence that the scientific goal intrinsically requires a 105-minute check.

Conditional engineering budgets with today's uncompiled MLX core:

- **5–8 minutes** for one completed one-second spike screen against verified retained reference spikes. The core alone extrapolates to 5.4 minutes here; the earlier 1,000-step production timing extrapolates to 6.25 minutes. This screen can reject, never provide full acceptance.
- **30–40 minutes** for the complete two-run MLX audit after properly preserving/reusing reference evidence, while retaining current dense native checks. Raw MLX execution alone is roughly 11–13 minutes for two runs; the current proof adds substantial cost.
- A lower full-audit target requires measured improvement of native reduction/proof work. Neither a one-minute whole-check promise nor a new project completion date is justified.

These are component-based planning budgets, not measured improved runs, statistical confidence intervals or delivery estimates. Replaying missing raw reference coverage and cold-cache/reference creation adds time. Do not apply a 243× component improvement to the whole audit.

### 5. Diagnosis and remediation order

Confirmed costs are the native CPU full-edge scan/per-entry dispatch, unnecessary work on inactive edges, dense MLX queue/state proof, expensive compensated accumulation, bytewise reference serialization/checksum, and unconditional reference/repeat execution before rejection. The default CPU helper invokes a scaled-vector addition for every stored edge, including the singleton trial; the specialized explicit-sum route avoids that helper. [Official PyTorch 2.11 helper](https://github.com/pytorch/pytorch/blob/v2.11.0/aten/src/ATen/native/sparse/SparseCsrTensorMath.cpp#L528), [specialized kernel](https://github.com/pytorch/pytorch/blob/v2.11.0/aten/src/ATen/native/cpu/SpmmReduceKernel.cpp#L26), and [parent source verification](evidence/execution-time-investigation/official-source-verification.json).

After an explicit user resumption: first make reference provenance/reuse and failure screening concrete; then qualify buffering/native checksum with complete observer frames and unchanged native reference outputs. Reduce measured proof/accumulation work only with equivalent evidence. Treat any faster comparator evaluator as a prospective scientific decision with complete preservation checks, not a selectable easier baseline. Measure an improved representative complete check before returning to bulk numerical work or issuing a forecast. All original gates, native evidence and suspended P9 state remain preserved.

The fresh-context **GPT-6 Astra at xhigh** review and read-only follow-up completed. Sol independently verified the contract, native source paths, integer bound, operation outputs, serialization, retained raster counts and budget calculations. [Decision and limits](evidence/execution-time-investigation/check-cost-review-decision.json). Production source, tests and dependencies remain identical to `a4920ef`; no proposed optimization is adopted. The original implementation still has 9/52 accepted cases, and the numerical candidate has none. **Development remains paused.**

## Why the estimates increased

I gave completion estimates before I had a complete costed execution plan. The required scientific matrix was already specified. I discovered its execution cost late, then changed both the assumptions and the uncertainty allowance between answers.

- **2–3 days:** the record does not support this with a measured end-to-end qualification budget. It was an unsupported completion estimate.
- **10–14 days:** I extrapolated the first one-second case to the remaining prescribed singleton durations, assuming serial execution and approximately linear cost. This produced roughly nine days of verification before batches and final work. It did not account correctly for permitted duration-prefix reuse, reusable reference results, measured concurrency, or early candidate rejection. Ten-second execution was unmeasured.
- **14–21 days:** I added time after the one-second sugar timing gate failed and a numerical correction/requalification became necessary. That extra allowance was not derived from a measured remediation duration or a proven correction. It should not have been presented as a reliable completion range.

The numerical failure is real. The forecast errors are mine. Neither the earlier estimates nor an 85%-confidence completion date are supported by the present evidence. All previous ranges are withdrawn as reliable forecasts.

## Measured costs and their limits

| Existing evidence | Result | What the measurement supports |
| --- | --- | --- |
| Complete one-second sugar qualification | 6,279.312 seconds, or 104.7 minutes | Two paired MLX/Brian2 executions, two original CPU PyTorch executions, setup, capture, verification and reporting; input loading is outside this timer. |
| Same 0.1-second Brian2 replay | Ordinary 1.879 seconds; observed 51.045 seconds | Detailed reference observation and its consumer add substantial cost; native outputs agree. |
| Complete 0.1-second CPU comparator proof | Ordinary 163.538 seconds; observed 173.319 seconds | Both modes already inspect/hash every state snapshot. The 5.98% difference measures the additional observer wrapper, not total auditing overhead. |
| Short P9 CPU stack sample | 183 of 207 main-thread samples, or 88.4%, in native sparse matrix multiplication | This sampled phase is dominated by an existing C++ routine. This is a short snapshot, not a whole-run or graphics processing unit (GPU) profile. |
| Production MLX 0.1-second run | 51.601 seconds total; 37.500 seconds warm simulation | The unaudited simulation also has substantial cost. Its timings cannot be substituted for qualification timings. |

Sources: [completed sugar timer](evidence/milestone-4/timing-remediation/review-decision.json), [reference observer comparison](evidence/milestone-4/full-reference-observer/reference-observer.json), [CPU comparison](evidence/milestone-4/full-cpu-observer/cpu-observer.json), [stack sample](evidence/execution-time-investigation/p9-cpu-stack-sample.txt), and [production run](evidence/milestone-3/production-sugar/simulation.json). The preserved progress milestones place approximately 56 minutes after entry into the CPU-first phase, including capture and final processing; this is not a measurement of pure multiplication time.

The [independent calculations](evidence/execution-time-investigation/calculations.json) reproduce workload totals, timing ratios and sample counts. The [executed calculation source](evidence/execution-time-investigation/executed-calculations.py) uses only preserved files and static source inspection. Parent source inspection also confirms that the MLX proof's mode named ordinary already captures phases, due masks and queue hashes; its 50.331-to-158.679-second comparison cannot isolate MLX observation overhead.

## Specific causes of slow progress

The verification pipeline is expensive and too tightly coupled. [Execution](../src/fly_brain/qualification/adapters/case_execution.py) completes both paired runs and both CPU runs before [scoring](../src/fly_brain/qualification/adapters/case_report.py). A candidate that fails an absolute timing floor cannot be rescued by later CPU comparison. Finishing its acceptance pipeline delays diagnosis. Reference results are also tied to each candidate's execution instead of being independently reusable evidence.

The reference observer exports seven float64 and three Boolean neuron fields at every timestep. That is about 81.8 gigabytes of phase payload per biological second, excluding time, queue and event records. Its [generated writer](../src/fly_brain/qualification/adapters/brian_observer.py) performs more than four billion one-byte Boolean writes over that horizon, plus bytewise checksum work. Buffering the existing stream without changing its bytes is a concrete candidate for improvement. Its individual contribution still requires profiling.

The MLX production [queue](../src/fly_brain/simulation/backend/bucketed.py) stores 19 Boolean slots for 15,091,983 connection rows: about 287 megabytes per trial. Two dense selection operations update it each step. The [ledger](../src/fly_brain/qualification/adapters/mlx_ledger.py) additionally checks all 19 slots each step. The [observer](../src/fly_brain/qualification/adapters/mlx_observer.py) hashes about 151 gigabytes of due-mask bytes and 90 gigabytes of queue bytes per biological second/trial, before other scans. These are logical operation and host scanning volumes, not measured physical transfers. MLX and NumPy can share unified memory through array views. [Official conversion documentation](https://ml-explore.github.io/mlx/build/html/usage/numpy.html).

Compilation is disabled and production evaluates each timestep separately. Queue work, compensated reductions, graph construction and synchronization are plausible bottlenecks. No GPU profile currently ranks them. I should have measured these costs before committing the full verification workload to the present implementation.

There is also a separate correctness blocker: the complete one-second sugar case has spike-time F1 of **0.798815**, below the fixed **0.95** floor. F1 measures the agreement of matched spike events. A very small threshold-rounding difference propagates through later network activity. The reviewed increment candidate repairs the saved local fork and the suite already in flight finished with **208 passes and zero skips**. It has no accepted full-network case. Faster execution alone does not resolve this uncertainty. [Recorded failure](evidence/milestone-4/one-second-sugar-metric-failure/completed-case/verification.json) and [preserved existing suite](evidence/execution-time-investigation/already-running-suite/result.json).

## Different approaches

| Approach | Recommendation and scope |
| --- | --- |
| Python orchestration with MLX | Keep configuration, data loading, execution requests and results in Python. Change the execution and proof plan first. |
| C++ MLX frontend | Offers native integration and lower frontend overhead. The same MLX arrays/backend operations remain. Select it only if measured frontend costs justify the additional build and requalification work. |
| Custom Metal kernels within MLX | Preferred escalation for a narrow measured GPU bottleneck. Gives control over work grouping, memory access and arithmetic order while preserving MLX production. Available from Python and C++. |
| Direct C++/Metal application | Gives greater buffer and command-submission control. Requires a larger rewrite and departs from the present MLX-only decision. Existing evidence does not justify selecting it now. |
| Native CPU C++ simulation | Brian2 already demonstrates efficient native reference simulation. It can use float64, but replacing production with it changes the Apple MLX objective; replacing PyTorch with it changes the pinned comparator. |

Official sources: [MLX C++ interface](https://ml-explore.github.io/mlx/build/html/dev/mlx_in_cpp.html), [custom Metal kernels](https://ml-explore.github.io/mlx/build/html/dev/custom_metal_kernels.html), and [native extensions](https://ml-explore.github.io/mlx/build/html/dev/extensions.html). Custom kernels are therefore a supported way to obtain more control without rewriting the whole application.

A C++ frontend does not enable float64 on the MLX GPU. MLX documents float64 operations as CPU-only. [Data types](https://ml-explore.github.io/mlx/build/html/python/data_types.html). Compilation can fuse operations and change rounding; the compensated algorithm requires a separate numerical qualification of any compiled/custom-kernel mode. Safe math mode alone does not prove preserved arithmetic. [Compilation](https://ml-explore.github.io/mlx/build/html/usage/compile.html) and [versioned kernel documentation](https://github.com/ml-explore/mlx/blob/v0.32.3/docs/src/dev/custom_metal_kernels.rst). If the reviewed single-state correction still fails long-horizon gates, a higher-precision state representation is a separate scientific design question.

A more substantial representation candidate is to retain delayed source-neuron spike bits instead of duplicating them for every outgoing connection. With this model's uniform delay, raw ring storage would be about 2.63 megabytes per trial. Original-row identities, duplicate connections, silencing, loss-at-arrival, wraparound and observation must remain correct. This is an unapproved design candidate, with no measured speedup; dense edge gathers and deterministic reduction could remain costly.

## Proposed resolution after the user lifts the hold

1. **Correct the execution plan.** Map every acceptance obligation to its evidence. The [approved contract](mlx-port-baseline.md#full-network-acceptance-fixed-before-validation) expressly permits ten-second sugar/P9 runs to supply shorter prefixes. Preserve all 52 independently scored identities and two fresh executions per engine. Capture actual native state, physical queues, offsets/counters and input cursor at each shorter boundary. The current collector needs those witnesses; slices of missing evidence cannot supply them. This removes 110,000 of 1,231,000 base steps per engine, about **8.94%**, before setup savings. It does not explain the whole estimate increase.
2. **Separate candidate screening from acceptance.** Reject an already completed required horizon when an applicable CPU-independent absolute floor fails. Preserve the failure and required diagnostic evidence; explicitly record unperformed work. A temporary partial-horizon score or an explained first spike difference alone is insufficient for rejection. Full acceptance retains every fixed/paired/repeat/batch gate.
3. **Reuse verified immutable reference evidence.** Key completed engine-specific records by inputs, model/setup, source dependencies, build, device, thread/reduction settings and capture method. Preserve both actual fresh executions. Changed MLX arithmetic invalidates old MLX acceptance, but need not invalidate unchanged original reference/comparator execution. Missing reference phase context still requires deterministic replay. Do not ignore a source mismatch without proving the engine's dependency boundary.
4. **Measure and preserve improvements before bulk runs.** The follow-up now measures bounded reference serialization, CPU multiply alternatives, MLX graph/evaluation, accumulation, queue, ledger and hashing. It is not an exclusive whole-pipeline hardware profile. Qualify the existing-format writer first; separately preserve coverage while improving the expensive proof/native paths. Consider a custom MLX/Metal operation only with sufficient profiling and separate execution-mode qualification. Require preserved native results, queue/event proof, repeatability and measured complete-check savings.
5. **Establish a stable numerical implementation before bulk runs.** Finish the remaining prerequisites for the already reviewed increment candidate, then screen the known failed one-second sugar case from fresh state. Do not transfer the original implementation's nine accepted cases. Keep the reference, strict threshold and all metric floors unchanged.
6. **Forecast from physical work.** Measure a representative ten-second case, required batch execution and safe concurrency. Cost remaining physical runs and engineering gates, accounting for verified reuse and prefixes. Disclose scientific failure/requalification uncertainty. No further calendar range is supported before this evidence exists.

The [causal contract](mlx-port-baseline.md#full-network-acceptance-fixed-before-validation) already allows chunk digests and deterministic replay. A staged audit can reduce raw export, but matching endpoints cannot establish all intermediate invariants, and float64/float32 hashes cannot be compared for tolerance. The earliest budget violation still needs a complete relevant-prefix comparison. Preserve current checks until an equivalent proof method is verified; do not start a second proof framework without a measured reason.

## Review, verification and current state

The bounded `/root/review_execution_strategy` review completed using fresh-context **GPT-6 Astra at xhigh**, at source checkpoint `ca64c6b`. Its recommendation is to change qualification execution before a broad rewrite, with **95% confidence in that next action**, not eventual completion. Sol independently read the cited code and contract, reproduced the workload/timing/sample calculations, checked native descriptor agreement, verified the installed kernel interface, and confirmed application source/dependency files remain identical to `a4920ef`. [Review decision and limits](evidence/execution-time-investigation/review-decision.json).

The original implementation retains **9/52** accepted cases. The candidate has zero accepted full-network cases. The first read-only investigation ran no new profile or benchmark; the subsequent authorized bounded diagnostics and their limits are recorded above. The remaining P9 process stays suspended; its paused wall time must be excluded from any later throughput calculation. The goal remains paused until a further user instruction. Investigation changes are committed locally; push remains pending because no user-owned remote is configured.
