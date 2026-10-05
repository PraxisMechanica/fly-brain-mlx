# Bounded matrix-diagnostic decision

Reviewer: `/root/review_matrix_diagnostics`, fresh-context GPT-6 Astra at explicit `xhigh`. Reviewed checkpoint: `5ae0cf9`; completion tree: clean `1f3ab53`. Sol records the returned decision and its limits here. No application files, network calls, device runs, or commits were made by the reviewer. The independent running P9 case was untouched.

Decision: pool neuron counts within each experiment and duration, keep timing matches within each trial, and report integer 1,000-step time-bin counts. No scientific ambiguity blocks this diagnostic policy. The [frozen contract](../../../mlx-port-baseline.md#full-network-acceptance-fixed-before-validation) and every individual case gate remain unchanged.

## Grouping and coverage

Use `(experiment, steps)` from `required_cases()`: 12 groups, ten with trials 0–4 and two silent groups with trial 0. Keep `ParityCase.trial`; normalized single-case rasters have no trial column, and native single-case CPU coordinates use local trial zero. One canonical raster per engine/case contributes to pooling. Repeats and batch replicas contribute verification, not extra trials. Different durations share prefixes and must remain separate.

Report expected, included, missing, invalid, and failed identities. Include valid complete rasters from cases that fail metric or causal gates. Missing or invalid data cannot be scored as silence. Refuse duplicate identities. Partial groups can have partial diagnostics using their actual included trials. No included trials means unavailable metrics and counts. Complete coverage does not imply acceptance.

## Pooled counts and rates

For included trials `R`, `r = len(R) > 0`, horizon `H`, and `T = H/10000` seconds, use `C_X(i) = sum_t C_X,t(i)` and exposure `r*T`. Rate is `C_X(i)/(r*T)`. A valid silent trial contributes exposure; a missing trial does not. Common support is the group-wide active union of Brian2, MLX, and CPU PyTorch, retaining missing-neuron zeros.

Calculate the existing exact rational Jaccard, total count error, signed count ratio, and normalized neuronwise error from pooled count vectors. Compute Pearson correlation directly from counts on the same support; common exposure cancels. Do not average case correlations. Shared-active correlation stays secondary. Rate mean absolute error and root-mean-square error use pooled rate differences on common support, in hertz.

Pooled counts describe the trial-averaged response and can cancel opposite errors in different trials. Pooled Jaccard describes neurons active in any included trial. Neither verifies agreement within each trial.

## Trial-separated timing

Independently apply the existing chronological greedy matcher for every trial/neuron at windows 0, 1, and 10 steps. Sum match counts `K_w`; pooled timing F1 is `2*K_w/(N_B+N_X)`. Precision and recall retain the existing empty rules. Never concatenate rasters before single-case matching, or offset trial times consecutively: both methods can create cross-trial matches. Run all three windows independently; filtering ten-step matches cannot recover the other windows.

Mean and median absolute timing errors use the combined multiset of matched differences, multiplied by 0.1 milliseconds. Do not average trial means/medians. No matches means unavailable timing errors.

## Time bins and empty values

Emit every half-open integer bin `[1000*b, 1000*(b+1))` through `H`. All prescribed horizons divide by 1,000. Use `step // 1000` and an explicit output length. Network counts per case/engine/bin must sum to that engine's spike count. Retain trailing zeros and silent bins. Missing trials have unavailable counts; step `H` is invalid. Pooled bin counts sum included trials. No neuron-by-bin tensor, new bin correlation, or bin acceptance threshold is needed. Timing can match steps 999 and 1,000 within the same trial.

For a nonempty set of valid trials, reuse current empty/undefined conventions: exact pooled silence has Jaccard/F1 1, count errors 0, undefined signed ratio/correlation, and no matched timing errors. Added spikes against silence keep normalized errors undefined. Constant vectors keep correlation unavailable. These rules do not apply to missing coverage. Do not call `apply_gates()` on pooled diagnostics or use aggregate equality to satisfy any failed individual fallback.

## Evidence, limits, and next action

The reviewer checked trial exchange, offset trial boundaries, trial exposure/common support, weighted F1/timing errors, independent matching windows, integer bin endpoints, and 52-case/12-group coverage with small in-memory calculations. The retained sugar raster reproduced 1,612/1,612/1,609 spikes, support 343, 1,030 CPU timing matches, and F1 `2060/3221`. One initial review-harness assertion incorrectly required computed correlation to equal 1 exactly; it was corrected for NumPy's `0.9999999999999999` result.

Sol independently verified these counterexamples and retained sugar scores. [Parent verification](parent-verification.json) records the actual source hashes and successful checks. This review does not execute new full-network cases, certify matrix/batch/performance completion, or authorize a new persisted report format, application programming interface, schema, or gate.

Next: implement pure diagnostic pooling and bin functions with focused intent tests. Preserve `evaluate_case()`, `apply_gates()`, existing files and command behavior. Commit each passing unit before further implementation.
