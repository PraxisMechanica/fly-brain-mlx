# Prospective exact CPU evaluation review

Fresh-context reviewer: `/root/review_active_cpu_adoption`, GPT-6 Astra at `xhigh`, checkpoint `74fd0f5`. Read-only review; no tests, simulations, edits, process signals or nested delegation. Parent verification checkpoint `33c5381`.

Decision: implement and qualify active-source propagation as an exact evaluation mode of the frozen CPU comparator. Confidence 95%. Keep `torch_reference.py` unchanged as the oracle. Adoption requires the evidence below; this review alone does not adopt it.

The prepared matrix's finite integral float32 counts have incoming absolute sums at most 69,948, below 2^24. Binary recurrent spikes select exact integer contributions; every partial sum remains exactly representable. Float64 integer accumulation followed by float32 conversion and the original PyTorch post-sum scaling can therefore preserve the sum. This argument does not cover arbitrary real weights or nonbinary recurrent inputs. Overlapping external replay counts may exceed one and must retain their existing path.

Derive immutable source adjacency from the actual prepared, post-silencing compressed sparse row (CSR) matrix. Use an explicit typed step callable in the observer/collector, defaulting to the original forward method. The alternative calls the existing Replay, applies existing stimulus scaling, reads previous recurrent spikes, applies existing recurrent scaling and calls existing AlphaLIF. Preserve old-conductance voltage integration, all 19 delay slots, refractory updates, stimulus placement, strict threshold and resets.

Required qualification:

- Exact raw and scaled operation bytes for exhaustive small binary masks, untouched destinations, inactive negative edges, explicit zeros, cancellation, equal/opposite duplicate edges and a nonzero residual. Preserve zero sign bits rather than hiding a difference.
- Exact singleton/four-row operations, including empty, identical and different rows and sources with no outgoing edges; outgoing-only silencing must not prevent receiving input or emitting spikes.
- Fresh ordinary/observed trajectories across multiple queue wraps, firing, refractory transitions, overlapping input channels, silencing and empty connectivity. Compare all five native tensors at each step; verify repeats and chunked continuation.
- Two actual fresh free-running one-second sugar executions must match every retained original digest, native raster and final tensor. Feeding the saved spikes is insufficient. Include a retained whole-network silenced witness.
- Verify orientation, stored matrix values, integer bounds, ordered mapping, canonical stimulus/trial, targets/silencing, parameters, initial state, relevant source dependencies, native build/settings and full capture coverage.

The original one-second pair contains 10,001 ordered native snapshots in each run. Every digest includes all five native tensors and all 19 delay slots. The reviewer and parent independently verify both digest files and native archives against the completed-case manifest/ZIP and verify relevant source bytes against launch `55ea35f`. This permits complete native equality comparison without another long original pair once provenance is established.

The original environment did not record the native Torch binary fingerprint. Link retained lock/installation/build evidence before asserting full historical identity; never label a present binary hash as a past measurement. If that link cannot be established, retain old evidence as historical and obtain missing current-identity qualification. Version equality alone is insufficient.

Reject same-comparator certification for any byte difference, missing step, trial contamination, input/setup mismatch, unsupported bound, invalid recurrent bits or changed scaling/sequencing. Actual full-network sugar/P9 four-trial executions and repeats remain required for batch certification. Missing identities still need prescribed reference runs.

Reuse the native CPU raster and rescore each new three-engine case. The union of active neurons depends on MLX output, so old metric scalars are insufficient. CPU digest equality cannot establish Brian2-to-MLX tolerance; preserve relevant raw Brian2 values or verified replay. All 52 case obligations and acceptance gates remain unchanged.

Evidence: [parent checks](prospective-decision.json), [operation diagnostic](../active-source-rows/verification.json), [preserved full pair](../../../milestone-4/one-second-sugar-metric-failure/completed-case/verification.json). The requested `torch_trace.py` does not exist; `torch_observer.py` and `torch_collect.py` own the trace.
