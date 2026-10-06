# MLX fly-brain milestones

Historical milestone log preserved during the 2026-10-05 documentation audit.
Snapshot checkpoint: `b93229808ce40c5bdce58cf1bb288338ec4da82a`. Entries retain their recorded scope,
including superseded holds, forecasts, model switches, and remote status.
Use the active [milestone.md](../../../milestone.md) for current instructions and
acceptance status, [AGENTS.md](../../../AGENTS.md) for agent policy, and the
[numerical contract](../numerical-contract.md) for scientific gates.

Native-stack checkpoint retained from `e54aed7` (2026-10-06):

Further development is held by the latest user instruction until the rejected pull-request series is cleaned up. PRs 1–4 are closed; their source commits, branches, incoming work, and evidence are preserved. The first replacement reapplies only the shared local commit/push checks and their source-only rejection fixtures, including the indexed-input guard. It starts from `2362fab5c2019b95d665669f13ff81b39a537b20` on `ocasta181/local-quality-checks`; confidence in this scope and dependency order is 99%.

The user approved registered native GitHub stacking on 2026-10-06. Each replacement remains a single-purpose PR; `main` is the stack's enforced merge destination, while parent branches supply focused comparison bases. Review local checks, continuous integration, boundary-coverage characterization, then the documentation-only refresh. The latter uses the preceding workflow/coverage records and required check foundation. Preserve every original ref and omit bulk metric reports. Full structural-rule coverage remains incomplete; local checks do not release scientific development. Confidence in this review order is 91% at `aa0c8c8deeba6c61be124c854929a4bdfcc0e76b`.

Verification of this reconstructed local-check scope: `just check` passes formatting, lint, strict typing, all three import contracts, 37 quality tests with no failures or skips, and staged metric comparisons. All fifteen retained tooling/evidence files match their preserved source bytes. Application/scientific suites were not rerun; no application or numerical source is changed. Required native commit and push hooks must also pass before delivery.


This is the authoritative project plan, acceptance criteria, and progress record. Updated 2026-10-05 (Europe/Paris). It consolidates the supplied charter, milestone specification, startup evidence, and subsequent user amendments.

Documentation consolidation checkpoint (2026-10-05): at `2362fab5c2019b95d665669f13ff81b39a537b20`, confidence **98%** in separating user instructions from agent policy, active plans, and historical records. Move twelve agent documents under `docs/agent/`, rebase authored links, add a document-owner index, and mark old reports/review briefs as historical. All 697 local links/anchors across sixteen documents pass. Original scientific text, review ownership, source, dependencies, data, and evidence are preserved. Next documentation step: simplify the human README and active milestone plan, collect developer commands, and archive the complete checkpoint log. Quality-gate implementation remains pending after this documentation task.

## Development resumed — measured performance remediation

At `710a267`, the standalone metric engine passes **17 source-only tests with zero failures/errors/skips**. Real isolated Git fixtures reject CQ001/CQ002/CQ003 regressions, an unstaged repair over a staged defect, and a bad commit followed by a repair commit. Repaired/nearby compliant source passes. Missing analyzer, missing history, invalid syntax and empty source scans return analysis failures. [Executed report](../../evidence/code-quality/metric-intent-tests.xml). No application, device or database is started. Both installed hooks already passed the shared command during the `aebad54` commit and branch push; controlled rejection/weakening fixtures and continuous integration remain to be implemented. Complete architecture-catalog coverage remains open.

At `2362fab5c2019b95d665669f13ff81b39a537b20`, the updated user goal requests coherent review branches and stacked pull requests. Confidence **99%** that this supersedes the earlier main-only workflow for new work. Continue quality enforcement on `codex/quality-gates`, based on the published `main`; commit and push verified increments, then submit a pull request whose checks pass. The shared command is `just check`, configured for both commit and push. The first invocation exposed a test-runner import-path error; invoking pytest as a Python module fixes it. The corrected command passes formatting/lint across **166 files**, strict types with zero errors/warnings, all three complete existing import-contract scans, and **9 source-only tests with zero failures/errors/skips**. Exact staged metrics cover **226 files / 24,856 nonblank lines**, with average/max complexity **5.42 / 28** and health/maintainability **68.92 / 68.92**; all three regression gates pass. Broader source/hook rejection fixtures, continuous integration and complete architecture-rule coverage remain open; these native tool commands alone do not prove all structural predicates.

The user's 2026-10-05 follow-up supplies `origin = git@github.com:PraxisMechanica/fly-brain-mlx.git` and requests publishing the current work before installing static analysis and the reusable code-quality checks. **The first push is complete** at `02613c0`: GitHub's repository API exposes `src/fly_brain` and the remote `main` matches the local commit. The initial push failed because the imported upstream commit was a shallow history boundary with a missing parent; `git fetch --unshallow upstream` restores that history without changing project commits, then `git push --no-thin -u origin main` succeeds. Future incremental commits must push to this user-owned origin. Earlier pending-push statements below are historical.

Next work: install the requested quality checks before returning to performance implementation. The supplied `~/Code/code-quality/` location is absent; the matching standalone package is at `~/Code/AIUC/code-quality/packages/code-quality`, source checkpoint `ed7aea73c7c5d11e63d6d30fefd671859500557d`, with no package-local changes. At `02613c0`, confidence **99%** that this is the intended source. Use its independently importable metric engine, preserve the application's uv/MLX runtime, and add local and continuous-integration enforcement. The package needs no application server or database. No new quality integration or expanded architecture compliance is claimed yet.

Status: **resumed by the user's 2026-10-05 instruction to document the approach, implement the optimizations, and continue**. At clean `4d8cac3`, confidence **98%** that this authorizes the recorded performance remediation and subsequent milestone work while preserving scientific gates and architecture. This instruction supersedes the historical investigation hold below. The app goal tracker still reports paused; agents cannot change that tracker to active, but the user's explicit instruction authorizes current work.

At `20f0b44`, install the standalone `@eng-metrics/code-quality` archive, with all runtime/documentation bytes bound to the unchanged source package at `ed7aea73`. [Archive provenance](../../../tools/code-quality/provenance.json) records pnpm's removal of the metadata file's final newline and the corrected exact verification; no analyzer is changed. Add pinned development-only Radon 6.0.1 and pre-commit 3.2.2 via uv, and lock the metric package via pnpm. The scientific reference packages remain installed at their frozen versions. Actual full committed-snapshot analysis covers **223 supported files / 24,759 nonblank lines**, average/max cyclomatic complexity **5.46 / 28**, heuristic health/maintainability **68.90 / 68.90**. [Complete measured snapshot and unsupported-path inventory](../../evidence/code-quality/bootstrap/initial-snapshot.json). The [exact staged-snapshot comparison](../../evidence/code-quality/bootstrap/staged-check.json) passes all three unchanged metrics; its first sandboxed attempt could not write Git's temporary index lock, and the authorized execution passes. Ruff, formatting, strict Pyright and the existing three import contracts pass. This establishes the development toolchain only; hook installation, source-only rejection fixtures, continuous integration and expanded architecture-rule coverage remain required before claiming quality setup complete. Commit and push this verified dependency checkpoint before adding gate behavior.

At `890465b1f2d5e020096690caa572ab5490502518`, follow the user's instruction to keep `AGENTS.md` project-specific. Confidence **99%** that the repeated general rules belong in the supplied user instructions. Reduce the file from 354 to 41 lines, retaining the authoritative plan/scientific-contract links, MLX-only runtime scope, data/evidence preservation, Sol/Astra settings and review ownership, and project remotes. Refer current holds to this record instead of repeating the released architecture hold. All three local links and the existing delegation anchor pass verification; `git diff --check` passes. General user rules remain in effect. This is a documentation change; application tests and scientific runs are not required for it. Quality-gate setup remains the next implementation work.

The execution approach now separates candidate screening, reusable reference evidence and full acceptance. Preserve original runs and pinned comparator source. A completed-horizon absolute failure can stop a screen; it cannot count as a completed acceptance case. Reuse references only with independently verified engine-specific input/source/build/mode provenance and sufficient native values or digest-verified replay. Keep two real fresh runs and all 52 independently scored obligations.

Implementation order and verification:

1. Buffer reference Boolean output and use an equivalent native checksum. Verify complete frames, native states, queue evidence, repeat digests and useful measured savings before adoption.
2. Implement engine-specific reference reuse and completed-horizon rejection without changing public file/output contracts. Existing records with missing raw reference coverage require verified replay; never infer tolerance from hashes.
3. Qualify the measured active-source CPU operation against the pinned original core, including full native trajectory/digest equality, signed cancellation/zero, silencing, duplicate and batch cases. Keep the original evaluator and baseline until a prospective bounded scientific decision and required equivalence checks pass.
4. Reduce expensive MLX proof/accumulation work only under a reviewed equivalent coverage/numerical contract. Retain the original execution mode as an oracle; profile before a custom Metal kernel and requalify changed modes.
5. Measure an improved complete representative check, then finish the already reviewed numerical remedy prerequisites and screen the known failed one-second sugar case. Continue Milestone 4 only with qualified modes; old candidate acceptances do not transfer.

Use the existing uv/MLX architecture and approved packages. Keep changes inside their owning domains, run Ruff, strict Pyright, import contracts and relevant scientific checks, and commit every verified working step on `main`. Preserve process 62191 suspended until its original-mode work can be safely continued or recorded as superseded; do not silently discard its evidence. Do not issue a new completion forecast from component speedups.

At `74fd0f5`, implement buffered canonical Boolean rows and the system zlib `crc32_z` checksum in the reference observer. No package is added. The observer adds only its required zlib header/link flag; generated numerical code, initialization, schedule and original arithmetic flags remain unchanged. **34 tests pass with zero failures/errors/skips**, including complete frame checksums, all physical queues/cursors, independent original-row delivery, native phase/final/spike equality against stock and fresh repeated executions across block partitions. Ruff, formatting, strict Pyright and all three import contracts pass. [Application verification](../../evidence/execution-time-investigation/reference-writer/application-verification.json) and [test report](../../evidence/execution-time-investigation/reference-writer/application-tests.xml). The previously measured 5.55× serializer improvement remains a component result; measure the adopted writer and whole pipeline separately.

Dispatch `/root/review_active_cpu_adoption` at `74fd0f5` with fresh-context `gpt-6-astra` at `xhigh`. Its bounded read-only question is the prospective equivalence decision and decisive qualification for active-source CPU evaluation while preserving the original Torch model as oracle. The parent implements independent capture work while awaiting the review; no evaluator substitution occurs before the reviewed checks pass.

At `4ae255a`, measure the adopted writer body against the preserved original using the same 261,751,204-byte payload and consumer. Three runs of each produce identical full hashes and independently verified checksums. Median wall time falls from **1.188 s to 0.177 s (6.71×)**; producer CPU time falls from **1.028 s to 0.028 s**. [Executed diagnostic, native source and measurements](../../evidence/execution-time-investigation/reference-writer/adopted/result.json). The six payloads use repeated retained endpoint arrays; this is a serializer measurement, distinct from the complete-frame tests above and from whole-check timing.

At `33c5381`, accept the [prospective Astra decision](../../evidence/execution-time-investigation/active-cpu-qualification/astra-review.md) to implement and qualify guarded active-source CPU evaluation while keeping the pinned core unchanged. Parent verification independently binds both original 10,001-snapshot streams/native archives to the completed-case manifest/ZIP and source at `55ea35f`. [Decision and parent checks](../../evidence/execution-time-investigation/active-cpu-qualification/prospective-decision.json). Adoption requires focused signed-zero/duplicate/batch/state tests, two fresh free-running complete sugar matches, a silenced witness and resolved engine-specific provenance. No native historical binary hash was recorded; do not invent it. CPU metric scalars must be rescored using the new three-engine support. This remains a qualification mode, never an additional production backend.

At `f3a234b`, implement immutable outgoing adjacency from the prepared CPU matrix and an explicit optional step callable in its observer/collector. The default path and pinned `torch_reference.py` remain unchanged. **42 focused tests pass with zero failures/errors/skips**, including every binary mask of a graph with signed/zero/duplicate/cancelled weights, singleton/four-row scaled bytes, fresh 101-step trajectories and repeats, and unsupported-input/weight rejection. [Test report](../../evidence/execution-time-investigation/active-cpu-qualification/focused-tests.xml). Ruff, formatting, strict Pyright and all import contracts pass. The candidate remains disabled in the full-case runner pending complete free-running equality and provenance qualification.

At `7e702c6`, vectorize the independent queue proof into one gather/reduction across the 19 slots. Confidence **98%** that this preserves its Boolean equality checks without reducing coverage: every physical slot is still checked at every timestep, in the same 30-column output. **45 Metal tests pass with zero failures/errors/skips**, including corruption detection for all 19 slots and unchanged native phase, queue and due evidence. [Report](../../evidence/execution-time-investigation/mlx-components/vector-ledger-tests-final.xml). Ruff, formatting, strict Pyright and all import contracts pass. The first test run also passed; its type-check failure required using the API's declared list argument, then the final tests/checks passed. Numerical source remains unchanged. Measure useful savings before any performance claim.

At `4783bab`, accept the bounded prospective [Astra exact-count reduction review](../../evidence/execution-time-investigation/exact-count-reduction/astra-review.md), fresh `gpt-6-astra` at `xhigh`. Parent independently verifies all 693,195 retained native count pairs, positive-zero count lows/zero highs, zero-total initial bits and the original layout archive hash. [Decision](../../evidence/execution-time-investigation/exact-count-reduction/prospective-decision.json). Implement/qualify leaf-axis float32 sum only when each destination's full absolute integer-count sum after silencing is <=2^24; preserve every downstream compensated expression and the original out-of-envelope oracle. Complete scalar/pinned/layout/scientific/native repeated qualification is required before enabling this new mode; no old acceptance transfers.

At `09cd0d4`, add the guarded count-reduction candidate with explicit internal selection, original-reducer fallback and Boolean geometry validation. It remains **disabled by default**. **63 tests pass with zero failures/errors/skips**, including exact high/low/result bits immediately below/at/above the guard, signed zeros, cancellation, padded/empty destinations and singleton/batch/repeat checks; the existing recurrent reference suite also runs the candidate through firing, delay, refractory, silencing, overlapping inputs and chunked continuation. [Final report](../../evidence/execution-time-investigation/exact-count-reduction/focused-tests-final.xml). Ruff, formatting, strict Pyright and all import contracts pass. The first harness invocation failed because I omitted its artifact directory and used a callable without its required name; [failed report](../../evidence/execution-time-investigation/exact-count-reduction/focused-tests.xml) is retained. Correcting that invocation/factory leaves the numerical gates unchanged. Full prescribed scalar/layout and whole-network native qualification remain required.

At `a41b8d4`, complete CPU singleton-mode qualification: two actual fresh free-running 10,000-step sugar runs match every one of the original **10,001 native snapshots**, full raster and final tensors; two 1,000-step silenced witnesses also match completely. The sugar pair takes **308.85 s (5 min 9 s)** including complete native capture/hash; the silenced pair takes **30.80 s**. Parent independently matches all four files/runs to original case manifests. Current installation validates **12,413** Torch RECORD entries, native binaries and build; launch/current lock bytes and later build match. Historical build identity is explicitly derived from locked-artifact/install continuity, not a falsely backdated binary measurement, as accepted by Astra's bounded follow-up. [Full evidence and limits](../../evidence/execution-time-investigation/active-cpu-qualification/full-native/parent-verification.json). The initial driver's wrong silenced-case date is recorded; only its missing witness was rerun. **44 focused tests pass, zero failures/errors/skips**, including ordinary/chunked continuation and complete independent-trial agreement. [Report](../../evidence/execution-time-investigation/active-cpu-qualification/focused-tests-final.xml). Quality/architecture checks pass. Enable this exact CPU evaluation mode for singleton qualification; required full-network four-trial certification remains separate.

The same checkpoint adds explicit internal candidate selection to the existing scalar, pinned and complete-layout probes. All **157** scalar cases pass (**132 exact reductions / 25 original fallback**); all **24,576** prescribed pinned cases pass with the existing conversion limitations retained. The complete 15-bucket native layout witness passes and every stored array matches the retained oracle byte for byte. Broader qualification artifacts remain in `data/results/performance-remediation-exact-count-matrices-20261005` and `data/results/performance-remediation-exact-count-layout-20261005`. The first complete-layout attempt failed before accumulation because the new Boolean option reused a local array name; the corrected probe and strict type checks pass. The candidate remains disabled in normal execution until full native closed-run/repeat qualification and archived parent verification are complete.

At `7bc710d`, enable the qualified exact active-source CPU mode in singleton case execution and record its selection in an additive evidence file. **Two complete paired-case tests pass with zero failures/errors/skips**, preserving fresh CPU/reference/MLX repeats, native queue/evidence coverage and existing reports. [Report](../../evidence/execution-time-investigation/active-cpu-qualification/case-tests.xml). Ruff, formatting, strict Pyright and all import contracts pass. The default CPU observer callable remains the original oracle, and the normal simulation remains MLX-only. This change grants no additional MLX case acceptance.

At `29aa42a`, independently verify and archive the guarded MLX candidate's broader matrices. All native input/reference/result/count/repeat/singleton fields match the saved oracle: **157 scalar cases and 24,576 prescribed pinned cases across 31 targets**, plus every stored complete-layout array across 15 buckets. The **99 original one-step conversion limitations remain explicit**. [Executed drivers, compact arrays and parent verification](../../evidence/execution-time-investigation/exact-count-reduction/matrices/parent-verification.json). Confidence **98%** that these results satisfy the scalar/layout portion only; complete fresh closed trajectories and a fresh-process witness remain required before adoption. The private parent verifier was interrupted to correct repeated archive decoding inside a row loop; its original source is retained and the corrected verifier passes every numerical assertion. No scientific output or prior run was removed.

At `16e78e6`, measure the explicitly selected count candidate and vector ledger on the same retained step-10,000 endpoint. Seven synchronized samples per component give production-step medians **39.16 ms original / 21.14 ms candidate**, and observed-step medians **77.40 ms original / 53.26 ms combined candidate**. All actual state/trace bytes and all 30 proof flags match. The separate accumulation measurement is **29.37 / 33.01 ms**, so it does not support an isolated accumulation speedup claim; component costs overlap and cannot be added. [Executed source, measurements and verification](../../evidence/execution-time-investigation/mlx-components/optimized/parent-verification.json). Start the complete native witness with exact reduction explicitly active, both fresh trajectories and a separate-process full-layout repeat. No whole-check speedup or new case acceptance is yet claimed.

The user asks for a revised implementation estimate at this checkpoint. Planning estimate: **2–4 more hours for performance implementation/testing/commits**, and **3–5 days provisionally for end-to-end completion**, confidence **60%**, conditional on the numerical correction meeting every fixed case. This is not an 85%-confidence delivery commitment; replace it with a measured complete-pipeline estimate when available. The earlier unsupported forecasts remain withdrawn.

At `49fd4a9`, add optional lossless compressed recording of the original reference wire stream. A narrow byte-reader/writer seam records exactly what the unchanged frame parser consumes; replay uses that same checksum, clock, geometry and completeness validation. Deterministic gzip metadata makes fresh repeated capture archives identical. **31 focused tests pass with zero failures/errors/skips**: [18 transport/recording tests](../../evidence/execution-time-investigation/reference-writer/tape-tests.xml) and [13 actual reference-process tests](../../evidence/execution-time-investigation/reference-writer/live-tape-tests.xml), including native/ordinary/source/queue equality, live tape replay and owned-process failures. Ruff, formatting, strict Pyright and all three import contracts pass. I initially counted the non-yielded header as a frame; the [one-failure assertion report](../../evidence/execution-time-investigation/reference-writer/tape-tests-initial.xml) is retained and the corrected count passes. This is only the transport prerequisite; cache identity/sealing/reuse and complete-horizon screening remain to implement. No numerical source or public output contract changes.

At `99c335f`, wire optional recording into the existing paired collector. **Three live paired checks pass with zero failures/errors/skips**, including complete retained float64 phase hashes and every physical queue/cursor/delivery digest replayed from tape, both populated/empty pathways, ordinary-vs-recorded repeat equality and injected first-cause retention. [Report](../../evidence/execution-time-investigation/reference-writer/paired-tape-tests.xml). Ruff, formatting, strict Pyright and all import contracts pass; recording is opt-in and normal execution is unchanged. Dispatch fresh-context `gpt-6-astra` at `xhigh` as `/root/review_reference_reuse_contract` for a read-only prospective cache-provenance decision. No cache reuse is enabled pending the completed review and parent verification.

At `198092b`, accept the bounded [Astra reference-reuse contract](../../evidence/execution-time-investigation/reference-reuse/astra-review.md), confidence **97%**, after independently inspecting its preference/dependency and process-finalization findings. Bind effective semantic/code-generation preferences and actual installed/build/runtime contents; seal only after successful generator exhaustion and archive closure; compare complete tape spikes/final clock/cursor with native outputs as well as neural fields. Reparse complete original float64 values for each fresh candidate audit. Exact-horizon same-environment reuse only; no hash-only tolerance claim or transferred MLX acceptance. Implement and pass the recorded decisive checks before enabling any cache hit.

At `c7d3503`, require complete reference tape/native spike bytes, final clock/cursor, native field sets/types/shapes and finite correctly sized recurrent weights in paired capture. The original final neural-state check is retained. **13 focused tests pass, zero failures/errors/skips**: [ten native boundary/alteration checks](../../evidence/execution-time-investigation/reference-reuse/native-tests.xml) and [three actual paired-process checks](../../evidence/execution-time-investigation/reference-reuse/paired-native-tests.xml). Signed counts retain original unit scaling and outgoing silence. Ruff, formatting, strict Pyright and all import contracts pass. This closes the native-result binding prerequisite; provenance sealing/reuse remains disabled until its complete qualification.

At `be30da3`, adopt the bounded Astra follow-up's simpler post-build identity, confidence **97%**: preserve the existing reference compilation, then key actual generated code/static inputs, exact canonical model/stimulus/mapping, coverage and effective build context. The original sealed executable remains the producer on reuse; the new executable is unused. Add streaming content fingerprints for the complete installed Brian2 dependency closure and native/generated files. **16 identity intent checks pass, zero failures/errors/skips**, for every input, mapping, source/static/coverage/build-context category and the unused-executable/MLX-only boundary. [Report](../../evidence/execution-time-investigation/reference-reuse/identity-tests.xml). Actual installed closure fingerprinting succeeds; Ruff, formatting, strict Pyright and import contracts pass. Complete compiler/SDK/runtime capture and cache sealing/reuse remain to implement; no hit is enabled.

At `6c533da`, bind effective reference preferences, the complete installed generator closure, Python/native and operating-system build, processor, compiler/SDK, relevant build/loader environment and reference source inventory before and after actual compilation. Resolve the actual compiler and consumed system headers separately from `make.deps`, then record linked native/runtime identities. This implements the reviewed post-build provenance prerequisite; cache reuse remains disabled. **14 actual reference-job tests pass with zero failures/errors/skips**, including system zlib-header coverage and unchanged complete native/queue/phase replay. [Final report](../../evidence/execution-time-investigation/reference-reuse/build-tests.xml). Ruff, formatting, strict Pyright and all three import contracts pass. The first run passed 13 tests and failed one assertion because I expected a dotted preference name in an INI-format snapshot; [the initial report](../../evidence/execution-time-investigation/reference-reuse/build-tests-initial.xml) is preserved. Correcting that assertion changes no reference semantics or acceptance gate. Commit this verified state before cache finalization or further transport changes.

At `68b6b42`, independently verify both fresh complete one-second sugar trajectories with guarded exact-count reduction explicitly active. All **10,000 native phase snapshots, 313 queue boundaries, every due-event digest, all 30 ledger checks per timestep, final native fields and complete rasters** match the retained original mode. The separate-process complete 15-bucket layout also matches every oracle array. The two observed runs take **705.64 s and 719.64 s**; these are complete MLX witness timings, not paired-check or acceptance timings. [Executed witness, native arrays, parent verification and original archive binding](../../evidence/execution-time-investigation/exact-count-reduction/full-native/parent-verification.json). The original sugar timing-floor failure is preserved; same-engine equality grants no cross-engine acceptance. Confidence **98%** that the complete native/repeat prerequisite is met. Keep the default original reducer until the remaining applicable scientific checks pass, then enable the guarded selection with truthful evidence of the selected reduction. The previous goal turn made progress by committing the verified actual reference build context at `68b6b42`; this turn adds independently verified whole-network evidence.

The following paragraphs preserve the investigation history and the limits that applied before resumption.

The user requests an explanation for the successive 2–3-day, 10–14-day, and 14–21-day estimates; measured causes of slow progress; and a review of different approaches, including C/C++. Investigation may read existing source and evidence, inspect preserved process state, and record findings. Do not adopt the numerical prototype, start new tests or simulations, optimize the application, or relax acceptance gates during this hold.

At checkpoint `a4920eff7e083476416d838f85402c04234291ad`, suspend the existing P9 Python process (PID 62191, session 88326) with `SIGSTOP`. Its source, data, output, and live state remain preserved; do not restart or resume it. A brief stack sample taken before suspension supports the timing investigation. [Pause decision and process record](../../evidence/execution-time-investigation/pause.json) and [stack sample](../../evidence/execution-time-investigation/p9-cpu-stack-sample.txt). Confidence in this interpretation of the user's pause request: 95%.

The scientific suite already running before the pause finished with 208 passes and zero failures/errors/skips. This is isolated candidate evidence, not adoption or full-network acceptance. [Preserved result](../../evidence/execution-time-investigation/already-running-suite/result.json) and [independent XML/source/archive checks](../../evidence/execution-time-investigation/already-running-suite/preservation.json). Production numerical source remains unchanged; the accepted full-network matrix remains 9/52. The earlier completion estimates are withdrawn as reliable forecasts pending this investigation.

At clean `ca64c6b`, dispatch `/root/review_execution_strategy` using fresh-context `gpt-6-astra` at `xhigh` for a bounded read-only review. Its assignment is to assess measured execution costs, Python/C++/Metal alternatives, proof overhead, immutable reference reuse, duration-prefix obligations, and the minimum evidence needed for a reliable forecast. No file edits, test/simulation runs, process signals, nested delegation, implementation, or acceptance changes are permitted. Sol independently verifies the result and records a proposal while keeping development paused.

The review is complete. At `8acba3f`, Sol independently verifies its main evidence and records the [execution-time investigation and proposed resolution](execution-time-investigation.md), [read-only calculations](../../evidence/execution-time-investigation/calculations.json), and [bounded review decision](../../evidence/execution-time-investigation/review-decision.json). The cause combines unsupported forecasting, expensive native CPU comparison, heavy observation, avoidable execution duplication/coupling, and a real timing-score failure. Approved sugar/P9 prefix reuse removes about 8.94% of base steps; it cannot explain the entire estimate increase. No new completion range is justified.

Confidence **95%** in the proposed next phase after an explicit user resumption: correct the qualification execution/provenance plan, measure the costs, and select the smallest evidence-preserving improvement before bulk runs or a broad language rewrite. Keep Python orchestration and MLX production unless profiling supports a more specific change. Native C++/Metal controls are available within MLX. No optimization, representation change, numerical adoption, test/simulation launch, acceptance relaxation, or process resumption is authorized by this proposal. **The goal remains paused and P9 remains suspended.**

The user's subsequent 2026-10-05 instruction now authorizes **bounded performance investigation/debugging before any further work**. At `1b405c8`, confidence **95%** in interpreting this as permission for isolated operation profiles and short timing diagnostics, while preserving the feature/numerical-development hold, existing source, data, gates and suspended P9 process. Do not run another full qualification matrix or resume P9. Determine which parts of the 105-minute check are necessary, alternatives, required frequency, a first-principles runtime budget, and concrete causes of unreasonable cost. This diagnostic permission supersedes the earlier read-only limit only for the required performance investigation; it does not authorize production changes or a new completion estimate.

At `f3a6da9`, the bounded CPU operation diagnostic completes in 15.67 seconds. The current dense-times-sparse multiplication takes a median **157.675 ms** on a saved active step; the built-in explicit-sum sparse kernel takes **57.048 ms**, with identical native dtype, shape and output bytes for resting, saved active, all-firing and four-row inputs. This **2.76× component speedup** is not a whole-check speedup or adopted comparator change. Parent verification independently recomputes the 69,948 integer row bound, records actual matrix/index hashes and storage, and confirms the specialized operator in the native profile. [Diagnostic, executed source, profile and verification](../../evidence/execution-time-investigation/cpu-multiply/verification.json). Source, tests, dependencies and acceptance gates remain unchanged; P9 remains suspended. Recording/queue cost investigation remains open.

At `400ccb6`, a bounded Metal diagnostic completes in 12.50 seconds using one retained whole-network endpoint and repeated evaluation of the unchanged next-step expressions. Median production step **32.143 ms**, observed step **73.486 ms**, isolated ledger **39.449 ms**, compensated accumulation **25.686 ms**, dense queue update **5.956 ms**. The production graph builds in **3.437 ms**; most time remains in synchronized native evaluation. Due-mask hashing/scanning takes **9.830 ms per step**; queue hashing takes **127.049 ms per 32-step boundary**. This identifies expensive dense proof work and native reduction, rather than a reason for an immediate C++ frontend rewrite. All 30 ledger checks pass on the probed step and the isolated queue expression matches its output bytes. [Executed diagnostic, timings, scope and archive verification](../../evidence/execution-time-investigation/mlx-components/verification.json). This is one-endpoint component evidence, not a new accepted horizon, representative GPU trace, production optimization or sum of exclusive timing shares. The hold remains active.

At `a5e7973`, a bounded native reference serialization diagnostic emits the same 261,751,204-byte, 32-row payload in nine executions. Original one-byte Boolean writes with the current bytewise checksum take median **1.266 s**; buffering Boolean rows with the same checksum takes **0.909 s**; buffering plus the system's native checksum takes **0.228 s**, a **5.55× component speedup**. Every complete stream digest and independently checked checksum agrees. The original writer/checksum setup is extracted unchanged from application source, and parent verification reproduces its input hash and timings. [Source, measurements and verification](../../evidence/execution-time-investigation/reference-writer/verification.json). This is serialization-only evidence using repeated retained endpoint arrays, not a physical reference trajectory, complete frame qualification or adopted capture change. The production and acceptance hold remains active.

At `f0af676`, an isolated active-source gather/sum diagnostic completes in 9.57 seconds using existing NumPy. The saved busiest CPU step visits **1,906** outgoing edges rather than 15,091,983, taking median **0.649 ms**, approximately **243×** faster than the earlier original multiply component. Resting, saved active, all-firing and four-row output bytes match the original operation, including unchanged post-sum scaling. The simple prototype is slower for synthetic dense/all-firing inputs; this is not a universal speedup or whole-case result. [Measurements and independent original-output/raster checks](../../evidence/execution-time-investigation/active-source-rows/verification.json). The [failed prior CSR-by-CSR probe](../../evidence/execution-time-investigation/unavailable-csr-product/failure.json) is retained: nonempty products require unavailable support in the installed wheel. No package, framework or evaluator was installed/adopted. The frozen comparator still requires a prospective decision and complete equivalence/mode qualification before any replacement; the development hold remains active.

The bounded check-cost investigation is complete at `882c64e`. [Findings for all five user questions](execution-time-investigation.md#the-105-minute-check-findings-and-required-action) and [Astra review/parent decision](../../evidence/execution-time-investigation/check-cost-review-decision.json) preserve required science while identifying avoidable repeated reference execution, late rejection, native full-edge scans, expensive dense proof/reduction, and reference serialization/checksum. [First-principles work and runtime calculations](../../evidence/execution-time-investigation/check-runtime-budget.json) explain the original 105 minutes and distinguish conditional **5–8-minute failure screening** from a **30–40-minute two-run MLX audit after complete immutable reference reuse with current dense checks**. These are component-based engineering budgets, not measured improved runs, confidence intervals or completion estimates. Existing Brian2 phase hashes alone cannot supply cross-engine tolerance values; preserve raw relevant-prefix reference fields or use digest-verified replay. No optimized evaluator, capture method, proof shortcut, numerical remedy or acceptance change is adopted. **The goal and development remain paused; P9 remains suspended.** After user resumption, remedy the measured verification costs and measure a complete improved check before bulk numerical work.

## Architecture compliance — hold released

Status: **architecture remediation complete on 2026-10-04; all seven acceptance checks pass**. The user authorized the MLX-only repair, removal of Conda and NVIDIA backends, and removal of unused packages. This release applies to application architecture. Full-connectome loading, integration, parity, and performance remain open milestones.

I did not implement the required application architecture before the original numerical work. The [historical audit](architecture-audit.md) records that omission and its cause. The [remediation and final architecture review](architecture-remediation.md) records the repair, current technology scope, and limits. One uv project now owns the installed `fly_brain` package, MLX runtime, explicit domain boundaries, validated external requests, and complete quality checks. Independent Brian2 and CPU PyTorch remain optional qualification references. No database infrastructure is needed or present.

The [incoming-work archive](../../evidence/architecture-remediation/incoming-review-work.json) preserves all 47 original manual-review files and hashes. Numerical source, data/output contracts, scientific artifacts, and licenses are preserved. The manual review retains its owner; this architecture release does not finalize its separate specification updates.

- [x] Declare ownership and allowed imports for all application-owned code; resolve every audit finding without a blanket legacy exception.
- [x] Verify uv-managed installation, pinned resolution, normal imports, and side-effect-free domain/service imports; the clean ten-package runtime executes the core on Metal.
- [x] Enforce all three dependency contracts; inject configuration, execution engines, and output collaborators. No runner/orchestrator cycle or hidden run-state registry remains.
- [x] Pass full-scope Ruff formatting/lint/import checks and strict Pyright across all 48 application/test files. Narrow third-party typing limits are documented.
- [x] Verify thin entrypoints, independent run configurations, and existing file contracts with real Parquet/process checks; classify unit, integration, reference, and Metal tests.
- [x] Requalify 61 scientific tests, 157 factored scalar cases, and four deterministic reference replays using unchanged acceptance budgets, with zero skipped required tests.
- [x] Record the final Python/software architecture review, bounded Astra preservation decision, independently verified evidence, and this release before further milestone work.

Verification commands and evidence:

- `uv sync --locked --group qualification`; `uv lock --check --offline`; uv package compatibility checks for the 38-package development/qualification environment and ten-package clean runtime pass.
- `UV_PROJECT_ENVIRONMENT=/private/tmp/fly-brain-clean-runtime-20261004 uv sync --locked --no-dev --no-editable` installs the normal package. A smoke run outside the checkout executes 19 Metal steps with the expected delayed conductance. [Installation record](../../evidence/architecture-remediation/clean-runtime.json).
- Ruff lint/import sorting and formatting, strict Pyright, and `lint-imports --no-cache` pass. [Final check record](../../evidence/architecture-remediation/checks.json) and [typing report](../../evidence/architecture-remediation/pyright.json).
- `pytest -q --disable-warnings --junitxml=docs/evidence/architecture-remediation/boundary-tests-final.xml`: **31 passed, zero failures/errors/skips**. [Application report](../../evidence/architecture-remediation/boundary-tests-final.xml).
- `uv run --locked --group qualification fly-brain qualify --output data/results/architecture-remediation-20261004/qualification-final`: **61 passed, zero failures/errors/skips**. [Result](../../evidence/architecture-remediation/qualification/result.json), [report](../../evidence/architecture-remediation/qualification/tests.xml), and complete trace arrays are retained.
- The installed `probe-factored`, `probe-accumulation`, `probe-replay`, and `inspect-reference` commands write fresh sibling outputs under `data/results/architecture-remediation-20261004`. [Factored scalars](../../evidence/architecture-remediation/factored-scalars/factored.json): **157/157** meet both unchanged budgets, with bit-identical repeated/standalone results. [Replay](../../evidence/architecture-remediation/reference-replay/numerical-contract.json): all four traces are byte-identical with 43 spikes and the frozen stimulus hash. [Schedule diagnostic](../../evidence/architecture-remediation/reference-schedule/reference-schedule.json) matches the retained reference.
- [28 source/reference checks](../../evidence/architecture-remediation/source-preservation.json) pass. [Artifact/archive verification](../../evidence/architecture-remediation/artifact-preservation.json) confirms 1,076 arrays in 39 artifacts retain their dtype, shape, and bytes, and all incoming archive hashes are valid.
- The fresh-context Astra subagent at `xhigh` returned a **bounded numerical preservation pass**. The parent independently verified its evidence. [Review and limits](../../evidence/architecture-remediation/astra-preservation-review.md).

The retained weight-casting diagnostic still passes only 109/125 original-weight one-step budgets and 119/125 trajectory budgets; its 125 successful diagnostic assertions are not a parity pass. Threshold-rounding and serial-cancellation limitations remain explicit. No full-connectome execution, compilation, custom kernel, production spike export, full-network parity, or performance approval is implied.

Incremental implementation checkpoints: `22c813e` preserves authorization/incoming work; `d98f5bf` establishes the application and uv tooling; `bf97672` verifies installation/file boundaries; `c61e246` records numerical qualification and Astra review. The release is a separate documentation checkpoint. Push remains pending because only the reference `upstream` remote is configured.

## Objective and execution

Develop a scientifically validated Apple MLX backend for the [Eon Systems fly-brain simulation](https://github.com/eonsystemspbc/fly-brain), preserving the existing FlyWire v783 leaky integrate-and-fire model's numerical behavior, activation and silencing experiments, and output contracts. Run the complete connectome locally on Apple silicon and provide reproducible correctness evidence, measured performance, and verified installation instructions. This is an MLX array-compute project, not an MLX-LM language-model project.

Implementation owner: GPT-6.1 Sol at the user-selected reasoning effort; the updated goal requests `xhigh`. The user controls parent-model changes. Future bounded scientific, numerical, and difficult kernel-design reviews use GPT-6 Astra subagents at `xhigh`, following [the current delegation rule](../../../AGENTS.md#active-project-specification). Keep the already assigned manual accumulation-design review with its current owner and recorded return procedure.

Do not implement MaleCNS, new neuron models, plasticity, reinforcement learning, a user interface, or a generalized simulation framework. Keep the authorized MLX-only architecture; preserve model semantics and data contracts. Optimize only after correctness is established. No custom Metal kernel without profiling evidence. Honor [AGENTS.md](../../../AGENTS.md) and the user's standing schema-approval and database-preservation requirements.

## Implementation and evidence rules

The numerical backend varies; the model, experiment definitions, neuron ordering, connection direction, weights, delays, activation, silencing, thresholds, reset, and timestep semantics must remain invariant under the reviewed contract.

- Read and run the reference before adding MLX code. The bounded review selects pinned Brian2 2.8.0 CPU float64 as ground truth; the [reviewed contract](../numerical-contract.md#reviewed-discrete-contract) resolves material inconsistencies. Do not blend contradictory backend behavior.
- Use the installed MLX package and explicit domain boundaries. Preserve the validated numerical core, model semantics, scientific evidence, and data contracts.
- Generate stochastic stimulus schedules outside the engines and feed identical events to each. Equal seed values across unrelated generators do not prove equal stimuli.
- Keep simulation state resident on the Apple graphics processing unit. Do not transfer complete state to the CPU each timestep. Retain the simple correct implementation as an oracle if optimized kernels are introduced.
- Verify one milestone before proceeding to the next. Update this file after significant steps with exact commands, test results, measured outcomes, unresolved issues, and supporting artifact links. Commit verified work incrementally on `main`.
- Commit each verified implementation step before beginning the next. Commit later execution evidence separately, and inspect `git status --short` before proceeding. This checkpoint rule implements the user's repeated instruction to avoid accumulated changes.
- Commit every passing working state with changes immediately; more than 100 uncommitted lines is an immediate commit checkpoint under the user's latest amendment.
- Distinguish tolerance-bounded small-network continuous state with exact ordinary-fixture discrete parity from full-network event/statistical parity. Keep the separately asserted threshold-rounding limitation explicit. Do not declare acceptance thresholds after seeing results, explain away discrepancies, or infer scientific validity from a successful run alone.

Each review assignment must contain the reason for deeper review, current checkpoint and commits, exact evidence and files to inspect, one bounded requested outcome, and a completion condition. Use [the bounded subagent skill](../../../skills/bounded-subagent/SKILL.md) with the model and effort specified by this project's delegation rule for future reviews. Sol awaits the result, verifies the evidence, records the decision, and commits integrated work before continuing dependent implementation. The earlier manual handoffs retain their historical completion records.

## Completion requirements

Every requirement remains open until the evidence below is recorded and inspected:

1. `uv run --locked --no-dev fly-brain simulate --duration-s 0.1 --trials 1` runs the complete MLX simulation on Apple silicon. The first normal-installation sugar run is verified in Milestone 3; repetition and control runs remain required.
2. MLX outputs the existing Parquet spike schema and works with existing comparison tools.
3. Seeded runs are repeatable with identical externally generated stimulus schedules.
4. Small deterministic networks match an approved reference at every timestep, including leak, threshold, reset, excitation, inhibition, simultaneous fan-in, fan-out, delay, and silencing.
5. The full pinned FlyWire v783 dataset runs without CPU fallback for synaptic propagation.
6. Full-network numerical parity with Brian2 is no worse than PyTorch under an explicitly approved metric, stimulus protocol, and tolerance.
7. Benchmarks separate initialization, compilation/warm-up, warm simulation, result collection, memory, and synchronization costs; report steady-state timesteps per second and biological simulation time per wall-clock second.
8. A clean Apple-silicon installation and documented reproduction workflow are executed successfully.
9. Final scientific review, required corrections, and complete verification are recorded without silently skipped tests or overstated claims.

## Milestone 0 — Reference baseline

Status: complete for reference evidence; the numerical-contract review is also resolved below.

Acceptance: `docs/mlx-port-baseline.md` documents enough implementation-level detail to reproduce the pinned Brian2 model without guessing. Relevant tests and experiments provide direct evidence for the stated behavior. Material disagreements are collected for review, not silently resolved.

Required work:

- [x] Pin and import upstream while preserving its source and licence notices.
- [x] Read Brian2, PyTorch, and orchestration code.
- [x] Reproduce the shortest supported Brian2 CPU experiment.
- [x] Record equations, exact discrete integration, operation order, timestep, delay, threshold, reset, refractory behavior, activation, and silencing.
- [x] Record neuron ordering, connection direction, data counts, random-number and seed behavior.
- [x] Record benchmark fields, spike-output schema, comparison-tool contracts, and backend disagreements.
- [x] Record licensing and publication/source distinctions.
- [x] Run focused reference-contract tests and preserve raw evidence.
- [x] Finish the baseline document and the bounded numerical-contract handoff.

Evidence completed:

- Upstream commit: `a3db62f9436074e485c0278290c2164ed6150808`; [pin record](../../upstream-pin.json).
- Import commit: `4466b37`; upstream implementation matches the pinned tree. Only project documentation and ignore patterns differ at import.
- Experiment commit: `295994b`.
- Consolidation commit: `396f169`; reference-contract evidence commit: `5489ae0`.
- Command: `.venv/bin/python scripts/run_reference_baseline.py --output data/results/mlx-reference-20261004`.
- Brian2 2.8.0, NumPy 1.26.4, Python 3.10.14; full resolved reference environment in `requirements-reference.txt`.
- Full-data sugar experiment: 21 stimulated neurons at 200 Hz, 0.1 seconds, one trial, 0.1 ms timestep; 1,518 spikes and 321 active neurons.
- Measured build: 12.742 seconds; simulation: 1.348 seconds; spike extraction: 0.329 seconds; total accounted time: 16.824 seconds. This is one unseeded reference run, not a repeatability or MLX-performance claim.
- [Raw result and schema](../../evidence/milestone-0/brian2-baseline.json), [log](../../evidence/milestone-0/brian2-baseline.log), [input summary and hashes](../../evidence/milestone-0/input-summary.json).
- Measured inputs: 138,639 neurons, 15,091,983 connection rows. The original approximate five-million figure does not describe the pinned connectivity file.
- [Reference baseline contract](../numerical-contract.md) records the exact observed model, ordering, data/output contracts, comparison tools, differences, and licence notices.
- `.venv/bin/python -m pytest -q tests/test_reference_contract.py --junitxml=docs/evidence/milestone-0/reference-tests-final.xml --disable-warnings`: nine passed, zero skipped/failures/errors, 136 dependency warnings, 2.84 seconds. [Final test report](../../evidence/milestone-0/reference-tests-final.xml).
- [Generated update, schedule, and delay diagnostic](../../evidence/milestone-0/reference-schedule.json): Brian2 recurrent conductance arrives at step 18 and affects voltage at step 19; PyTorch's measured arrival/influence steps are 20/21.
- [Publication equations and source provenance](../../evidence/milestone-0/publication-source.json) were retrieved from the Europe PMC full-text interface and distinguish the original v630 study from this v783 dataset.
- The inspection harness reproduced the retained schedule/delay evidence exactly. All 71 local links in the README, milestone, baseline, and handoff documents passed verification. `git diff --check` passed; the diff against the upstream pin for numerical source, data, original scripts, environments, and licences is empty.
- [Bounded Astra review request](../handoffs/astra-numerical-contract.md) records the checkpoint, evidence, required decisions, and return condition. No review decision is implied by Milestone 0 completion.

Resolved scientific review:

- Brian2's coupled linear integration, threshold-before-stimulation scheduling, frozen/gated refractory state, outgoing-only silencing, and step-18 delivery/step-19 voltage effect are authoritative. PyTorch remains the comparison baseline with its known numerical differences.
- A firing neuron immediately blocks incoming writes even when its refractory duration is zero; the review refined the earlier reset-only explanation with a pre-reset observation.
- Float32 policy, state tolerances, exact discrete invariants, threshold-rounding treatment, deterministic stimuli, and full-network acceptance are fixed in the [reviewed baseline](../numerical-contract.md#reviewed-precision-and-state-acceptance). The full-network gate requires both fixed floors and no worse than PyTorch for every primary metric/case.

## Numerical-contract handoff

Status: resolved. Contract approved for Milestone 1 implementation/qualification; the user returned execution to GPT-6.1 Sol at `xhigh`. This is not approval of an MLX implementation or full-network result.

Review checkpoint (2026-10-04):

- Probe/evidence commit: `4b7ea63`, following incoming checkpoint `6deca27`. `.venv/bin/python scripts/probe_numerical_contract.py --output data/results/mlx-numerical-review-20261004` completed all assertions. It probes linear float32 error, threshold rounding, cancellation, and deterministic external replay; it does not implement a backend.
- A 10,000-step linear diagnostic against Brian2 float64 measured maximum float32 voltage/synaptic errors of 0.000381470/0.000218289 mV. A quarter-unit-in-the-last-place threshold offset changes the float32 spike decision; a 4,097-event cancellation case changes the sum from 0.275 to 0.25 mV with adverse ordering. These are explicit precision limitations, not parity passes.
- Two NumPy runtime replays and two independently built C++ standalone replays produced identical complete state/discrete traces and 43 spikes each under the same 1,000-step, three-channel event schedule. Schedule regeneration, save/load, duration prefix, and trial separation checks passed.
- [Probe measurements](../../evidence/milestone-0/numerical-contract.json), [compressed raw reference trace and events](../../evidence/milestone-0/numerical-contract-replay.npz), and [probe source](../../../src/fly_brain/qualification/adapters/replay_probe.py) are retained. Fresh standalone builds and four raw traces remain in the probe output directory; no existing output was removed.
- `.venv/bin/python -m pytest -q tests/test_reference_contract.py --junitxml=docs/evidence/milestone-0/reference-tests-contract-final.xml --disable-warnings`: 12 passed, zero skipped/failures/errors, 162 dependency warnings, 17.97 seconds. Added tests settle same-step recurrent/native-Poisson input gating, refractory-boundary arrival, and replay equivalence with guaranteed native Poisson input. The preceding 11-test and 12-test runs are preserved; the final refinement adds native Poisson input to the pre-reset gating test.
- All 92 local links/Markdown anchors across the README, milestone, baseline, and handoff passed verification. The compressed evidence matches each of the four retained raw traces and the stimulus hash. Original upstream file changes remain limited to the pre-existing `.gitignore` and README changes; numerical source/data are untouched. `git diff --check` passed.

Deliverable completed: the [bounded review record](../handoffs/astra-numerical-contract.md#decision-record--resolved) records selected semantics, evidence, limits, and remaining qualification. The [baseline](../numerical-contract.md#reviewed-discrete-contract) holds the durable specification. No numerical backend or public interface was implemented in this review.

Return condition met: reference semantics and acceptance decisions are explicit and evidence-supported. No further reference probe blocks Milestone 1. Actual MLX precision/compilation/repeatability, high-fan-in accumulation, the full-network matrix, and future public/empty-output schema changes remain unverified or unapproved as specified in the handoff. The user must switch back before implementation resumes.

## Milestone 1 — Small MLX numerical kernel

Status: complete for the reviewed small-network envelope, uncompiled Metal mode. Compilation and full-connectome accumulation are not qualified.

Acceptance: every timestep's voltage and synaptic state meet the [reviewed budgets](../numerical-contract.md#reviewed-precision-and-state-acceptance): isolated one-step error ≤`2e-5 + 2e-6*abs(reference)` mV and trajectory error ≤`1e-3 + 1e-5*abs(reference)` mV. Ordinary fixtures require exact spike/reset/refractory/delay-event state, with no timing slack. Test strict equality and neighboring representable values, and assert the separate near-threshold rounding limitation rather than claiming universal float64 spike equivalence. Run every enumerated synthetic case, shared deterministic stimuli, and repeated identical runs without skips.

Start with source indices, destination indices, and weights. Keep model state on the Apple graphics processing unit. Use externally generated stochastic schedules shared with the reference. Do not load the full connectome or add a custom Metal kernel at this milestone.

Startup checkpoint (2026-10-04):

- Review checkpoint `4fcb224` was clean. The active session metadata confirms GPT-6.1 Sol at `xhigh`; no model was switched or substituted by the agent.
- Installed MLX/MLX-Metal 0.32.3 into the existing Python 3.10.14 environment; [MLX requirements](../../../pyproject.toml) and [qualification tools](../../../pyproject.toml) are pinned. Existing reference dependency versions were preserved.
- `MLX_ENABLE_TF32=0` GPU smoke test succeeded on Apple M1 Max, macOS 15.3.1, architecture `applegpu_g13s`, 34,359,738,368 bytes unified memory. Device operations returned `[2.0, 3.0]` for `[1, 2] + 1`.
- The sandbox cannot expose a Metal device; the GPU smoke process was authorized outside the sandbox. Actual qualification must use the same access, without CPU fallback. No core correctness or milestone acceptance is inferred from this smoke test.

Initial implementation checkpoint:

- [Private core](../../../src/fly_brain/simulation/backend/core.py) uses explicit Metal streams, float32 state, integer last-spike steps, a Boolean 19-slot per-edge queue, exact availability/reset/input gating, and ordered edge/channel additions. This deliberately small oracle does not claim a scalable connectome accumulation method.
- [Qualification suite](../../../tests/qualification/test_mlx_core.py) compares independent Brian2 phase monitors plus a spike-derived event ledger with complete MLX state/event traces. Ordinary fixtures require the approved threshold margins, exact discrete parity, state budgets, and bit-identical repeats. The threshold rounding counterexample is an asserted limitation.
- `.venv/bin/python scripts/qualify_mlx_core.py --output data/results/mlx-milestone1-20261004-01`: 40 passed (12 reference, 28 MLX qualification), zero skipped/failures/errors, 251 dependency warnings, 31.79 seconds. [Initial report](../../evidence/milestone-1/initial-tests.xml), [measurements](../../evidence/milestone-1/initial-measurements.json), [result](../../evidence/milestone-1/initial-result.json), and [log](../../evidence/milestone-1/initial-qualification.log) are preserved. Complete traces remain in the fresh output directory.
- Ruff and Pyright passed for the authored core/qualification runner. The initial run left explicit long-trace repeatability, coincident recurrent delivery, fresh-state pending-queue reset, and large-cancellation coverage to finish; these are closed in the final checkpoint below.

Final qualification checkpoint (2026-10-04):

- Implementation checkpoint `03f5b40` followed dependency pin `af06fa8`. All work remained on `main`; existing numerical runners, comparison tools, data, licences, and public/persisted contracts were preserved.
- `.venv/bin/python scripts/qualify_mlx_core.py --output data/results/mlx-milestone1-20261004-final`: **43 passed** (12 reference and 31 MLX qualification), zero skipped/failures/errors, 256 dependency warnings, 42.81 seconds. [Final result](../../evidence/milestone-1/final/result.json), [test report](../../evidence/milestone-1/final/tests.xml), [log](../../evidence/milestone-1/final/qualification.log), [measurements](../../evidence/milestone-1/final/measurements.json), and [artifact hashes](../../evidence/milestone-1/final/manifest.json) are retained. All 19 compressed diagnostic/state/event artifacts are preserved beside them. Earlier fresh output directories remain untouched.
- Six isolated linear cases satisfy the one-step budget. Two complete 10,000-step Metal traces were bit-identical; maximum voltage/synaptic error against Brian2 was **0.000381470/0.000218289 mV**, within the fixed trajectory budgets. [Complete linear traces](../../evidence/milestone-1/final/linear-10000.npz).
- Every ordinary firing-network case satisfies state bounds at pre-threshold, pre-reset/post-input, and end phases, safe reference threshold margins, and exact spikes, availability, last-spike steps, due/accepted/discarded events, channel decisions, and per-edge pending queues. Each was repeated bit for bit. Maximum recorded phase-state error among these cases was **0.000045944 mV**; no timing or discrete-state tolerance was used.
- Coverage includes rest/empty output, exact reset/freeze, strict equality/neighbor predicates, excitation/inhibition, balanced and duplicate-edge fan-in, 32 simultaneous edges, fan-out/self-delay/multiple wraps, refractory loss/release and release-at-arrival, same-step recurrent loss at ordinary and zero refractory durations, outgoing-only silencing with retained incoming activity/spiking, overlapping channels/zero-rate activation, trial reset, chunked continuation, and standalone-vs-batched independent trials.
- The 1,000-step retained schedule has the approved byte hash and duration prefix; the 43-spike MLX replay meets the complete retained Brian2 state/discrete evidence as well as independent live phase monitors. Three batched trials match individually initialized trials bit for bit. Chunk boundaries preserve pending edges and state exactly. [Replay evidence](../../evidence/milestone-1/final/retained-replay.npz), [batch evidence](../../evidence/milestone-1/final/batched-trials.npz), [chunk evidence](../../evidence/milestone-1/final/chunked-continuation.npz).
- The quarter-unit-in-the-last-place threshold case explicitly asserts the approved precision-dependent spike difference. The 4,097-event cancellation diagnostic is also an **asserted limitation**, outside the ordinary envelope: ordered serial float32 and `mx.sum` both yield **0.25 mV** versus **0.275 mV**, exceeding **0.00100275 mV**. Interleaved serial addition yields 0.275000006 mV, demonstrating order sensitivity rather than approving a general accumulation method. [Raw accumulation evidence](../../evidence/milestone-1/final/accumulation-limit.npz). Passing these diagnostic assertions does not mean the adverse numerical case passed parity.
- `.venv/bin/ruff check code/mlx_core.py tests/test_mlx_core.py scripts/qualify_mlx_core.py` passed; `.venv/bin/pyright` passed strict checks for the authored core/runner; `UV_CACHE_DIR="$PWD/.uv-cache" uv pip check --python .venv/bin/python` confirmed all 41 installed packages are compatible. Authored diffs passed whitespace checks. Existing numerical source/data match the upstream pin.
- The core keeps neural state and propagation on explicit Metal streams, with host-only setup/coefficient construction and integer loop control. Qualification collects traces after execution; its per-step synchronization is for correctness evidence and makes no throughput claim. No compilation, custom kernel, connectome load, public MLX command, production output, full-network parity, clean installation, or performance result is claimed.

## Accumulation-design handoff

Status: **preferred outcome achieved on the reopened attempt**. The same manual Astra owner selects the factored-connectivity design for Milestone 2 implementation/qualification. All finite scalar and network gates below pass. Sol has verified and integrated the completed review after architecture release; actual connectome conversion, integration, full-network parity, compilation and performance remain unqualified.

Milestone 1 is complete at `52f8427`. The [current bounded-review decision](../handoffs/astra-accumulation-design.md#selected-design--factored-connectivity-with-compensated-scaling) specifies the selected arithmetic, minimal representation, evidence and next qualification. The earlier blocker-only outcome is historical and superseded. No custom kernel, tolerance waiver, backend integration, or full-data benchmark is approved by this handoff.

Review diagnostic checkpoint (2026-10-04):

- Incoming checkpoint `1757aa8`, clean `main`. Active session metadata confirms GPT-6 Astra at `xhigh`; no model substitution or review agent was used.
- `MLX_ENABLE_TF32=0 .venv/bin/python scripts/probe_mlx_accumulation.py --output data/results/mlx-accumulation-review-20261004-final` completed all diagnostic assertions on the Apple M1 Max Metal device. [Probe](../../../src/fly_brain/qualification/adapters/accumulation_probe.py), [measurements](../../evidence/accumulation-review/accumulation.json), and [complete raw inputs/results](../../evidence/accumulation-review/accumulation.npz) are retained; source and artifact hashes were verified. The initial `-01` output remains intact.
- All **125 scalar diagnostics** produced an exact two-component representation of the sum of their stored float32 inputs and the correctly rounded final float32 sum. High/low components and final results repeated bit for bit and matched independently run, minimally padded standalone reductions. The original adverse case returned **0.2750000059604645 mV** instead of 0.25 mV.
- This is **not an accumulation parity pass**: only **109/125** cases meet the original-weight float64 one-step budget, and **119/125** meet the trajectory budget. All failures are retained individually. In particular, 128 copies of `[2405, -2404, -1]*0.275 mV` have near-zero float64 sum but a **0.003124237060546875 mV** sum after individual float32 weight casts, exceeding the unchanged **0.001 mV** trajectory floor even with exact subsequent addition. Ordinary reductions can accidentally cancel this input error; that does not qualify them.
- Ruff and strict Pyright passed for the new probe. The qualified small core, its existing tests, upstream runners, dependencies, and production contracts are unchanged. The existing 43-test suite was not rerun in this diagnostic-only step; its retained Milestone 1 result is not a test result for this candidate. No full-data loading, custom kernel, compilation, or benchmark was performed.

Initial decision checkpoint (superseded by the reopened review below):

- Probe/evidence commit `0084fe0`. The [durable precision record](../numerical-contract.md#accumulation-review-reduction-candidate-and-weight-cast-blocker) separates weight-cast error from reduction error and preserves all fixed budgets. The candidate is supported for further diagnostics only; six measured trajectory failures preclude strategy approval. Independent-process repeatability and full propagation remain untested.
- The return condition is met through the documented-blocker branch. After the user's switch, Sol may begin the [precisely specified Milestone 2 host-side input audit](../handoffs/astra-accumulation-design.md#exact-next-work-for-sol-milestone-2-input-audit), preserving data and existing numerical code. Mapping, per-source cast-error extrema, and representative pinned-data masks provide evidence for the next bounded numerical decision. The audit cannot dismiss the retained synthetic failures or authorize rollout by itself.
- Final documentation verification: all 138 local links/anchors across the README, milestone, baseline, and handoffs passed. The retained arrays independently reproduced the exact cast-input sums, correctly rounded outputs, and bitwise repeated/standalone comparisons; evidence hashes matched. Ruff, strict Pyright, and `git diff --check` passed. The diff against incoming `1757aa8` for existing core/tests/runners/dependencies is empty. Both review commits remain local because no user-owned push destination is configured.

Reopened review checkpoint (2026-10-04):

- Incoming checkpoint `71400e3` includes the user's new delegation workflow, which explicitly preserves this manual review's owner. The user asked this owner to attempt a passing strategy. The earlier blocker and evidence remain recorded; the next input audit is deferred until this attempt concludes.
- [Factored-scale probe](../../../src/fly_brain/qualification/adapters/factored_probe.py): keep signed integer connectivity exactly in float32, reduce it with the compensated tree, then use compensated products with high/low float32 components of the shared `0.275` scale and combine current synaptic state before final rounding. This tests the factoring alternative already contemplated by the numerical contract. No per-edge extra weight component, float64 device state, tolerance change, or production-core change is introduced.
- `MLX_ENABLE_TF32=0 .venv/bin/python scripts/probe_mlx_factored_accumulation.py --output data/results/mlx-factored-review-20261004-01`: **157/157** scalar cases pass both original-float64 one-step and trajectory budgets, including all retained 125 cases and 32 new cases. Count expansions are exact; repeated components/results and independently sized standalone results are bit-identical. Maximum measured one-step budget fraction is **0.023660**. [Measurements](../../evidence/factored-accumulation/scalars/factored.json) and [complete scalar inputs/results](../../evidence/factored-accumulation/scalars/factored.npz) are retained. Ruff and strict Pyright pass for the new probe. This checkpoint does not yet approve firing-network behavior or connectome rollout.

Final reopened-review decision:

- Scalar prototype/evidence commit `4aa7ec8`. A second fresh process using `--output data/results/mlx-factored-review-20261004-repeat` also passed all 157 cases; every input/reference/component/result array and the reports match byte for byte. [Independent repeat verification](../../evidence/factored-accumulation/scalars/independent-repeat.json). The original 4,097-event result is `0.2750000059604645 mV`; the previous 384/6,144-event casting failures now return `0 mV`, within the unchanged budgets against their near-zero original-weight references.
- Full command/environment in [result.json](../../evidence/factored-accumulation/networks/result.json): the unchanged 43-test reference/core suite plus [18 factored-input tests](../../../tests/qualification/test_factored_accumulation.py) completed **61 passed, zero skipped/failures/errors**, 352 dependency warnings, 77.34 seconds. [Test report](../../evidence/factored-accumulation/networks/tests.xml), [log](../../evidence/factored-accumulation/networks/qualification.log), [factored measurements](../../evidence/factored-accumulation/networks/factored-networks.json), [hash manifest](../../evidence/factored-accumulation/networks/manifest.json), and all 37 compressed trace artifacts are preserved in the evidence directory.
- The test-only adapter feeds factored state into subsequent timesteps and compares independent live Brian2 phases and the exact event ledger. Maximum factored-network phase-state error is `0.000026733 mV`. Exact spikes, refractory/receiving state, due/accepted/discarded edge events, repeatability, three-trial batching, chunking, fresh trials, and Metal operation with a CPU-default stream are verified. Delayed 4,097/384-edge cancellation also passes the isolated arrival-state budget. The new replay uses count-derived weights and is separately named; the unchanged original fixtures and retained replay still run in the 43-test portion.
- **Select the uncompiled factored-connectivity strategy** in the [durable specification](../numerical-contract.md#selected-factored-accumulation-strategy). This uses the already contemplated common-scale factoring exception, keeping device arithmetic and persistent neural state float32. Approve the stated destination grouping for initial Milestone 2 implementation, with actual mapping/count guards and all representative-source-mask comparisons still required. Do not change tolerances, coalesce rows, alter queue meaning, compile residual formulas, or add a custom kernel. No further Astra review is needed merely to begin this approved implementation; failures or new design changes use the amended bounded-delegation workflow.

## Milestone 2 — Connectome loading

Status: **complete on 2026-10-04**. Pinned host mapping, stable host buckets, the complete prescribed matrix through actual device layouts, every complete device field/event gather, scalar/live-reference regressions, and complete-connectome controlled delivery are verified. The selected factored arithmetic is unchanged. Full experiment integration, parity, and performance remain later gates.

Acceptance: MLX input arrays are demonstrably equivalent to upstream in neuron count, connection count, identifier-to-index mapping, source/destination orientation, weight scaling, delays, silencing masks, and deterministic checksums. The checkpoints below distinguish complete host equivalence, isolated device arithmetic, and the still-open integrated device representation.

Prove the mapping before introducing the approved destination grouping. Follow the [current Milestone 2 instructions](../handoffs/astra-accumulation-design.md#minimal-representation-and-exact-next-milestone-2-work), including arithmetic guards and the earlier audit's fixed source-mask selection. Implement the selected factored arithmetic, then qualify actual signed high-fan-in arrays against original float64 weights, exact event membership, repeatability and all fixed budgets. Rerun all 157 scalar cases and 61 reference/core/factored tests against the adapted implementation, retaining the original oracle. Full-network parity remains a separate later gate. A failed qualification or additional representation/precision change requires a bounded Astra subagent review; existing design approval does not waive it.

Input mapping checkpoint (2026-10-04):

- The installed `audit-inputs` command validates the two pinned SHA-256 hashes, preserves the CSV neuron order, verifies every presynaptic/postsynaptic identifier against its index, checks signed integer connectivity against sign times count, and retains every original edge row. NumPy/CSV/PyArrow perform host setup; no Pandas or neural CPU fallback is used.
- Verified **138,639 neurons and 15,091,983 edges**. Signed counts range from -2,405 to 1,897; there are no zero-count or duplicate source/destination/count rows in the pinned input. All counts convert exactly to float32. The greatest per-target absolute-count sum is **69,948**, below the approved `2^40` guard. Maximum incoming degree is **10,356**; nearest degree quantiles 0/50/90/99/100 percent are 0/69/229/662/10,356.
- Stable destination grouping retains original edge order within targets. Both permutation directions and every source/destination/count/float64-weight column round-trip exactly. Canonical original/regrouped checksums and complete locally retained arrays are recorded in [the installed-command report](../../evidence/milestone-2/input-mapping/installed-command.json). The temporary first audit and installed command produced byte-identical complete NPZ artifacts. [Repeat verification](../../evidence/milestone-2/input-mapping/repeat.json).
- Outgoing-only silencing is verified across the complete edge set and preserves row identity; unit/file tests also cover negative and zero counts, duplicates, invalid orientation/indices/counts, changed pins, and reversible ordering.
- **42 application tests passed, zero skips**; full Ruff, strict Pyright, and all three import contracts pass. The preserved 61 scientific tests remain the recorded unchanged-core result; this host-only step does not claim a new device qualification.
- Reproduction: `uv run --locked --no-dev fly-brain audit-inputs --output data/results/<fresh-input-audit-directory>`. Full converted arrays remain under `data/results`; their hashes and compact evidence are versioned. No original file was modified or deleted.
- Next: compute the prescribed cast-error/source-group extrema and deterministic target/mask selection; qualify actual signed fan-in with the selected factored strategy under both fixed budgets. Then implement the approved bucket representation, verify event membership, and rerun the 157 scalar/61 scientific regressions against it. Full-network execution and parity remain later gates.

Pinned-data qualification checkpoint (2026-10-04):

- The prescribed selector produces **31 targets**: union of top degree/absolute weight/positive and negative achievable source-group cast errors, nearest degree quantiles, and maximum absolute-count sum. Ties use neuron index. [Selection and all target metrics](../../evidence/milestone-2/source-patterns/patterns.json); complete per-target arrays are retained beside it.
- The 70 source masks per target preserve duplicate membership and use the exact recorded PCG64 seed tuples. Four new pure tests pass for selector ties, synchronized duplicates, achievable source-group error, and deterministic source identity across edge order. Full Ruff, strict Pyright, and three import contracts pass. These host checks do not complete device qualification.
- A mandatory cancellation state at target **11,645**, identifier **720575940611563310**, mask `negative-error`, produces a concrete first failure. It has 4,268 incoming rows, 1,998 accepted events, and absolute accepted-count sum 11,559. Requested initial state is `-789.5250000000001 mV`; float32 stores `-789.5250244140625 mV`.
- On the pinned M1 Max Metal device with precision policy zero and compilation disabled, original/reversed/fixed-permuted orders all give `-0.00002441406286379788 mV`, repeating bit for bit. Against the original-initial-state accurate reference the error is **0.0000244140628320455 mV**, exceeding the unchanged **0.000020000000000000066 mV** one-step budget. All three pass the trajectory budget. Against the separately labelled stored-initial-state reference, arithmetic error is about **4.23e-13 mV**; that alternative reference is diagnostic, not an approved substitute.
- [Failure measurements](../../evidence/milestone-2/initial-state-cast/initial-cast.json) and complete inputs/masks/orders/results preserve the failure. The audited contract explicitly includes initial casting. The entire actual-data matrix has not been run; no case is removed, no budget is relaxed, and no input/state representation is changed.
- The fresh Astra subagent at explicit `xhigh` completed the [bounded review](../../evidence/milestone-2/initial-state-cast/astra-review.md): the original-state one-step gate remains failed, and the stored-state result is correctly rounded. Initial information loss cannot be repaired by the unchanged reducer. The parent independently verified the exact decomposition and a collision of initial states requiring disjoint output intervals. [Parent verification](../../evidence/milestone-2/initial-state-cast/parent-verification.json).
- **Engineering decision recorded:** on 2026-10-04 the user delegated low-level engineering judgment to the agent. Sol adopts the bounded review's exact input-state accounting amendment in the [numerical contract](../numerical-contract.md#reviewed-precision-and-state-acceptance). The isolated fan-in one-step check compares accurate and ordered accumulation from the same stored float32 starting state with original float64 weights. Every prescribed original state and comparison remains recorded; both unchanged original-state trajectory gates remain mandatory. Original-state one-step failures stay labelled conversion limitations. All tolerance values, other small-network gates, event semantics, and full-network Brian2 criteria are unchanged. The [decision and rationale](../../evidence/milestone-2/initial-state-cast/astra-review.md#recorded-engineering-decision) resolve the hold; the complete matrix is the next required work.
- Current application suite: **46 passed, zero skips/failures/errors**. [Report](../../evidence/milestone-2/source-patterns/application-tests.xml). Full Ruff, strict Pyright, and all three import contracts pass. No numerical core change occurred during this decision review.

Qualification implementation under delegated engineering judgment (2026-10-04):

- The decision was committed at `93ba165` before dependent implementation. The pure fan-in case builder retains all prescribed source masks, conditional cancellation states, three orders, original and stored-state accurate/ordered references, and the old once-cast-input diagnostic. No device arithmetic changes.
- Four focused tests verify that conversion failures stay visible, the original-state trajectory gate still rejects excessive error, empty targets retain all cases, and reordered duplicate masks preserve counts. The full application suite passes **50 tests, zero failures/errors/skips**. [Report](../../evidence/milestone-2/fan-in/tests-cases.xml). Ruff, strict Pyright, and all three import contracts pass.
- Next: execute the complete pinned-data matrix on Metal, preserving inputs, individual results, count expansions, repeatability, and standalone/batch evidence. The builder's unit tests do not qualify device accumulation.
- The installed `qualify-fan-in` command loads the pinned files and writes complete per-target inputs, masks, states, orders, both reference paths, results, failures, and repeat/standalone component checks. Its application/architecture checks pass: **50 tests, zero failures/errors/skips**, Ruff, strict Pyright, and three import contracts. [Report](../../evidence/milestone-2/fan-in/tests-adapter.xml). The first two targets passed all 1,680 cases on Metal; the full run is still executing in `data/results/milestone-2-fan-in-20261004-01`. No full-matrix pass is claimed at this implementation checkpoint.

Complete isolated fan-in qualification (2026-10-04):

- `uv run --locked --group qualification fly-brain qualify-fan-in --output data/results/milestone-2-fan-in-20261004-01` completed with exit status zero at implementation checkpoint `81a8fdd`. All **24,576 cases** from **31 targets**, **70 masks per target**, all prescribed initial states, and **three orders** meet both stored-state one-step and original-state trajectory limits against accurate and ordered float64 references. [Complete matrix report](../../evidence/milestone-2/fan-in/matrix.json).
- Every result and both count components repeat bit for bit and match individually executed cases. Integer count expansions are exact; zero-count updates preserve the initial state's bits. Maximum budget fractions across both references are **0.0237805 one-step** and **0.0244141 trajectory**.
- All **99 original-state one-step failures** remain recorded conversion limitations, not accepted original-state passes. Both original-state trajectory checks pass for every case. [Individual failures and independent verification](../../evidence/milestone-2/fan-in/verification.json).
- A fresh process reloaded the pinned source files, verified every selected original row, reconstructed complete case membership and both reference paths, and reproduced all 24,576 results/count components bit for bit on Metal. [Versioned complete inputs and results](../../evidence/milestone-2/fan-in/inputs-and-results.npz) retain every original field except redundant dense leaves; those leaves reconstruct bit-exactly from counts/masks/orders and recorded widths. Full original artifacts remain locally preserved, with their hashes in the verification record.
- No queue layout, event rule, operation order, compiled expression, or production simulation was introduced. Next: implement the approved stable destination buckets, qualify exact event membership and state transitions, and rerun the 157 scalar and complete 61-test reference/core/factored regressions against the adapted implementation.

Stable host bucket representation (2026-10-04):

- The pure mapping builds the approved 15 power-of-two destination buckets, with original edge identities, float32 integer counts, and explicit occupied masks. Every neuron and all **15,091,983 original connections** appear exactly once, in stable row order within their destinations. Padding uses identity -1, zero count, and a false mask; real zero/silenced rows remain occupied.
- The installed `audit-inputs` command independently verifies destination/count/original-weight identity, the complete edge/target partitions, stable ordering, and minimal widths. The canonical original mapping artifact remains byte-identical to the preceding audit. [Complete host mapping and bucket checksums](../../evidence/milestone-2/buckets/host-mapping.json).
- There are **6,672,741 padding leaves**; the host bucket arrays total **196,437,072 bytes**. This is measured host representation storage, not a device peak-memory benchmark.
- Three new focused tests verify stable padding, exact edge/count/destination recovery, and retained identities under outgoing silencing. The full application suite passes **53 tests, zero failures/errors/skips**. [Report](../../evidence/milestone-2/buckets/application-tests.xml). Ruff, strict Pyright, and all three import contracts pass.
- Device execution, queue/event membership, and full reference/state regression remain the next qualification step.

Bucketed device execution checkpoint (2026-10-04):

- The production preparation path reads original integer connectivity, preserves occupied leaves and source/edge identities, and applies the unchanged factored operation to each destination bucket. Functional concatenation/inverse gathering restores original neuron order. It uses the original integration/threshold helpers and unchanged 19-slot per-edge queue semantics.
- `uv run --locked --group qualification fly-brain qualify --output data/results/milestone-2-bucketed-qualification-20261004-01` passes **79 tests, zero failures/errors/skips**: all 61 original scientific tests remain, plus the same 18 factored fixtures executed through the actual bucketed engine. [Result](../../evidence/milestone-2/buckets/qualification/result.json), [test report](../../evidence/milestone-2/buckets/qualification/tests.xml), [bucketed measurements](../../evidence/milestone-2/buckets/qualification/bucketed_case-networks.json), and [all 55 raw trace hashes](../../evidence/milestone-2/buckets/qualification/manifest.json).
- Live Brian2 comparisons retain every phase-state budget and exact spikes, availability, last-spike clocks, due/accepted/discarded decisions, channel events, and pending-edge queues. The adapted engine passes large cancellation, outgoing silencing, refractory loss/release, batch/standalone, chunked continuation, CPU-default stream isolation, and fresh-state reset checks.
- The default application suite passes **53 tests, zero failures/errors/skips**. [Report](../../evidence/milestone-2/buckets/tests-device-adapter.xml). Ruff, strict Pyright, and all three import contracts pass. The original numerical oracle and operation sequence remain intact.
- Remaining Milestone 2 checks at this checkpoint: the retained 157 scalar cases through the actual layout path, actual pinned-array layout arithmetic/transfer verification, and full-connectome event construction evidence. No complete production simulation, full-network parity, or performance result is claimed.

Bucketed scalar and bounded review checkpoint (2026-10-04):

- `uv run --locked --group qualification fly-brain probe-bucketed --output data/results/milestone-2-bucketed-scalars-20261004-01` completes with exit status zero: **157/157 cases** meet both unchanged original-state budgets through the production layout. Exact count expansions, untouched source states, zero-count copies, repeats, and three-trial versus standalone bits pass. [Complete report and all raw cases](../../evidence/milestone-2/buckets/scalars/bucketed-scalars.json).
- Sol independently checks all artifact/source hashes, original inputs against the retained prototype, literal ordered and accurate references, both budgets, count expansions, repeat/standalone bits, and zero copies. Output/count-component bits match the prototype. The ordered reference for the empty negative-zero case changes from padded `+0.0` to unpadded `-0.0`; numerical reference values agree and required output bits remain negative zero. [Verification](../../evidence/milestone-2/buckets/scalars/verification.json).
- **53 application tests pass, zero failures/errors/skips**; Ruff, strict Pyright, and three import contracts pass. [Report](../../evidence/milestone-2/buckets/scalars/application-tests.xml). No numerical source changed after the recorded 79-test scientific run.
- A fresh-context Astra subagent at explicit `xhigh` finds **no blocking defect** in its bounded implementation review, checks retained evidence, and performs additional Metal checks. [Assignment, decision, verification, and limits](../../evidence/milestone-2/buckets/astra-execution-review.md). Its remaining requirements are the complete prescribed pinned-case replay through the layout, all device fields and gathered event masks, and a complete-connectome delayed pulse. Sol owns these engineering decisions and qualification; no user choice of numerical internals is required.

Pinned layout replay implementation checkpoint (2026-10-04):

- The installed `qualify-layout-fan-in` command injects actual layout execution into the existing fan-in case/report path. It retains the same 31 targets, 70 masks, three orders, all initial states, accurate/ordered references, count/component checks, and every individual execution. Induced incoming networks preserve original neuron identifiers, source membership, signed counts, and row order; every other neuron must retain its exact state bits.
- Ruff formatting/lint, strict Pyright, three import contracts, and **53 application tests, zero failures/errors/skips**, pass. The full Metal run is executing under `data/results/milestone-2-layout-fan-in-20261004-01`; its first 11 targets pass. No complete layout-matrix pass is claimed at this implementation checkpoint.

Complete pinned layout replay checkpoint (2026-10-04):

- The full command completes with exit status zero: **24,576/24,576 cases** meet both stored-state one-step and original-state trajectory gates against both float64 references through actual production layouts. All orders, count expansions, repeats, individual execution bits, zero copies, and untouched source states pass. [Matrix](../../evidence/milestone-2/buckets/pinned-replay/matrix.json).
- Sol independently verifies every artifact/source hash and compares all arrays with the previously independently verified isolated matrix: inputs, references, results, high/low components, repeats, individual runs, and gate flags are byte-identical. All **99 original-state conversion limitations** remain unchanged. [Verification and complete compact inputs/results](../../evidence/milestone-2/buckets/pinned-replay/verification.json).
- This closes the bounded review's prescribed-case requirement. Complete pinned-device field/event gathering and full-connectome delayed pulse remain open. The implementation checkpoint is `7a92065`; production numerical source remains unchanged from the 79-test scientific qualification.

Complete pinned-device representation checkpoint (2026-10-04):

- `uv run --locked --group qualification fly-brain qualify-device-layout --output data/results/milestone-2-device-layout-20261004-01` completes with exit status zero. All 15 buckets' targets, original edge identities, signed counts, occupied masks, padding, and inverse neuron gathering round-trip with exact dtype/shape/bytes. The gathered events match the host prediction at every occupied and padding leaf for all five fixed patterns. [Report and complete results](../../evidence/milestone-2/buckets/device-layout/device-layout.json).
- The patterns accept 15,091,983 / 0 / 9,879 / 94,545 / 3,820,288 original rows. Every one of **693,195 neuron/trial results** has an exact high/low count expansion and meets both original-state budgets against accurate and ordered original-weight references. Repeats, individual runs, and zero-count state bits match exactly. Greatest one-step budget fraction is `0.0236201321`.
- Sol reloads the pinned files, matches all device-field checksums against the previously verified host manifest, regenerates seeded source/receiving masks and every original edge event, and recomputes all exact counts and both references using original rows rather than padded device leaves. Artifact/source hashes and all budgets/component/copy checks pass. [Independent verification](../../evidence/milestone-2/buckets/device-layout/verification.json).
- **53 application tests, zero failures/errors/skips**, full Ruff, strict Pyright, and three import contracts pass. [Report](../../evidence/milestone-2/buckets/device-layout/application-tests.xml). Complete-connectome delayed-pulse construction remains the final Milestone 2 requirement; full experiment parity and performance remain later gates.

Complete-connectome pulse and Milestone 2 completion (2026-10-04):

- `uv run --locked --group qualification fly-brain qualify-connectome-pulse --output data/results/milestone-2-connectome-pulse-20261004-02` completes with exit status zero on all **138,639 neurons and 15,091,983 edges**. The original and outgoing-silenced modes each execute 20 steps with two trials, including a target blocked at delivery. All network fields, complete event masks, every pending queue slot, last-spike clocks, and untouched-neuron bits match at every step. [Report and complete tracked phase arrays](../../evidence/milestone-2/buckets/connectome-pulse/connectome-pulse.json).
- Source index 0 has 62 original outgoing rows. Its step-0 spike arrives at step **18**, and first affects voltage at step **19**. All tracked phase states meet unchanged float64 trajectory limits; arrival also meets the unchanged one-step limit. Greatest phase-state error is `0.000001700346 mV`. Outgoing silencing leaves due/accepted/discarded identities unchanged and produces no conductance or voltage influence.
- Sol independently recovers original rows/identifiers, expected complete event membership and queue counts, all 40 device-check vectors, and analytic float64 phase updates with literal ordered original-weight delivery. Hashes and both budgets pass. [Independent verification](../../evidence/milestone-2/buckets/connectome-pulse/verification.json). The initial `-01` run remains preserved; `-02` strengthens unaffected-state checks to binary representations, with identical raw traces/results.
- **53 application tests, zero failures/errors/skips**, full Ruff, strict Pyright, and three import contracts pass. [Report](../../evidence/milestone-2/buckets/connectome-pulse/application-tests.xml). The prior 79-test live Brian2/core/factored/bucketed suite and all 157 adapted scalar cases remain valid: no production numerical code changed after those runs.
- All remaining requirements from the [bounded Astra execution review](../../evidence/milestone-2/buckets/astra-execution-review.md) are satisfied and independently verified. **Close Milestone 2.** This controlled pulse uses an independent analytic float64 reference; it does not claim live full-network Brian2 comparison, production experiment output, full-network parity, or performance acceptance.

## Milestone 3 — Backend integration

Status: **complete on 2026-10-04**. The normal ten-package installation executes the complete shortest sugar experiment twice with byte-identical schedules and spike files. The complete silent control stays silent and writes the existing typed empty output. Existing comparison readers and commands consume both populated and empty files. Full scientific parity and performance remain later gates.

Acceptance: the normal command-line interface runs the shortest MLX experiment, consumes existing experiment definitions, uses the sole MLX execution backend, writes the existing spike schema, and produces outputs consumable by the analysis tools. Record initialization, compilation, simulation, and collection separately. Preserve device-resident state and avoid complete CPU-device transfers each timestep.

Present and obtain explicit approval for any required application programming interface or database schema change before writing dependent code, as required by the user's standing rules.

Experiment/stimulus checkpoint (2026-10-04):

- Pure immutable experiment/stimulus types preserve the exact upstream sugar/P9 identifier lists and rates. The five frozen parity configurations retain channel order, distinct experiment/generator codes, and outgoing silencing. Sol compares the original definitions directly with the imported upstream source and resolves every identifier against pinned CSV order. [Evidence](../../evidence/milestone-3/stimuli/experiments.json).
- Schedule generation uses pinned NumPy PCG64 seed tuples, float64 row-major step/channel draws, explicit rates, and immutable uint8 event bytes. Each trial is independent of batch size and shorter durations are prefixes. Sugar silencing reuses sugar events exactly; the silent control has a real empty channel dimension.
- Six intent tests cover original channel order under unsorted neuron data, trial/batch/prefix identity, unchanged silenced stimuli, the frozen draw protocol, silent controls, and missing IDs. The complete application suite passes **59 tests, zero failures/errors/skips**, Ruff, strict Pyright, and three import contracts. [Report](../../evidence/milestone-3/stimuli/application-tests.xml). This checkpoint does not run a production experiment or change a database/application programming interface schema.

Normal run/export implementation checkpoint (2026-10-04):

- The installed `simulate` command has a validated request, a thin entrypoint, explicit service/collaborator injection, and the sole MLX engine. It accepts the planned duration/trial options and the five frozen experiments. Normal installation requires only the pinned input files; it does not require the qualification test tree.
- Local stimulus evidence uses immutable uint8 NPZ events and a versioned JSON provenance record. Layout is trial/step/channel, with each trial's canonical row-major step/channel bytes, seed tuple, hash, rates/IDs, and original data pins. The adapter reloads and verifies those exact bytes before execution. This is a recorded local-file engineering decision; no database or HTTP endpoint contract changes are required.
- The engine keeps voltage/current/clocks/queues on explicit Metal streams and preserves the qualified update. It collects 256-step blocks of spike events, retains exact integer steps and trial identities, and restores original output ordering. Setup, first step, warm steps, collection, input/output, compilation-disabled state, and [MLX allocator peak](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.get_peak_memory.html) are recorded separately; the allocator value is not total system memory.
- Parquet output retains `t`/`time_ms` doubles, `trial`/`neuron_index`/`flywire_id` int64, `exp_name` string, the existing filename convention, and Brotli compression. Empty files use these same existing column types. Real file tests verify both empty/populated exports and existing comparison-reader consumption.
- **66 application tests, zero failures/errors/skips**, full Ruff, strict Pyright, and three import contracts pass. [Application report](../../evidence/milestone-3/integration/application-tests.xml). The full live scientific qualification passes **80 tests, zero failures/errors/skips**: all 79 prior tests plus a production collection test spanning 513 steps, two distinct trials, and three collection blocks. [Result](../../evidence/milestone-3/integration/result.json), [test report](../../evidence/milestone-3/integration/tests.xml), and [all 56 trace hashes](../../evidence/milestone-3/integration/manifest.json).
- Next: execute the shortest complete sugar experiment from a fresh normal runtime, verify persisted schedule/output/schema/compression/analysis, repeat it, and test the complete silent control. No full experiment or parity pass is claimed at this implementation checkpoint.

First production-run checkpoint (2026-10-04):

- Implementation `c863ed8` runs from a fresh noneditable ten-package normal runtime with exit status zero. The complete pinned sugar experiment at 0.1 seconds and one trial produces **1,612 spikes from 335 neurons**. [Run report](../../evidence/milestone-3/production-sugar/simulation.json), [execution log](../../evidence/milestone-3/production-sugar/run.log), and [exact spike coordinates](../../evidence/milestone-3/production-sugar/spike-events.npz) are retained.
- Independent verification checks both data pins, all ten installed/checkout source hashes, original experiment identifiers/rates/order, regenerated canonical stimulus bytes, complete CSV identifier mapping, exact six-column types, Brotli compression, valid unique ordered step/trial/neuron coordinates, counts, and existing comparison-reader consumption. [Verification and installation record](../../evidence/milestone-3/production-sugar/verification.json), [stimulus provenance](../../evidence/milestone-3/production-sugar/stimulus.json), and [canonical events](../../evidence/milestone-3/production-sugar/stimulus.npz).
- This execution takes **51.600719 seconds**: data load 3.071755, device setup 9.832647, first step 0.651656, remaining steps 37.499551, and collection 0.394501 seconds. Compilation is disabled; MLX allocator peak is 1,607,040,478 bytes. These are one-run execution measurements, not a benchmark acceptance claim. Repeatability, the silent control, and full-network scientific parity remain open. Commit this evidence before beginning the next run, as required by checkpoint `e766ea2`.

Production repetition checkpoint (2026-10-04):

- A second fresh-process shortest sugar run exits successfully with **1,612 spikes from 335 neurons** in 48.981883 seconds. Both complete Parquet files, every typed column and integer spike coordinate, stimulus archives/metadata, and source/data/dependency hashes match exactly. [Repeat report](../../evidence/milestone-3/production-sugar-repeat/simulation.json) and [independent verification](../../evidence/milestone-3/production-sugar-repeat/verification.json).
- The installed normal runtime's `compare` command reads both complete outputs and produces exact agreement: activity Jaccard, count ratio, shared rate correlation, and timing F1 are 1; all 1,612 matches have zero timing difference. [Existing-tool output](../../evidence/milestone-3/production-sugar-repeat/pairwise_summary.json). This proves production-output repeatability; complete state/queue repeatability and scientific parity remain Milestone 4 requirements. Next: complete silent control, with this result committed first.

Silent-control and integration completion checkpoint (2026-10-04):

- The normal installed runtime executes the complete 138,639-neuron/15,091,983-edge silent control for 1,000 steps with **zero spikes and zero active neurons**, exit status zero, in 51.283983 seconds. Canonical input has shape `(1, 1000, 0)`, no channels or silenced neurons, the correct seed tuple, and independently regenerated empty bytes. [Run report](../../evidence/milestone-3/production-silent/simulation.json), [stimulus provenance](../../evidence/milestone-3/production-silent/stimulus.json), and [verification](../../evidence/milestone-3/production-silent/verification.json).
- The real empty Parquet file retains all six original column types and Brotli compression. Both the existing reader and installed comparison command consume it with zero events. [Comparison output](../../evidence/milestone-3/production-silent/pairwise_summary.json). Legacy empty-score conventions remain unchanged; the frozen Milestone 4 acceptance layer has its separately specified empty-agreement rules.
- **Close Milestone 3.** All required normal-run, shared-input, file-contract, installation, repeat-output, and analysis-consumption checks are recorded. The unchanged implementation retains its 66 application/80 scientific test results, zero skips/failures/errors, and complete quality gates. Next: build and qualify the frozen full-network scientific comparison, including complete state/queue repeatability and first-divergence diagnosis. No full-network parity or benchmark pass is inferred from integration.

## Milestone 4 — Full-network parity

Status: in progress. **Nine of 52 required three-engine cases are accepted:** sugar, P9, silenced sugar, two-class, and silent trial 0, plus sugar trials 2–4, at 0.1 seconds have exact MLX/Brian2 spikes; sugar trial 1 at 0.1 seconds has a separately recorded parent acceptance under the prospectively approved explained-roundoff condition. All five sugar trials at 0.1 seconds are accepted. Every fixed/paired metric and complete causal/native replay requirement passes for each accepted case. The remaining 43 cases, complete prescribed repeat/batch checks, complete matrix summaries, and full-network parity approval remain open.

Acceptance: execute the [frozen 52-case matrix and protocol](../numerical-contract.md#full-network-acceptance-fixed-before-validation) through Brian2, the pinned PyTorch numerical core with common experiment setup/replay, and MLX. Sugar and p9 cover 0.1/1/10 seconds with five paired trials; silenced sugar and two-class stimulation cover 0.1/1 seconds with five trials; silent controls cover both shorter durations. Repeat each case and execute the specified batch checks.

Every case must satisfy active Jaccard ≥0.95, relative total count error ≤0.02, normalized neuronwise count error ≤0.05, common-support rate correlation ≥0.99 when defined, and one-to-one timing F1 ≥0.95 within 1 ms. MLX must also be no worse than PyTorch on **every** primary metric for that case, with the documented empty/undefined rules. Require deterministic replay and an explained first divergence; aggregate averages cannot rescue failures. These thresholds precede all full-network MLX results. Obtain a bounded Astra parity adjudication if interpretation is required; do not relax the frozen criteria retrospectively.

Evidence-design assignment (2026-10-04): [bounded handoff](../handoffs/astra-full-network-evidence.md). Fresh-context Astra at explicit `xhigh` reviews a complete-reference observer/chunk method, actual state/queue replay evidence, and first-cause coverage within local memory. Sol awaits and independently verifies the decision before dependent instrumentation. Pure frozen acceptance-metric implementation is independent. The review has no authority to change the model, references, tolerances, schema, or project scope.

Metric-calculation checkpoint (2026-10-04):

- Pure [comparison calculations](../../../src/fly_brain/comparison/acceptance.py) use integer per-case spike steps, the union of all three engines' active neurons, exact rational activity/count/timing metrics, and full-precision common-support correlation. Missing-neuron zeros, inclusive ten-step one-to-one matching, exact/one-step diagnostics, and explicit empty/undefined values follow the frozen contract. Existing rounded comparison outputs remain unchanged.
- Nine intent tests cover common support, missing neurons, integer timing boundaries/nonreuse, distinct diagnostic windows, exact silence with active PyTorch, empty candidates, zero denominators, and row-order independence. An initial empty-group bug caused three failures and was corrected before this checkpoint. **75 application tests pass, zero failures/errors/skips**; full Ruff, strict Pyright, three import contracts, and the offline lock check pass. [Test report](../../evidence/milestone-4/metrics/application-tests.xml) and [verification/source hashes](../../evidence/milestone-4/metrics/verification.json).
- This step calculates metrics only. Fixed absolute/paired gate execution, validated case inputs, actual-engine trace capture, and full-network comparison remain open. The production numerical engine is unchanged; its retained 80-test scientific qualification is not a new run of this metric code. Commit this verified unit before adding gates.

Evidence-design review completion (2026-10-04):

- Fresh-context Astra at explicit `xhigh` returns the [bounded decision](../../evidence/milestone-4/evidence-design/astra-review.md). Select one continuous Brian2 C++ run, three actual all-neuron phase monitors, and an appended observer that streams/clears only bounded monitor storage. Inspect actual recurrent/replay queues and counters; distinguish physical repeat digests from normalized pending-event comparisons. MLX uses the unchanged update with bounded phase capture and complete device queue/event checks. No reconstructed ledger is mislabeled as an observed queue.
- Sol independently inspects insertion/scheduling order, monitor storage behavior, public queue fields, and actual MLX edge-queue dimensions; the installed queue source matches the retained C++ build exactly. [Source verification](../../evidence/milestone-4/evidence-design/verification.json). The review and parent ran no observer simulation: transparency, integrity, complete/four-trial memory, causal evidence, and parity still require execution qualification. Implement the small-network observer proof before full-network wiring, retaining all frozen gates. Pure metrics are committed at `73ceebc`.

Metric-gate checkpoint (2026-10-05):

- Execute all five frozen absolute and paired metric gates, including exact silent-reference agreement and the exact count-vector fallback for undefined correlation. Rational comparisons have no tolerance; only paired computed correlation permits the frozen `1e-12` host slack. A weak PyTorch result cannot excuse an absolute failure, and a one-spike degradation cannot hide inside comparison slack.
- Eighteen new boundary/intent cases verify inclusive fixed thresholds, paired exactness, silence, empty candidates, constant vectors, undefined PyTorch correlation, and limited host correlation slack. **93 application tests pass, zero failures/errors/skips**; full Ruff, strict Pyright, and all three import contracts pass. [Test report](../../evidence/milestone-4/gates/application-tests.xml) and [verification/source hashes](../../evidence/milestone-4/gates/verification.json). Source-supported observer design is committed at `178aa9b`.
- Metric acceptance is one required component. Validated data/setup, actual-engine observer transparency, deterministic full-state/queue/batch evidence, causal diagnosis, and every full-network case remain open. This pure step does not change or requalify the production numerical engine. Commit it before observer implementation.

Observer-transport checkpoint (2026-10-05):

- The qualification-only [stream reader](../../../src/fly_brain/qualification/adapters/observer_stream.py) checks version/dimensions, chronological steps and bounded phase blocks, canonical Boolean data, actual physical queue offsets/slots/order, final observations, and per-frame CRC-32 (32-bit cyclic redundancy check). Bounded reads support partial pipe delivery. It rejects truncated, omitted, reordered, changed, and trailing frames, including a missing final observation block.
- Fourteen intent cases prove complete intermediate/final field decoding, partial reads, preserved queue entries, and explicit transport fault detection. **107 application tests pass, zero failures/errors/skips**; full Ruff, strict Pyright, and three import contracts pass. [Test report](../../evidence/milestone-4/observer-stream/application-tests.xml) and [verification/source hashes](../../evidence/milestone-4/observer-stream/verification.json). Fixed metric gates are committed at `dae7284`.
- This validates the internal reader only. The live reference observer, actual queue ledger, stock-monitor equivalence, complete/four-trial memory, and all full-network scientific checks remain open. Next: connect the small-network C++ observer to this tested format and prove numerical/recording transparency. Commit transport before beginning that step.

Small reference-observer prototype checkpoint (2026-10-05):

- The qualification-only [C++ observer](../../../src/fly_brain/qualification/adapters/brian_observer.py) appends one callback to one continuous reference run. It reads actual physical recurrent/input queues, delivery order, neural/source spikes, clocks, and replay cursor; it clears only recorded monitor rows, timestamps, and monitor-local length. Model state and numerical functions remain untouched by the observer code.
- Five live [prototype checks](../../../tests/qualification/test_brian_observer.py) pass, zero failures/errors/skips, through four fresh C++ builds. The 101-step six-neuron fixture includes duplicate/self connections, zero-weight and silenced outgoing rows, overlapping input channels, zero/ordinary refractory periods, repeated queue wraps, and a nonempty final pending queue. Stream sizes 1, 17, and 32 reproduce every raw stock-monitor phase/final byte, spike coordinate, and observed physical queue/cursor value from the uncleared-monitor mode.
- Command: `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync pytest -q tests/qualification/test_brian_observer.py --disable-warnings --artifact-output data/results/milestone-4-observer-prototype-20261005-01`. All four builds, binary streams, input arrays, and phase archives remain in that fresh local directory. The 107 application tests and full Ruff, strict Pyright, and three import contracts pass.
- This bounded proof compares cleared/uncleared monitors with the same read-only observer. It does not yet prove independently correct queue contents, generated-code/scheduling identity, equality with fully uninstrumented execution, complete-network memory, or scientific parity. Commit this verified prototype before adding those checks; later complete evidence receives a separate checkpoint.

Small reference ledger/source checkpoint (2026-10-05):

- Extend the prototype committed at `05e0746` with a stock run that has no appended observer. All four observer modes reproduce every stock phase/final array and spike coordinate byte for byte. An independently constructed original-row event ledger verifies every physical queue offset, ordered slot/delivery, source input, and cursor at all 101 steps, including the final pending queue.
- All 64 generated numerical/support files, compiler flags, and static initialization arrays are byte-identical. The ordinary numerical callback order and single continuous run invocation are unchanged; the observer callback follows the last end monitor. Main initialization differs only by one extra consecutive assignment of the same `0.0001` clock value in the first fresh build.
- Engineering decision at `05e0746`, confidence **99%**: normalize only consecutive identical literal clock assignments for the main-source identity check. Direct source diff proves no other initialization change; the executed clock, every monitored state, and all spikes also agree exactly. Numerical functions, initial values, schedules, tolerances, and compiler options are not normalized or changed.
- Eight targeted tests pass, zero failures/errors/skips, in fresh output `data/results/milestone-4-observer-ledger-20261005-02`; full Ruff and strict Pyright pass. The preceding seven-pass/one-failure source check and its fresh build directory remain preserved. This proves small stock-observer/queue/source transparency; complete-network execution, memory, causal capture, and parity remain open. Commit these verified checks before the complete regression/evidence step.

Reference-observer regression/evidence checkpoint (2026-10-05):

- Implementation and checks are committed at `05e0746` and `83316a8`. The installed qualification command runs the complete suite: **88 passed, zero failures/errors/skips**, in 85.66 seconds. [Result](../../evidence/milestone-4/reference-observer/result.json), [test report](../../evidence/milestone-4/reference-observer/tests.xml), and [execution log](../../evidence/milestone-4/reference-observer/qualification.log). The separate [application report](../../evidence/milestone-4/reference-observer/application-tests.xml) records **107 passed, zero failures/errors/skips**. Full Ruff, strict Pyright, three import contracts, and the 38-package offline lock check pass.
- Independent evidence inspection decodes every actual queue/cursor/frame, reconstructs all phase arrays, validates all 101 clocks, checks every original-row ledger slot/delivery, and compares every stock/observed/final/raster byte. Each mode also repeats byte for byte against the earlier fresh targeted builds. [Verification and source hashes](../../evidence/milestone-4/reference-observer/verification.json), [all 62 trace hashes](../../evidence/milestone-4/reference-observer/trace-manifest.json), [original inputs](../../evidence/milestone-4/reference-observer/input.npz), [stock trace](../../evidence/milestone-4/reference-observer/block-None-phases.npz), [32-step trace](../../evidence/milestone-4/reference-observer/block-32-phases.npz), [actual framed queues/state](../../evidence/milestone-4/reference-observer/block-32-observer.bin.gz), and [generated sources/initialization](../../evidence/milestone-4/reference-observer/generated-source.zip) are retained.
- The complete fresh local build/trace directory is `data/results/milestone-4-observer-regression-20261005-01`; earlier prototype and failed/refined targeted directories remain preserved. This closes the small reference observer proof, including complete-suite coexistence and fresh-build replay. Next: bounded MLX observation and independent full-layout queue checks, followed by complete short-run observer transparency and measured memory. Full-network scientific parity and performance remain open. Commit this execution evidence before the next implementation step.

MLX device-ledger implementation checkpoint (2026-10-05):

- The qualification-only [device ledger](../../../src/fly_brain/qualification/adapters/mlx_ledger.py) derives event expectations from actual spikes and independently supplied original source/destination/input metadata. It checks every actual due/accepted/discarded event, input gate, availability/threshold/receiving flag, last-spike clock, and all 19 physical pending queue slots. It also detects nonfinite pre-threshold, pre-reset, and end state. Only a 19-step neuron-spike history is retained; complete edge queue histories are not collected.
- Eighteen [live Metal tests](../../../tests/qualification/test_mlx_ledger.py) pass, zero failures/errors/skips. Four 101-step cases cover one/four independent trials and empty/nonempty edge sets, duplicate/self edges, zero/silenced weights, blocked and accepted arrivals, overlapping inputs, repeated queue wraps, and pending final events. Deliberately changed event/queue/clock bits and nonfinite phase values are detected. Raw small-network state/trace/check arrays remain in fresh output `data/results/milestone-4-mlx-ledger-20261005-02`.
- The first harness run recorded nine passed/nine failed tests because I used an unsupported MLX mutation method in fault injection. The corrected tests use supported functional operations; the failed log/report and first directory remain preserved. Full Ruff, strict Pyright, and three import contracts pass. The production numerical source is unchanged; the retained complete 88-test scientific result remains the prior checkpoint's result, not a rerun for this new checker.
- This qualifies the small device ledger. Bounded phase capture, stock MLX trace equivalence, complete-layout observer execution/memory, causal capture, and all full-network parity gates remain open. Commit this verified checker before phase-observer implementation.

Bounded MLX phase-observer checkpoint (2026-10-05):

- The qualification-only [MLX observer](../../../src/fly_brain/qualification/adapters/mlx_observer.py) calls the existing execution function and captures at most 32 steps of raw pre-threshold, pre-reset, end, discrete-clock, spike, and input observations. The ledger committed at `1db6572` checks actual complete queues/events on the device each step. Only phase/check blocks and actual queue hashes cross to the host at block boundaries; the actual final queue is retained. No queue history is collected in this observer.
- Ten [live Metal checks](../../../tests/qualification/test_mlx_observer.py) pass, zero failures/errors/skips, in fresh output `data/results/milestone-4-mlx-observer-20261005-02`. Sizes 1, 17, and 32 reproduce every ordinary raw phase/spike/clock/input and final queue byte across four trials, with both empty and populated edge sets. Independently hashed ordinary queue arrays match every observed per-trial boundary digest. Repeated phase/queue digests and final arrays match exactly; actual four-trial observations match all four separately initialized trials byte for byte. Invalid zero/over-limit block sizes are rejected.
- Full Ruff, strict Pyright, and three import contracts pass. The production engine, arithmetic, and experiment/output contracts are unchanged. This qualifies the small MLX observer; the complete combined regression/evidence checkpoint follows after committing this implementation. Complete-network memory/transparency, paired causal capture, PyTorch full-state observation, and all 52 scientific cases remain open.

Combined observer regression/evidence checkpoint (2026-10-05):

- MLX ledger/capture implementations are committed at `1db6572` and `45637a4`. The installed qualification command completes **116 scientific tests, zero failures/errors/skips**, in 101.42 seconds. [Result](../../evidence/milestone-4/mlx-observer/result.json), [test report](../../evidence/milestone-4/mlx-observer/tests.xml), and [execution log](../../evidence/milestone-4/mlx-observer/qualification.log). The [application report](../../evidence/milestone-4/mlx-observer/application-tests.xml) records **107 passed, zero failures/errors/skips**; full Ruff, strict Pyright, three import contracts, and the offline 38-package lock check pass.
- Independent host inspection verifies every actual event, gate, clock, and physical queue entry in all four small device-ledger archives. It verifies every ordinary/captured phase and final queue byte in all six partition/empty-edge archives; each archive also matches the earlier fresh targeted run byte for byte. Separate new Metal executions retain all raw repeated and four independently initialized trial records, with exact per-block phase/check/queue-digest and final-array equality. [Verification and source hashes](../../evidence/milestone-4/mlx-observer/verification.json), [all 72 raw trace hashes](../../evidence/milestone-4/mlx-observer/trace-manifest.json), [actual repeat arrays](../../evidence/milestone-4/mlx-observer/recorded-repeat.npz), and [actual batch/single arrays](../../evidence/milestone-4/mlx-observer/recorded-batch-versus-single.npz).
- All fresh local outputs remain under `data/results/milestone-4-observer-combined-20261005-01`; compact MLX traces and failed/refined targeted reports are versioned with the verification. This closes the small reference/MLX observer and complete regression proof. Next: continuously streamed reference jobs, paired causal checks, complete short-run transparency, and measured concurrent memory. PyTorch observation and every frozen full-network parity case remain open. Commit this execution evidence before the next implementation.

Streamed reference-job implementation checkpoint (2026-10-05):

- The qualification-only [job adapter](../../../src/fly_brain/qualification/adapters/brian_jobs.py) compiles the pinned reference without running it, then consumes one continuous C++ run through a bounded pipe. Native result files and process errors remain in fresh directories; the raw stream is not saved to disk. Original signed counts are multiplied by Brian2's original unit-bearing scale, with original row order, outgoing silencing, resting initialization, and replay scheduling preserved. Runtime version, float64 state/time, single-thread queues, and frozen compiler flags are checked.
- Engineering decision at `8fc14de`, confidence **99%**: reuse the compiled binary for repeated identical inputs, while starting each trial execution in a fresh process and a new result directory. The generated program initializes all state and reads the same retained static inputs on each start; numerical execution is never split or resumed.
- Two [live job checks](../../../tests/qualification/test_brian_jobs.py) pass, zero failures/errors/skips, in `data/results/milestone-4-reference-jobs-20261005-01`. Streamed final state and spikes match ordinary execution without phase monitors or an appended observer. Every raw phase and native final array repeats exactly through the reused binary; the partial final block is present and no raw stdout file is created. The compile-only result directories are empty before execution. **107 application tests pass, zero failures/errors/skips**; full Ruff, strict Pyright, and three import contracts pass.
- This verifies small live-pipe execution and fresh-process reuse. Detailed queue/cursor replay, child-process fault handling, complete-network observer transparency/memory, paired causal capture, and the full matrix remain open. The complete 116-test scientific result is the prior checkpoint's evidence. Commit this verified working state before adding further checks.

Reference-process failure checkpoint (2026-10-05):

- The live-pipe implementation is committed at `d3f8e10`. Three focused real-process checks pass, zero failures/errors/skips: nonzero execution fails with its retained error log, a corrupt stream stops its owned child, and closing an incomplete stream stops its owned child. Each cleanup check verifies that the specific child no longer exists. The two model-run checks retain their preceding successful execution; they were deselected in this focused process check.
- The adapter's generator type now exposes its supported close operation to callers. Full strict Pyright, Ruff, and format checks pass. This small verified process-lifecycle unit is committed before queue replay checks; no production or reference numerical function changes.

Live-pipe replay/scaling checkpoint (2026-10-05):

- Process-lifecycle checks are committed at `c0b7ffe`. The seven-check reference-job module now passes together, zero failures/errors/skips, in fresh output `data/results/milestone-4-reference-jobs-20261005-02`. Every physical queue slot, ordered delivery, neural/source spike vector, raw clock, and source cursor repeats exactly through the live pipe, including the actual final pending queues. Native weights in all three result directories retain the original count-times-unit-scale operation and every zero/silenced row.
- Full Ruff, formatting, and strict Pyright pass. This is small reference execution evidence; complete-network observer execution, measured memory, causal checks, and scientific parity remain open. Commit this verified unit before further implementation.

Reusable reference-ledger checkpoint (2026-10-05):

- Replay/scaling checks are committed at `a710bcd`. The [reference ledger](../../../src/fly_brain/qualification/adapters/reference_queues.py) independently groups original outgoing rows and checks every actual recurrent/replay queue slot, ordered delivery, channel bit, cursor, and final spike space. Its pending expectations retain at most 19 due steps. Expectations are derived from actual spikes and original row identities; they do not replace the observed queue.
- All eight live reference-job checks pass, zero failures/errors/skips, in fresh output `data/results/milestone-4-reference-jobs-20261005-03`. Full strict Pyright, Ruff, and three import contracts pass. Fault injection for this reusable checker and complete-network execution remain next. Commit this verified working state now; no numerical function changed.

Retained reference-ledger proof checkpoint (2026-10-05):

- The reusable ledger is committed at `0d482d7`. Four additional file-boundary checks consume the preserved actual reference streams for block sizes 0, 1, 17, and 32. Every original-row queue, delivery, replay cursor/channel, and final observation agrees, including the earlier stress fixture's zero/silenced rows and queue wraps. The **111-test application suite passes with zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass.
- The stream reader now types the single byte-read operation its consumers need. Real pipes, compressed binary files, and in-memory streams satisfy that small interface directly; no runtime behavior or transport bytes change. Commit this working state before fault injection.

Reference-ledger fault checkpoint (2026-10-05):

- Retained-stream integration is committed at `cee1599`. Forty-four additional fault cases across all four actual transport modes reject changed source cursors/channels, invalid/duplicate spikes, shifted clocks, altered queue offsets/delivery/order, lost pending rows, changed replay queues, and changed final spike space. The **155-test application suite passes with zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass.
- These failures are deliberately injected into decoded observations; the model and retained data are preserved. The independent checker is ready for complete-network queue validation. Scientific full-suite coexistence and complete-network observer transparency/memory remain open. Commit this passing unit before those executions.

Reference setup/source checkpoint (2026-10-05):

- Ledger fault coverage is committed at `3f1d6b0`. The complete reference-job module now passes **12 tests, zero failures/errors/skips**, in fresh output `data/results/milestone-4-reference-jobs-20261005-05`. Every ordinary numerical code object and original static input is byte-identical with phase capture enabled. Actual neuron initialization statements, core callback order, one continuous run, and the appended observer position agree. Silent input, empty recurrent edges, and no-pathway execution preserve their actual queue geometry and expected spikes.
- I initially guessed the generated source's index name and scalar formatting in one assertion. The resulting eleven-pass/one-failure report and build directory `data/results/milestone-4-reference-jobs-20261005-04` remain preserved. The corrected test compares actual initialization statements exactly, without normalizing their values or changing the model. Full strict Pyright, Ruff, and formatting pass. Commit this passing setup unit before complete-network execution; complete regression/evidence follows separately.

Reference-job regression/evidence checkpoint (2026-10-05):

- Setup/source checks are committed at `e49d5b1`. The installed qualification command completes **128 scientific tests, zero failures/errors/skips**, in 128.23 seconds. [Result](../../evidence/milestone-4/reference-jobs/result.json), [test report](../../evidence/milestone-4/reference-jobs/tests.xml), and [log](../../evidence/milestone-4/reference-jobs/qualification.log). The [application report](../../evidence/milestone-4/reference-jobs/application-tests.xml) records **155 passed, zero failures/errors/skips**; full Ruff, strict Pyright, three import contracts, and the 38-package offline lock check pass.
- Independent inspection compares all 41 ordinary and 60 observed/repeated native result arrays against their earlier fresh execution, with exact bytes. Observed/repeated arrays and common ordinary arrays also match each other. [Verification/source hashes](../../evidence/milestone-4/reference-jobs/verification.json), [72 raw trace hashes](../../evidence/milestone-4/reference-jobs/trace-manifest.json), [native arrays](../../evidence/milestone-4/reference-jobs/native-results.zip), and [generated numerical/support source and static inputs](../../evidence/milestone-4/reference-jobs/generated-source.zip). Initial/refined source-check reports are retained.
- Full local outputs remain in `data/results/milestone-4-reference-jobs-regression-20261005-01`. This closes small continuously streamed reference execution, fresh-process reuse, all setup paths, process failure handling, and the independent queue check. Next: the complete shortest observer run with ordinary/repeat evidence and measured reference memory, then paired causal checks and concurrent/four-trial memory. Full-network scientific parity remains open. Commit this execution evidence before continuing.

Complete shortest reference-observer checkpoint (2026-10-05):

- The complete regression is committed at `0faec9b`. The qualified job/observer runs the pinned **138,639-neuron, 15,091,983-row** sugar experiment for **1,000 steps / 0.1 seconds**, trial 0, with the frozen 21-channel schedule and 417 events. Its stimulus hash matches the Milestone 3 run. Ordinary execution, observed execution, and a fresh-process observed repeat all produce **1,612 spikes / 335 active neurons**, with identical raw native neural state, clocks, replay cursor, and spike output.
- Every actual recurrent/replay queue slot, delivery order, input channel, and cursor passes the independent original-row ledger at all 1,000 steps and the final pending observation. All **1,001 physical snapshot digests** and **32 complete all-neuron raw phase blocks** repeat exactly; the eight-row final block is present. Every phase is finite. Actual final neural/pending-queue arrays and native outputs are retained; no approximately 7.8 GB raw phase stream is saved to disk. All ordinary numerical code objects and static inputs match the observed build exactly.
- [Complete observations, raw hashes, timings, and memory samples](../../evidence/milestone-4/full-reference-observer/reference-observer.json), [independent verification and scope](../../evidence/milestone-4/full-reference-observer/verification.json), [actual final pending queues/state](../../evidence/milestone-4/full-reference-observer/observed-observed-final.npz), [native reference output](../../evidence/milestone-4/full-reference-observer/ordinary-native.npz), [stimulus](../../evidence/milestone-4/full-reference-observer/stimulus.npz), [executed proof](../../evidence/milestone-4/full-reference-observer/executed-proof.py), and [generated source](../../evidence/milestone-4/full-reference-observer/generated-source.zip) are versioned. Full builds/native files remain in `data/results/milestone-4-full-reference-observer-20261005-01`.
- Observed/repeated capture takes **51.045 / 51.648 seconds**, versus **1.879 seconds** for this ordinary execution. These are qualification overhead measurements, not an MLX benchmark. The sampled resident-size sum for the proof process and its direct reference child peaks at **1,515,913,216 bytes** during execution/capture. It excludes load/build/source checks, can double-count shared pages, and does not measure total unified memory or concurrent/four-trial MLX memory.
- This closes the complete shortest reference observer transparency/repeat proof. The separately committed **128 scientific / 155 application tests, zero skips**, remain the unchanged-source qualification. Next: paired causal capture and complete MLX observation with actual repeat/ordinary evidence, followed by concurrent/four-trial memory and the frozen matrix. No paired MLX/PyTorch scientific case is accepted by this reference-only result. Commit this execution evidence before proceeding.

Paired causal-audit implementation checkpoint (2026-10-05):

- The complete reference observer proof is committed at `592b9c1`. The pure [causal audit](../../../src/fly_brain/qualification/causality.py) records the earliest chronological trajectory-budget violation and first different spike step/identities. It checks every pre-threshold scalar through the first different step, and checks pre-reset/end state only while that step's spikes still agree. It retains finite-state and consecutive-step requirements after divergence, using the unchanged `1e-3 + 1e-5*abs(reference)` mV budget.
- Three initial intent cases verify every neuron across all three phases. **158 application tests pass, zero failures/errors/skips**; full strict Pyright, Ruff, formatting, and all three import contracts pass. The new pure module is covered by the framework-dependency contract. This verifies the basic classifier; inclusive boundaries, first-divergence sequencing, fault cases, raw-context collection, and live paired-engine wiring remain next. Commit this working state before those checks.

Causal-audit sequencing checkpoint (2026-10-05):

- Basic auditing is committed at `8e90dc6`. Nine additional intent cases prove the first different step's inclusive pre-threshold coverage, exclusion of that step's later phases and all later unforced state comparisons, exact budget inclusivity without added slack, retention of the earliest phase/neuron error, continued nonfinite detection, and rejection of omitted steps. **167 application tests pass, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass.
- This qualifies the pure sequencing rules, not live paired-engine causal evidence. Raw-context capture, complete MLX observer proof, concurrent/four-trial memory, PyTorch observation, and the matrix remain open. Commit this passing unit before the next implementation or execution.

Causal relative-budget checkpoint (2026-10-05):

- Sequencing checks are committed at `a9ec01e`. Two additional cases require the unchanged relative budget term for both positive and negative reference state; removing that term would fail these tests. **169 application tests pass, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass. The fourteen pure causal-audit cases now cover the fixed formula and chronology. Live paired wiring and full case evidence remain open. Commit this verified working state before proceeding.

Causal-audit evidence checkpoint (2026-10-05):

- The classifier and its checks are committed at `8e90dc6`, `a9ec01e`, and `51a1186`. The [169-test application report](../../evidence/milestone-4/causality/application-tests.xml) records zero failures/errors/skips, and [verification/source hashes](../../evidence/milestone-4/causality/verification.json) fix the fourteen causal intent cases, unchanged budget, chronology, and bounded claim. Full strict Pyright, Ruff, formatting, and the new pure-module import boundary pass.
- The scientific 128-test result and complete reference observer proof remain their separately recorded unchanged-source evidence. Next work is live paired reference/MLX block wiring and actual first-cause context, followed by complete MLX ordinary/repeat proof and measured concurrent/four-trial memory. No full-network parity case is accepted by this pure audit evidence. Commit this evidence before the next implementation.

Live paired-block checkpoint (2026-10-05):

- From clean `aa1c9d8`, the [paired observer](../../../src/fly_brain/qualification/adapters/paired_observer.py) consumes the live reference pipe and actual MLX blocks together, checks every reference physical queue and MLX ledger flag, hashes native phase arrays before conversion, and requires complete block/final coverage. Capture remains bounded to at most 32 steps.
- The live six-neuron, 101-step test passes, zero failures/errors/skips, including the five-row final block and native float64/float32 observations. The unchanged application suite passes **169 tests, zero failures/errors/skips**; full Ruff, strict Pyright, and all three import contracts pass. This verifies transport alignment; live causal comparisons/context and complete MLX transparency remain next. Commit this working state before further changes.

Live causal-comparison checkpoint (2026-10-05):

- Paired transport is committed at `26b1463`. The paired adapter now checks real phase timestamps, compares all-neuron voltage/synaptic state after hashing native arrays, and requires exact refractory flags and last-spike clocks while history is common. The first different step retains inclusive pre-threshold coverage; later unforced discrete/state closeness is excluded while finite-state checks continue.
- The independent live Brian2/MLX resting-state fixture completes all 101 steps with **no spike difference or state-budget violation**; its test passes with zero failures/errors/skips. Full strict Pyright, Ruff, and formatting pass. Raw first-cause context and fault injection remain next; no full-network acceptance follows from this small fixture. Commit this working state now.

Paired-coverage fault checkpoint (2026-10-05):

- Live causal comparison is committed at `1d17c0e`. Six injected faults reject an omitted MLX block, shifted block start, unequal row count, failed actual-queue check, missing final reference state, and extra reference output. The faults alter decoded evidence, not numerical execution or stored inputs.
- The live paired module passes **seven tests, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass. Commit this verified unit before causal-context implementation.

Causal-field fault checkpoint (2026-10-05):

- Coverage checks are committed at `5cb85c9`. Paired capture now rejects missing ledger flags instead of treating an empty Boolean array as a successful check. Six additional faults reject changed phase timestamps, nonfinite reference last-spike clocks, incorrect pre-threshold/end refractory state, changed MLX last-spike clocks, and nonfinite neural state.
- Three raw-hash tests require precision, shape, and native units to affect the digest. The live paired module passes **17 tests, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass. No numerical execution changes. Commit this verified working state before first-cause capture.

Actual MLX due-event checkpoint (2026-10-05):

- Decision at `28c5d43`, confidence **99%**: transfer each actual returned due-edge mask and immediately retain only its sparse original-row indices. This meets the approved first-cause requirement while avoiding full queue histories; numerical execution and device-resident propagation remain unchanged.
- The bounded MLX observer now carries actual due identities for every step/trial. They match ordinary returned due masks, repeat byte for byte, and agree between four-trial and independent execution, including empty layouts and partial blocks. The MLX/paired observer modules pass **27 tests, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass. Complete-network memory/capture remains unmeasured. Commit this working state before further context wiring.

Actual paired-event checkpoint (2026-10-05):

- Sparse due capture is committed at `be11cd2`. Each actual MLX due mask is now hashed before its sparse conversion; raw hashes repeat exactly and agree between batch and independent execution. While spike history is common, paired auditing compares actual MLX original-row identities with the reference's actual delivered rows, preserving the reference's separate delivery order for diagnosis.
- Injected missing, extra, and reordered MLX due rows are rejected. The MLX/paired modules pass **30 tests, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass. First-cause context and complete-network observation remain next. Commit this verified unit now.

Raw first-cause capture checkpoint (2026-10-05):

- Actual paired-event checks are committed at `e7ff0bc`. The [causal capture](../../../src/fly_brain/qualification/adapters/causal_capture.py) preserves the current and preceding raw observations for the first state-budget error and first spike difference. It retains actual reference snapshots/delivery order, raw neural/refractory/clock/input fields, and actual sparse MLX due identities/raw mask hashes. A single copied preceding row crosses block boundaries without retaining an earlier phase block.
- A fault at the first row of block two records step 32 and its actual step-31 predecessor, preserving float64/float32 precision and owned raw clock arrays. The paired module passes **21 tests, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass. Weight/reduction metadata, complete-network observation, and interpretation remain open. Commit this working state before additional capture checks.

First-cause retention checkpoint (2026-10-05):

- Raw capture is committed at `8a484a2`. Additional intent cases preserve the earliest error's exact raw context when later errors/blocks arrive, reject nonfinite state after spike divergence, and report no false cause for the complete common-history fixture. The paired module passes **24 tests, zero failures/errors/skips**; full strict Pyright, Ruff, and formatting pass.
- Capture is ready for complete-network execution, with weight/reduction metadata still required if a cause is found. Commit this working state before execution or further changes.

Paired-observer regression/evidence checkpoint (2026-10-05):

- First-cause retention is committed at `1c55b0f`. The installed qualification command completes **152 scientific tests, zero failures/errors/skips**, in 124.47 seconds. [Result](../../evidence/milestone-4/paired-observer/result.json), [test report](../../evidence/milestone-4/paired-observer/tests.xml), and [log](../../evidence/milestone-4/paired-observer/qualification.log). The [application report](../../evidence/milestone-4/paired-observer/application-tests.xml) records **169 passed, zero failures/errors/skips**; full Ruff, formatting across 111 files, strict Pyright, three import contracts, and the 38-package offline lock check pass.
- [Verification/source hashes](../../evidence/milestone-4/paired-observer/verification.json) independently fix unchanged production numerical source and all 66 retained compressed trace archives. The [trace bundle](../../evidence/milestone-4/paired-observer/trace-arrays.zip) reproduces every local archive hash. Full local results remain in `data/results/milestone-4-paired-regression-20261005-01`.
- This closes small live paired alignment, actual due-event agreement, fault detection, and raw first-cause retention with complete-suite coexistence. Next: complete shortest MLX ordinary/observed/repeated execution with live reference auditing and sampled concurrent memory, followed by four-trial memory and the frozen matrix. Commit this execution evidence before the complete-network proof.

Complete ordinary/observed MLX checkpoint (2026-10-05):

- Paired regression is committed at `c0e76e1`. The pinned 138,639-neuron / 15,091,983-row sugar trial 0 completes all **1,000 steps** through ordinary MLX and bounded observed MLX with a live independent reference. Both MLX runs produce **1,612 spikes / 335 active neurons**. Every native phase/block-boundary queue/due-mask hash and actual final state/queue/raster archive agrees exactly.
- All-neuron causal auditing records **no state-budget violation and no spike difference** against Brian2. Exact common-history refractory/clocks, actual due-edge identities, reference physical queues, replay channels/cursor, MLX all-entry ledgers, and finite state pass throughout. All 1,001 reference physical digests and native output also match the separately qualified complete reference proof. Direct normalized final-pending comparison checks every future due step and the cleared MLX current slot.
- [Independent verification](../../evidence/milestone-4/full-paired-observer/ordinary-observed-verification.json), [ordinary observations](../../evidence/milestone-4/full-paired-observer/ordinary.json), [observed comparisons](../../evidence/milestone-4/full-paired-observer/observed.json), [actual final MLX arrays](../../evidence/milestone-4/full-paired-observer/observed-mlx-final.npz), and [executed proof](../../evidence/milestone-4/full-paired-observer/executed-proof.py) are versioned. Ordinary/paired execution takes **50.331 / 158.679 seconds**; these include qualification capture and are not benchmark approval. Fresh-state repetition and the final sampled-memory report are still running. No PyTorch/full-matrix case is accepted. Commit this completed working evidence now.

Complete paired repeat/memory checkpoint (2026-10-05):

- Ordinary/observed evidence is committed at `ff29df4`. Fresh-state observed repetition completes all 1,000 steps in **157.056 seconds**, again with 1,612 spikes / 335 active neurons, **no budget violation and no spike difference**. Every native MLX phase, boundary queue, actual due-mask hash, final state/queue/raster, and every reference phase/physical queue/native output repeats exactly. [Independent verification](../../evidence/milestone-4/full-paired-observer/repeat-verification.json) and [repeat observations](../../evidence/milestone-4/full-paired-observer/repeat.json).
- [Memory records and scope](../../evidence/milestone-4/full-paired-observer/paired-observer.json) and [all samples](../../evidence/milestone-4/full-paired-observer/memory-samples.jsonl) show a sampled proof-process/reference-child resident-size sum peak of **3,177,136,128 bytes**. Sampling begins after data loading, compilation and `prepare()` return, and includes each mode's fresh-state allocation/evaluation and execution/collection. Shared pages can be counted twice; MLX allocator peaks are separate. This does not measure total system/unified memory or four-trial execution. The original full local report is preserved; the compact version references its three mode records and clarifies sampling scope.
- This closes complete shortest MLX observer transparency, raw state/queue repeat, and live common-history causal auditing. The separately committed 152 scientific / 169 application tests remain the unchanged-source regression. Next: actual four-trial concurrent memory, full PyTorch observation, and every frozen case/batch gate. No paired three-engine full-network case is accepted. Commit this completed evidence before proceeding.

Bounded four-trial wiring checkpoint (2026-10-05):

- Complete paired replay/memory is committed at `a9eefcc`. The qualified reader now exposes one reference-block read and finalization, allowing one batched MLX block to be audited against four independent live reference processes without cached block histories. A per-trial view preserves raw fields, check flags, physical queue hashes, actual due identities, and mask hashes.
- All **34 MLX/paired observer tests pass, zero failures/errors/skips**, including existing transport/causal faults and exact batch/independent view checks. Full strict Pyright, Ruff, and formatting pass. No numerical function changes. Commit this working state before actual four-trial execution.

CPU comparator setup checkpoint (2026-10-05):

- At `dee8d93`, confidence **99%**: retain the pinned comparator's original compressed sparse row (CSR) construction, signed count orientation, float32 model, and numerical methods; replace only its registered Poisson sampler with canonical count replay at the existing input slot. Original source inspection confirms CSR is the benchmark's selected representation. Common setup supplies outgoing-silenced counts and the activated union as approved by the frozen contract.
- The optional [CPU setup adapter](../../../src/fly_brain/qualification/adapters/torch_setup.py) uses immutable original data, explicit CPU weights, and typed native float32 tensor boundaries. Narrow upstream typing gaps are limited to NumPy/Torch conversions and the sparse constructor; no numerical reference method changes.
- Four tests pass, zero failures/errors/skips: orientation/silencing/activation, overlapping input counts, and all five actual tensors byte-identical with guaranteed native Poisson input across 25 steps at one/four trials. Full strict Pyright, Ruff, and formatting pass. This qualifies small common setup/replay; full PyTorch observation and acceptance remain open. Commit this working state now.

Complete four-trial memory/first-difference checkpoint (2026-10-05):

- At `dee8d93`, actual four-trial sugar execution completes all **1,000 steps** with four independently built continuously streamed references in **621.992 seconds**. Every live actual-queue/finite-state check passes; every trial-0 native phase/queue/due hash matches its previously qualified independent execution. [Report and limits](../../evidence/milestone-4/four-trial-memory/four-trial-memory.json), [independent verification](../../evidence/milestone-4/four-trial-memory/verification.json), [executed proof](../../evidence/milestone-4/four-trial-memory/executed-proof.py), and [actual final batch state/queues](../../evidence/milestone-4/four-trial-memory/batch-final.npz).
- [All resident-size samples](../../evidence/milestone-4/four-trial-memory/memory-samples.jsonl) include the proof process and all four direct reference children. Their sampled sum peaks at **5,625,659,392 bytes**; the separate MLX allocator peak is **5,895,508,577 bytes**. Sampling includes fresh-state allocation/execution/collection after load/build/prepare. Shared pages can be counted twice; these are not total system/unified-memory peaks and are not added together.
- Trials 0/2/3 have no spike difference or budget violation. Trial 1's first different spike is at **step 999, neuron 41,514 / identifier 720575940620025620**. Reference pre-threshold margin is `+0.0000153406537473 mV`; MLX margin is `-0.0000152587890625 mV`. Error `0.0000305994428089 mV` and reference margin are below the unchanged `0.00144999984659346 mV` budget. Both are available; their preceding last-spike step is 773. Actual current/preceding due membership, device leaf ordering/counts, and native reference weights independently match. All earlier phase budgets pass. [Raw current/preceding observations and actual reduction inputs](../../evidence/milestone-4/four-trial-memory/trial-1-spike-context.npz) preserve this first complete-network difference.
- The fixed numerical rounding conditions are satisfied; bounded Astra `xhigh` scientific adjudication is next before dependent case acceptance. This memory proof does not qualify four-trial repetition, independent trials 1–3, the prescribed one-second batch gate, PyTorch comparison, or the 52-case matrix. No tolerance or one-spike waiver is introduced. Commit this verified evidence before review dispatch.

Bounded first-difference review resolved (2026-10-05):

- Dispatched at `1b33fab` to `/root/review_first_full_divergence`, fresh-context **GPT-6 Astra / `xhigh`**. Its completed read-only review finds the actual step-999 difference consistent with the prospectively approved roundoff condition, with no scientific/observation blocker to that bounded classification. [Accepted decision, measurements, and limits](../../evidence/milestone-4/four-trial-memory/astra-review.md).
- At `c8a9e01`, Sol independently reproduces the actual selected reduction and ordered reference addition byte for byte, the local MLX state update, all 38 saved physical reference queue slots, stimulus regeneration, and every saved all-neuron phase budget. [Parent verification](../../evidence/milestone-4/four-trial-memory/astra-parent-verification.json). Most of the voltage difference is already present in the preceding end state; an exact global rounding decomposition and full first-spike replay are not claimed.
- Confidence **99%**: record this classification and proceed with the independent CPU comparator observer. The missing spike remains in every required metric. All repeat/batch and frozen 52-case acceptance requirements remain open; no tolerance or initial-state exception changes. Commit this decision before further implementation.

CPU comparator boundary checkpoint (2026-10-05):

- At `1772f3f`, add intent checks for noncanonical stimulus bits/dtype/shape, native tensor precision, changed global float defaults, and exact empty-connectivity/channel silence. All **13 CPU setup tests pass, zero failures/errors/skips**, with 29 dependency warnings. Full Ruff and strict Pyright pass. No numerical source changes; commit this passing working state before state observation.

Native CPU snapshot checkpoint (2026-10-05):

- At `bb22f88`, the observer copies and hashes all five actual native float32 tensors, including every physical delay-buffer cell. Per-trial hashes include field names, dtype, shape, and bytes; no unit/precision conversion or buffer reconstruction occurs. Each snapshot owns its data and rejects invalid shape or nonfinite fields.
- All **23 CPU setup/snapshot tests pass, zero failures/errors/skips**, with 29 dependency warnings. Every tensor's mutation changes the digest while saved bytes remain intact; a nonfinite value in each tensor fails. Full Ruff and strict Pyright pass. This qualifies the snapshot boundary; streamed execution, repeat/batch evidence, and complete comparator execution remain open. Commit this passing unit before adding the execution loop.

Streamed CPU observer checkpoint (2026-10-05):

- At `cf77810`, the CPU observer calls the unchanged model once per canonical event step and yields owned native snapshots, including initial state. It retains no tensor history; gradient suppression ends before each yield. The canonical input boundary validates trial/step/channel shape, dtype, and bits.
- All **27 CPU setup/observer tests pass, zero failures/errors/skips**, with 29 dependency warnings. All five tensors at all 101 steps match ordinary execution byte for byte for populated/silent fixtures at one/four trials. Full Ruff and strict Pyright pass. Repeat/batch equivalence, boundary faults, and complete comparator execution remain open. Commit this passing loop before further qualification.

CPU replay/batch checkpoint (2026-10-05):

- At `4486839`, all **35 CPU setup/observer tests pass, zero failures/errors/skips**, with 29 dependency warnings. Fresh populated/silent runs repeat every initial/per-step five-tensor digest; each of four actual batch trials matches independently initialized execution in every raw state and physical buffer byte. Invalid replay schedules fail before any observation is yielded. Full Ruff and strict Pyright pass. This is small-network evidence only; complete execution and the frozen matrix remain open. Commit this qualified unit before further work.

CPU snapshot validity checkpoint (2026-10-05):

- At `edac41b`, confidence **99%**: validate raw comparator output at the observation boundary before hashing/metric use. Missing neuron dimensions or physical delay slots, fractional/nonbinary spikes, and negative/fractional refractory counters fail explicitly. Numerical reference methods remain unchanged.
- All **41 CPU setup/observer tests pass, zero failures/errors/skips**, with 29 dependency warnings; full Ruff and strict Pyright pass. Commit this passing boundary before the complete scientific regression and full-network comparator proof.

Complete CPU observer regression checkpoint (2026-10-05):

- At `8f48b2e`, `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify --output data/results/milestone-4-cpu-observer-regression-20261005-01` passes **193 scientific tests, zero failures/errors/skips**, with 505 dependency warnings, in **122.57 seconds**. [Result](../../evidence/milestone-4/cpu-observer/result.json), [full report](../../evidence/milestone-4/cpu-observer/tests.xml), and [log](../../evidence/milestone-4/cpu-observer/qualification.log).
- The default application suite passes **169 tests, zero failures/errors/skips**. Ruff checks all 115 files, strict Pyright reports zero errors/warnings, all three import contracts pass, and the offline lock check resolves 38 packages. [Application report](../../evidence/milestone-4/cpu-observer/application-tests.xml) and [independent verification](../../evidence/milestone-4/cpu-observer/verification.json).
- All **72 generated NPZ files** (66 top-level traces and six nested observer input/phase files) are versioned together and independently rehashed. Production core/bucket/reduction and pinned CPU numerical reference sources match the preceding regression. [Complete source hashes](../../evidence/milestone-4/cpu-observer/source-hashes.json) and [raw traces](../../evidence/milestone-4/cpu-observer/traces.zip). This closes small CPU state observation with complete-suite coexistence; no complete-network CPU or matrix pass is implied. Commit this evidence before full execution.
- Archive correction at `ae78cc0`: the initial archive count check failed because recursive selection included six nested NPZ files beyond the expected 66 top-level traces. I committed the archive claims before inspecting that failed result. The archive and verification are now complete for all 72 files; test results were unaffected. No further execution began before correcting this checkpoint.
- Confidence **99%** at `8f48b2e`: run the complete shortest CPU comparator proof using the exact existing sugar trial-0 stimulus, unchanged CSR/float32 numerical source, and one explicit CPU execution thread. Record the actual framework/thread/determinism settings; prove ordinary/observed/fresh-state repeated native bytes before using its metrics. Keep total unified memory and benchmark approval separate from sampled proof-process residency.

Complete CPU proof environment checkpoint (2026-10-05):

- At `d0f5296`, the full CPU proof's ordinary mode completes all 1,000 steps and 1,001 native observations. The sandbox denies `ps` access, leaving no memory samples. I interrupt the owned process during observed mode (exit 130) and preserve every output. [Interrupted attempt and limits](../../evidence/milestone-4/full-cpu-observer/interrupted-sandbox-attempt.json) and [executed source](../../evidence/milestone-4/full-cpu-observer/interrupted-proof.py). Observer/repeat/memory qualification remains open; no numerical failure was observed.
- Confidence **99%**: use the same qualified numerical source and canonical inputs in a fresh run with authorized system access for residency sampling. Fail promptly if sampling breaks. Commit this environment checkpoint before restarting; do not overwrite the interrupted output.

Frozen matrix enumeration checkpoint (2026-10-05):

- At `9f3cdc2`, add a pure typed enumeration of all **52** required experiment/duration/trial cases. Intent checks independently require every prescribed case, no duplicates, the 15/15/10/10/2 configuration counts, and **1,231,000 base steps per engine** before repeats and batch gates. Add the module to the enforced framework-free dependency boundary.
- The default application suite passes **171 tests, zero failures/errors/skips**; full Ruff, strict Pyright, and all three import contracts pass. This defines the workload and does not execute or accept a case. The independent full CPU proof continues against unchanged numerical/observer sources. Commit this passing plan before runner wiring.

Scoring coordinate boundary checkpoint (2026-10-05):

- At `db5c999`, add a pure coordinate validator for the frozen case protocol. Aligned native integer vectors, pinned neuron/horizon bounds, and unique neuron/step events are required before scoring; real empty vectors remain valid silence. Nine intent cases cover empty/boundary coordinates, out-of-range events, duplicates, mismatched lengths, and missing dimensions.
- The default application suite passes **180 tests, zero failures/errors/skips**; full Ruff and strict Pyright pass. The unchanged metric calculations and numerical engines retain their separately recorded results. The full CPU observation proof is independent and still running. Commit this passing boundary before input normalization/scoring.

Native reference clock checkpoint (2026-10-05):

- At `ca3f1a6`, confidence **99%**: normalize the native Brian2 float64 spike times only when they lie exactly on the frozen 0.0001-second integer clock and inside the case horizon. The retained complete reference's 1,612 actual times meet that condition exactly. Nonfinite, negative, end/outside, or off-clock times fail rather than being rounded into valid events. Coordinate validation also refuses implicit float/int32/Boolean conversion.
- The default application suite passes **193 tests, zero failures/errors/skips**; full Ruff and strict Pyright pass. This changes no metric or numerical engine. The full CPU proof has matched observed to ordinary native bytes and is running its fresh-state repeat. Commit this passing normalization before three-engine scoring.

Complete CPU observer qualification checkpoint (2026-10-05):

- At `9f3cdc2`, the fresh full CPU proof completes ordinary, observed, and fresh-state repeated sugar trial 0 for all **1,000 steps**. All **1,001 initial/per-step native five-tensor digests**, every physical delay-buffer cell, complete final arrays, and integer spike rasters match byte for byte. Each mode has **1,609 spikes / 326 active neurons**. The parent's independent rehash also confirms a separate process's preserved ordinary run matches every digest. [Report](../../evidence/milestone-4/full-cpu-observer/cpu-observer.json), [environment/source pins](../../evidence/milestone-4/full-cpu-observer/environment.json), [verification](../../evidence/milestone-4/full-cpu-observer/verification.json), and [executed proof](../../evidence/milestone-4/full-cpu-observer/executed-proof.py).
- Actual CPU execution uses PyTorch 2.11.0, float32, the original CSR model, one execution thread, and ten recorded interoperation threads. Canonical sugar input is byte-identical to the qualified Brian2/MLX case. Numerical source hashes remain unchanged. Ordinary/observed/repeated execution and capture take **163.538 / 173.319 / 172.843 seconds**; these are qualification times, not benchmark approval.
- [Actual process-residency samples](../../evidence/milestone-4/full-cpu-observer/memory-samples.jsonl) peak at **2,519,154,688 bytes**, after load/prepare and including fresh-state allocation/execution/hash/collection. This covers only the proof process and is not total system/unified memory. The interrupted output remains preserved. This closes complete shortest CPU observation and raw repeat; three-engine metric scoring, full batch checks, and the remaining matrix stay open. Commit this verified evidence before scoring.

First accepted three-engine case (2026-10-05):

- At `1dcb201`, score the complete **sugar / 0.1-second / trial-0** case using the independently qualified reference/MLX/CPU observations and unchanged numerical source. All native input hashes, exact identical canonical event/target arrays, pinned input/mapping, valid unique coordinates, native reference clock, complete replay/physical-queue evidence, and common-history causal checks pass. Earliest state-budget violation and first different MLX/Brian2 spike are both explicitly **none**. [Case and exact gate results](../../evidence/milestone-4/cases/sugar-1000-0/case.json), [normalized FlyWire-identifier rasters](../../evidence/milestone-4/cases/sugar-1000-0/normalized-spikes.npz), and [executed score](../../evidence/milestone-4/cases/sugar-1000-0/executed-score.py).
- MLX matches all **1,612** reference events exactly: Jaccard/F1/correlation are 1, count/neuron errors are 0. CPU PyTorch has **1,609** events, Jaccard **318/343**, count error **3/1,612**, neuron error **141/1,612**, common-support correlation **0.990039783798138**, and timing F1 **2,060/3,221**. All **11 fixed/paired metric checks** and every per-case validity/causal/replay check pass; no one-spike allowance or tolerance change is used.
- [Independent parent verification](../../evidence/milestone-4/cases/sugar-1000-0/verification.json) checks exact complete MLX/reference rasters, all native file hashes, rational metrics, correlation via the standard statistics module, and **1,030** CPU timing matches using a separate dynamic program. This accepts **1/52 cases only**. The remaining cases, prescribed one-second sugar/P9 four-trial repeat/batch checks, pooled/time-bin reports, performance, and full Milestone 4 completion remain open. Commit this accepted evidence before runner wiring.

First-case working-state checkpoint (2026-10-05):

- Accepted case evidence is committed at `e07073e`. A fresh default-suite report records **193 passed tests, zero failures/errors/skips**; all 118 files pass Ruff formatting/lint, strict Pyright has zero errors/warnings, all three dependency contracts pass (88 modules / 324 dependencies), and the offline lock check resolves 38 packages. All local milestone links exist. [Application report](../../evidence/milestone-4/matrix-boundaries/application-tests.xml), [quality log](../../evidence/milestone-4/matrix-boundaries/quality.log), and [verification/source hashes](../../evidence/milestone-4/matrix-boundaries/verification.json).
- The separate complete 193-test scientific regression remains the unchanged numerical/observer result; it is not rerun for pure plan/coordinate/clock checks. Next: wire reproducible remaining-case execution and reporting, preserving all frozen cases, repeat/batch requirements, causal context, and incremental checkpoints. Push remains pending because only public reference `upstream` exists.

Reusable observer evidence checkpoint (2026-10-05):

- At `7b70c29`, the runner needs reusable evidence because cases vary while actual native state, physical queue order, clocks, and frozen gates must remain invariant. Keep orchestration and file/device work in qualification adapters; use the existing pure case plan and injected collaborators. No database, new framework, numerical method, or external endpoint is needed.
- Add native array descriptors and actual reference physical-snapshot hashing with the same deterministic encoding used by the qualified full proof. Precision, shape, signed zero, step, clock, native time, and source cursor all affect evidence. The default application suite passes **198 tests, zero failures/errors/skips**; full Ruff and strict Pyright pass. Commit this working unit before queue/spike integrity checks and runner wiring.

Physical-order evidence checkpoint (2026-10-05):

- At `9208533`, actual recurrent/source spike order, delivered row order, queue offset, physical slot order, and original edge order within a slot each produce a distinct physical digest. The default application suite passes **199 tests, zero failures/errors/skips**; full Ruff and strict Pyright pass. This closes the reusable native/physical hashing boundary without changing observation or numerical execution. Commit this verified unit before cause-file writing.

Raw cause archive checkpoint (2026-10-05):

- At `fe4185c`, the qualification-owned writer persists current/preceding native phase fields, actual recurrent/source spikes, delivery order, every physical queue slot/offset, and actual MLX due identities. Metadata retains the exact physical clock/cursor and native due-mask hash; no unit or precision conversion occurs. Files use exclusive creation.
- An initial test expected the wrong fixture array count (54 instead of 52); it is corrected before this checkpoint. The default application suite passes **200 tests, zero failures/errors/skips**; full Ruff and strict Pyright pass. This qualifies basic raw serialization only; full-field/no-overwrite checks and actual device reduction-input capture are next. Commit this passing unit before extending it.

Cause archive preservation checkpoint (2026-10-05):

- At `2885990`, current and preceding native state differ in the file fixture; every dtype/shape/byte and all 19 actual queue-slot arrays survive unchanged. Existing evidence cannot be overwritten. The default application suite passes **201 tests, zero failures/errors/skips**; full Ruff and strict Pyright pass. No execution or numerical method changes. Commit this passing serialization qualification before actual device leaf capture.

Actual reduction-input capture checkpoint (2026-10-05):

- At `e22812b`, capture the affected targets' actual device leaf row IDs, float32 signed counts, native occupancy/padding, and supplied original-row reference weights without conversion. Cause archives now include these reduction inputs. Missing targets fail explicitly; no reconstructed layout replaces actual device data.
- **Two real Metal checks pass, zero failures/errors/skips**, across populated and empty layouts, every target, outgoing silencing, exact row order/counts, native dtypes/weights, and padding. The default application suite remains **201 passed, zero failures/errors/skips**; full Ruff and strict Pyright pass. This qualifies capture primitives only; live paired-run cause wiring and complete matrix execution remain open. Commit this passing working state before further integration.

Live paired collector checkpoint (2026-10-05):

- At `3f7eeb8`, add a qualification-owned collector that streams independent Brian2 and MLX observations, checks every common-history phase, retains native phase/actual queue/due hashes, and writes complete native final arrays and spike coordinates. The actual final reference observation must match its separately written native output. Output creation is exclusive; each owned generator closes on exit. Correct the MLX generator's return annotation without changing execution.
- **Two live reference/Metal tests pass, zero failures/errors/skips**, with populated and empty networks, partial final blocks, all 102 physical observations, native float64/float32 preservation, fresh-process replay, and no-overwrite checks. [Live test report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-paired-collector-20261005-01.xml). The default application suite passes **201 tests, zero failures/errors/skips**; all 126 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass (93 modules / 352 dependencies).
- This closes basic live collection only. Actual final reference queue arrays, cause-file integration, and complete matrix execution remain next. No additional full-network case is accepted. Commit this passing working state before extending the collector.

Final physical queue archive checkpoint (2026-10-05):

- At `70b6ed7`, retain every actual final reference spike/channel array, delivered row array, queue offset, and ordered physical slot array, with native descriptors and exact clock/cursor metadata. The same physical-array helper now serves cause and final archives; existing cause filenames and bytes remain unchanged.
- **Two live reference/Metal tests pass, zero failures/errors/skips**, verifying every retained array against its observed native descriptor and fresh-process repeat. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-paired-collector-20261005-02.xml). The default application suite remains **201 passed, zero failures/errors/skips**; full Ruff formatting/lint and strict Pyright pass. Cause-file integration and matrix execution remain open. Commit this working state before the next unit.

Live cause-file integration checkpoint (2026-10-05):

- At `568ceed`, the paired collector writes explicit no-difference/first-difference results and bounded current/preceding cause archives. Each found cause includes supplied stimulus bits/targets, mapped affected identifiers, actual device leaves/counts/padding, native weights read from the completed reference process, threshold margins, and every native phase/physical queue descriptor. The recorded reduction order is the approved uncompiled factored tree; no classification or tolerance waiver is inferred.
- **Three live reference/Metal tests pass, zero failures/errors/skips**. An explicitly injected step-7 budget fault proves archive retention across subsequent blocks, checks all archived native descriptors, and compares selected weights directly with actual C++ output. The injected fault is a serialization test, not a naturally occurring numerical difference. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-paired-collector-20261005-03.xml). The default application suite remains **201 passed, zero failures/errors/skips**; all 127 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass.
- Full-network cause interpretation still requires the bounded review rule. CPU collection, repeat acceptance, and the remaining matrix remain open. Commit this working state before the next implementation.

Reusable CPU collector checkpoint (2026-10-05):

- At `8030edd`, stream the pinned CPU comparator's actual five float32 tensors and full physical delay buffer from fresh state. Retain each trial's native digest at initial state and every step, complete final arrays, and aligned integer trial/neuron/step spike coordinates. Output creation is exclusive; the actual generator closes on exit. Its corrected return annotation changes no numerical behavior.
- The first sandbox attempt stopped during shared Metal-fixture import before running tests. The rerun with device access passes **30 CPU collector/observer tests, zero failures/errors/skips**, including populated/silent four-trial collection, complete native array/hash preservation, fresh-state replay, and no-overwrite checks. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-cpu-collector-20261005-02.xml). The default application suite remains **201 passed, zero failures/errors/skips**; all 129 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass (95 modules / 374 dependencies).
- This qualifies reusable CPU evidence collection only. Persisted repeat checks, case execution/reporting, and the remaining matrix remain open. Commit this passing working state before the next unit.

Persisted replay verification checkpoint (2026-10-05):

- At `1476383`, compare the persisted native phase/state, actual physical queue/due, clock/cursor, final arrays, causal metadata, and any retained cause arrays across fresh paired runs. CPU replay compares every initial/per-step native digest and all final tensors/spike coordinates. Native dtype, shape, and bytes must match; missing evidence fails instead of passing from spike counts.
- Seven file-boundary cases reject changed/missing digest coverage, changed fields, precision, shape, and signed-zero bytes. The default application suite passes **208 tests, zero failures/errors/skips**. Five live paired/CPU collector tests pass with the persisted verifier, **zero failures/errors/skips**. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-replay-evidence-20261005-01.xml). All 131 files pass Ruff checks; strict Pyright has zero errors/warnings.
- Replay identity is one required check, not case acceptance. Frozen scoring, causal review when needed, complete case validity, and matrix execution remain open. Commit this working state before complete-suite qualification or further implementation.

Complete collector regression checkpoint (2026-10-05):

- At `1d596c9`, `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify --output data/results/milestone-4-collector-regression-20261005-01` passes **200 scientific tests, zero failures/errors/skips**, with 519 dependency warnings in 144.86 seconds. [Result](../../evidence/milestone-4/collectors/result.json), [report](../../evidence/milestone-4/collectors/tests.xml), and [log](../../evidence/milestone-4/collectors/qualification.log). This proves complete-suite coexistence of the new native/physical/cause/replay collectors with the numerical, reference, ledger, and device tests.
- A fresh default report passes **208 application tests, zero failures/errors/skips**. [Report](../../evidence/milestone-4/collectors/application-tests.xml). All 131 files pass Ruff formatting/lint; strict Pyright has zero errors/warnings; all three import contracts pass (96 modules / 377 dependencies); the offline lock check resolves 38 packages. [Quality record](../../evidence/milestone-4/collectors/quality.json).
- Archive all **72 generated trace files / 1,957 native arrays** and independently verify every archived file hash against its original. [Trace archive](../../evidence/milestone-4/collectors/traces.zip) and [executed verification, source hashes, and manifest](../../evidence/milestone-4/collectors/verification.json). Production numerical sources, reference equations/setup, and dependencies are unchanged since `7b70c29`; observer execution bodies are unchanged, with only their generator return declarations corrected.
- Full local outputs remain preserved. This closes collector regression; **1/52 full-network cases** remain accepted. Reusable complete-case execution/reporting, all remaining cases/batch gates, and later milestones remain open. Commit this verified execution evidence before proceeding.

Reusable case execution checkpoint (2026-10-05):

- At `7043381`, inject the prepared independent reference job, MLX execution, CPU comparator, canonical stimulus, and progress callback into a qualification-owned executor. Run all three engines twice from fresh state; persist every mode separately and require actual saved native state/queue/due/cause evidence to repeat before reporting replay verification. Existing output cannot be overwritten.
- **Two live three-engine tests pass, zero failures/errors/skips**, across populated and silent networks, complete horizon and initial-state coverage, independent reference processes, and mandatory repeat evidence. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-case-execution-20261005-01.xml). The default application suite remains **208 passed, zero failures/errors/skips**; all 133 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass (97 modules / 386 dependencies).
- This closes reusable execution only. Validated spike normalization, frozen scoring/reporting, and full matrix cases remain open. The separately recorded 200-test full scientific regression is not rerun for this adapter-only unit. Commit this working state before the next change.

Native case-coordinate loading checkpoint (2026-10-05):

- At `664051b`, load actual single-case spike arrays and record their native dtype/shape/byte digests before conversion. Require native reference int32 neuron indices and exact float64 integer-clock times; require native int64 MLX/CPU coordinates and aligned CPU trial-zero indices. Reject duplicates and out-of-range coordinates before mapping through the pinned CSV neuron order.
- Eight file-boundary cases verify correct identifier mapping/native descriptors and reject precision changes, off-clock times, wrong neuron bounds, nonzero/misaligned trials, and duplicate spikes. The default suite passes **216 tests, zero failures/errors/skips**. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-case-spikes-20261005-01.xml). All 135 files pass Ruff checks; strict Pyright has zero errors/warnings. No numerical method or reference changes. Commit this working state before frozen scoring/reporting.

Final pending-event verification checkpoint (2026-10-05):

- At `61f1a3e`, compare the actual saved final queues by absolute due step under the already verified physical mapping: Brian2 retains its just-delivered slot; MLX clears that slot. Require all 18 future original-row sets to agree, native queue geometry/offsets to match the horizon, and MLX's delivered slot to be empty. Keep physical order preservation/replay as separate mandatory checks. No reconstructed ledger is substituted for actual final arrays.
- Eight file-boundary cases verify the retained delivered history and reject changed future events, an uncleared slot, wrong offset/clock/precision, duplicates, and out-of-range original rows. The default suite passes **224 tests, zero failures/errors/skips**. Three live reference/Metal collector tests pass, **zero failures/errors/skips**, including actual populated/empty final queues. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-final-pending-20261005-01.xml). All 137 files pass Ruff checks; strict Pyright has zero errors/warnings after narrowing the validated native archive row type.
- Invoke this cross-engine pending comparison while the full spike history is common. After a spike fork, each engine still requires its own actual queue ledger/replay; later queues are not forced to match across engines. Full-network scoring/reporting remains next. Commit this passing unit before proceeding.

Frozen case reporting checkpoint (2026-10-05):

- At `3b69144`, score the actual validated, identifier-mapped three-engine rasters with the unchanged frozen gates. Require saved native replay identity, prescribed case/trial/seed/generator/target/rate metadata, declared input geometry, complete common-history budget coverage, and actual common-history final pending events. Retain exact rational metrics, native input descriptors before conversion, normalized raw spike arrays, and complete causal results.
- Any first different spike or state-budget violation remains marked for scientific review and cannot receive automatic case acceptance. Final cross-engine queues are explicitly inapplicable after a spike fork; each engine's actual queue ledger/replay remains required. No tolerance or metric changes.
- **Two live three-engine execution/reporting tests pass, zero failures/errors/skips**. Their unprescribed 101-step fixture is rejected as a full case despite exact MLX/reference spikes; exact rational serialization, native identifier/step preservation, pending checks, and no-overwrite behavior pass. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-case-report-20261005-01.xml). The default suite remains **224 passed, zero failures/errors/skips**; all 138 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass (100 modules / 411 dependencies).
- Reproducible command wiring and the next complete-network case are next. Commit this passing state before proceeding.

Prescribed parity driver checkpoint (2026-10-05):

- At `ce818dd`, wire prescribed experiment generation and outgoing silencing to persisted canonical inputs, one pinned CPU reference thread, the independent C++ reference, the approved uncompiled MLX layout, complete repeated execution, and frozen reporting. Record actual installed versions, device/configuration, executed application-source hashes, and reference-job metadata. The composition root owns CPU thread configuration; domain imports retain their normal-runtime boundaries.
- Require the fixed **138,639-neuron / 15,091,983-edge** geometry before full-case acceptance. The live six-neuron P9 driver fixture uses the prescribed 1,000-step seed/target/rate protocol and completes all three engines twice, but cannot claim a full-connectome case. Its corrected test passes **one test, zero failures/errors/skips**; the first attempt failed because the test restored CPU configuration before its final preservation check. [Corrected report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-parity-driver-20261005-02.xml); the first report/build remain preserved.
- The default suite remains **224 passed, zero failures/errors/skips**; all 140 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three import contracts pass (101 modules / 434 dependencies). Command-boundary validation and a new complete-network case remain next. Commit this working state before exposing the command.

Validated parity command checkpoint (2026-10-05):

- At `896e2f2`, expose `fly-brain qualify-parity` with project/fresh-output, experiment, duration, and trial options. The thin command calls the composition root once and returns a failure status for an unaccepted case. Pydantic boundaries admit every frozen configuration and reject unprescribed combinations/nonfinite durations. The command uses the fixed canonical seed; existing production/output contracts are unchanged.
- **286 application tests pass, zero failures/errors/skips**, including all 52 allowed cases, eight invalid combinations, and accepted/unaccepted dispatch statuses. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-parity-options-20261005-01.xml). All 141 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass (101 modules / 436 dependencies). Installed command help succeeds. [Reproduction command](../development.md#application-and-scientific-checks).
- Next: complete-suite regression followed by P9 trial 0 at 0.1 seconds on the full pinned connectome. Existing acceptance remains **1/52 cases**. Commit this passing command before execution.

Complete case-runner regression checkpoint (2026-10-05):

- At `3fe804c`, the installed `qualify` command passes **203 scientific tests, zero failures/errors/skips**, with 533 dependency warnings in 174.29 seconds. [Result](../../evidence/milestone-4/case-runner/result.json), [report](../../evidence/milestone-4/case-runner/tests.xml), and [log](../../evidence/milestone-4/case-runner/qualification.log). This verifies complete-suite coexistence of the three-engine executor, actual final pending checks, frozen reporter, prescribed driver, and all earlier numerical/reference/device tests.
- The separate application report passes **286 tests, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-runner/application-tests.xml). All 141 files pass Ruff formatting/lint; strict Pyright has zero errors/warnings; all three import contracts pass (101 modules / 436 dependencies); the offline lock check resolves 38 packages. [Quality record](../../evidence/milestone-4/case-runner/quality.json).
- All **72 generated trace files / 1,957 native arrays** are archived and every archived file hash is independently checked against its original. [Trace archive](../../evidence/milestone-4/case-runner/traces.zip), [verification/source hashes](../../evidence/milestone-4/case-runner/verification.json), and [executed verification](../../evidence/milestone-4/case-runner/executed-verification.py). Production numerical sources, reference equations/setup, and dependencies remain unchanged since `7b70c29`.
- Full local outputs remain preserved. Next is complete P9 trial 0 at 0.1 seconds through the installed command; acceptance remains **1/52 cases** until new results pass independent inspection. Commit this verified execution evidence before that run.

Matrix-diagnostic review assignment (2026-10-05):

- At clean checkpoint `5ae0cf9`, dispatch fresh-context `/root/review_matrix_diagnostics` to **GPT-6 Astra at explicit `xhigh`**, under the bounded subagent skill. Review only the required pooled summaries and 100 ms time-bin diagnostics: common experiment/duration grouping, trial-separated timing, rate normalization, integer bin boundaries, empty/incomplete coverage, and meaningful regression cases.
- Every individual fixed/paired/causal/replay gate remains mandatory. The review cannot change the model, references, precision, tolerances, schemas, or scope. Await its completed decision and independently verify it before dependent implementation. Existing manual reviews retain their owners.
- Independently, the installed full P9 trial-0 / 1,000-step case launched at `5ae0cf9` is running in `data/results/milestone-4-parity-p9-1000-0-20261005-01`. Both paired executions report no spike difference or state-budget violation; CPU first/repeat and final acceptance remain pending. The tree was clean before dispatch; commit this assignment before further changes.

Matrix-diagnostic review completion (2026-10-05):

- Fresh-context Astra at explicit `xhigh` completes the [bounded decision](../../evidence/milestone-4/matrix-diagnostics/astra-review.md). Pool counts only within common experiment/duration groups, normalize rates by actual included trial exposure, retain the common three-engine active support, and match timing independently within each trial. Use complete half-open integer 1,000-step bins for localization. Include valid failed cases and explicit missing/invalid coverage; never apply acceptance gates to pooled diagnostics.
- Sol independently verifies trial-exchange and offset-boundary counterexamples, event-weighted timing, separate matching windows, silent-trial exposure, integer bin endpoints/zeros, all 52 cases / 12 groups, and the retained complete sugar score. [Parent verification](../../evidence/milestone-4/matrix-diagnostics/parent-verification.json). No code, gates, physics, output contracts, or schemas change in this review.
- Next: pure pooling/bin functions and focused tests after this decision is committed. Full P9 CPU replay is independent and still running. This review is not matrix, batch, or performance acceptance.

Complete P9 trial-0 acceptance (2026-10-05):

- From launch checkpoint `5ae0cf9`, `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment p9 --duration-s 0.1 --trial 0 --output data/results/milestone-4-parity-p9-1000-0-20261005-01` completes all three engines twice and exits successfully. [Case and exact metrics](../../evidence/milestone-4/cases/p9-1000-0/case.json). All nine validity/causal/pending checks and all eleven fixed/paired metric gates pass. Both paired executions report no state-budget violation or spike difference.
- Brian2 and MLX produce exactly **67 spikes / 30 active neurons**, including integer steps and pinned FlyWire identifiers. CPU PyTorch also produces 67 spikes / the same 30 active neurons and counts, with all 67 timing matches within ten steps; exact-step matches are 14 and one-step matches 53. MLX meets the equally strong comparator primary scores without a waiver.
- [Independent executed parent verification](../../evidence/milestone-4/cases/p9-1000-0/executed-verification.py) confirms pinned input/mapping hashes, regenerated canonical stimulus, all recorded executed-source hashes against the launch commit, all native repeated fields, complete 32-block paired coverage, all 1,001 actual physical-reference and 1,001 CPU digests, actual final pending original-row sets, and separately recomputed rational/count/correlation/timing scores using counters, exact fractions, the standard statistics module, and a dynamic program. [Verification](../../evidence/milestone-4/cases/p9-1000-0/verification.json), [24-file native observation archive](../../evidence/milestone-4/cases/p9-1000-0/observations.zip); every archived byte hash matches the preserved original. All full local C++ builds/results remain preserved.
- Total driver elapsed time is 638.776 seconds after input load, including preparation, complete observation, repeat, scoring, and collection. This is qualification timing, not a warm benchmark or unified-memory result. This accepts **2/52 cases only**. Next: pure reviewed diagnostic functions and another prescribed case. Commit this complete verified case before further work.

Integer time-bin diagnostic checkpoint (2026-10-05):

- At `62d045b`, implement the reviewed pure 100 ms count function with native integer steps, half-open bins, complete prescribed horizons, and explicit zero bins. Reject negative/horizon-end coordinates rather than silently losing events. Add the pure module to the enforced framework-free import boundary; existing case gates, files, commands, and numerical sources are unchanged.
- **294 application tests pass, zero failures/errors/skips**, including eight bin-boundary, valid-silence, invalid-step, and incomplete-horizon cases. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-time-bins-20261005-01.xml). All 143 files pass Ruff checks; strict Pyright has zero errors/warnings; all three dependency contracts pass (102 modules / 437 dependencies). The separately recorded 203-test scientific suite is not rerun for this pure diagnostic unit.
- Commit this passing working state before trial-separated pooled calculation. Full silenced-sugar trial 0 at 0.1 seconds is independently running from `62d045b`; acceptance remains **2/52 cases**.

Trial-separated pooling checkpoint (2026-10-05):

- At `6225167`, implement pure pooled count/rate diagnostics and sum timing matches within each supplied trial at the unchanged zero/one/ten-step windows. Counts use actual included-trial exposure; matched timing errors use the combined event distribution. No pooled acceptance decision is introduced. The new pure module is part of the enforced framework-free boundary.
- **296 application tests pass, zero failures/errors/skips**, including exchanged-trial and adjacent-trial-boundary counterexamples: pooled counts can agree while timing matches remain zero. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-trial-separated-pooling-20261005-02.xml). Explicit int64 count-vector annotations/resolution fix the initial two NumPy typing errors; all 145 files pass Ruff checks, strict Pyright has zero errors/warnings, and all three dependency contracts pass (103 modules / 442 dependencies).
- Commit this passing function before the remaining exposure/empty/window coverage and group integration. Existing single-case acceptance/calculations, numerical sources, commands, and artifacts are unchanged. The 203-test scientific suite remains the separate recorded regression; full silenced-sugar execution continues independently.

Pooled diagnostic intent coverage (2026-10-05):

- At `306b6a0`, add the remaining reviewed regressions: missing versus valid empty trials, undefined errors for added spikes against silence, valid-silent-trial exposure and CPU-only support, event-weighted F1/error distributions, separately matched windows, and timing across a count-bin boundary. No application source changes in this step.
- **304 application tests pass, zero failures/errors/skips**. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-pooled-diagnostic-intent-20261005-01.xml). All 145 files pass Ruff checks; strict Pyright has zero errors/warnings. The unchanged three dependency contracts and separate 203-test scientific regression remain recorded above. Commit this passing coverage before matrix group integration.

Matrix coverage checkpoint (2026-10-05):

- At `16c7e06`, derive all 12 diagnostic groups from the frozen 52-case matrix. Keep expected, included, missing, invalid, and failed trial identities separate. Refuse duplicate/unprescribed identities and failures without an included valid raster; no group acceptance flag or silent substitution exists.
- **310 application tests pass, zero failures/errors/skips**, including complete unobserved coverage, partial-group failure/invalid/missing separation, duplicate identities, absent failed rasters, and unprescribed trials. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-matrix-coverage-20261005-01.xml). All 147 files pass Ruff checks; strict Pyright has zero errors/warnings; all three dependency contracts pass (104 modules / 446 dependencies). No numerical or reference change.
- Commit this working state before combining coverage with pooled metrics/bin counts. Silenced-sugar paired first/repeat have completed; CPU first/repeat and final qualification remain independent pending work. Acceptance remains **2/52 cases**.

Combined group-diagnostic checkpoint (2026-10-05):

- At `a45918c`, combine valid three-engine case rasters with reviewed group coverage, common pooled support, trial-separated metrics, per-trial integer bins, and their pooled counts. Sort included trial identities; keep failed cases in the calculation and retain missing/invalid identities. Unobserved groups have unavailable metrics/counts. No aggregate acceptance flag or gate exists.
- **312 application tests pass, zero failures/errors/skips**, including a partial group's exact pooled count cancellation with zero timing matches and both individual failures retained. [Report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/3083d9fd9760f46b880e9b71ad86fdf7921e3bf4/docs/evidence/historical-tests/20261005/milestone-4-combined-diagnostics-20261005-02.xml). All 147 files pass Ruff checks; strict Pyright has zero errors/warnings; all three dependency contracts pass (104 modules / 450 dependencies). Explicit typed candidate fields replace unnecessary dynamic attribute access before this final report.
- Commit this passing composition before executing actual case summaries or further changes. Existing case/calculation contracts, numerical sources, and the separately recorded 203-test scientific suite remain unchanged. Full silenced-sugar CPU repeat is still running; acceptance remains **2/52 cases**.

Complete silenced-sugar trial-0 acceptance (2026-10-05):

- From launch checkpoint `62d045b`, the installed `qualify-parity` command runs `--experiment sugar-silenced --duration-s 0.1 --trial 0` into fresh `data/results/milestone-4-parity-sugar-silenced-1000-0-20261005-01`. All three engines complete twice; all nine validity/causal/pending checks and all eleven unchanged metric gates pass. [Case](../../evidence/milestone-4/cases/sugar-silenced-1000-0/case.json). Both paired executions have no state-budget violation or spike difference.
- Brian2 and MLX produce exactly **410 spikes / 21 active neurons**. CPU PyTorch produces 417 spikes across the same 21 neurons: count/neuronwise error `7/410`, 410 timing matches, timing F1 `820/827`, and common-support correlation `0.9900122232445101`. MLX has exact reference counts/timing and satisfies every paired gate.
- [Independent executed verification](../../evidence/milestone-4/cases/sugar-silenced-1000-0/executed-verification.py) confirms launch/current executed-source hashes, pinned mapping/data, regenerated events equal to the accepted unsilenced sugar schedule, full native replay/digest coverage, actual final pending identities, and separately recomputed exact metrics/dynamic-program matches. It checks **all 15,091,983 actual native reference weights**, with precisely 1,550 outgoing original rows zeroed; original rows are retained, and the repeat's native weight bytes agree. [Verification](../../evidence/milestone-4/cases/sugar-silenced-1000-0/verification.json), [24-file raw archive](../../evidence/milestone-4/cases/sugar-silenced-1000-0/observations.zip); every archived hash matches its preserved original.
- The first independent verifier attempt used the build directory for native weights and failed before writing a report. Reading the inspected first execution's `reference-results` fixes that path; the complete corrected verifier succeeds. All simulation/build outputs remain preserved. Driver elapsed time is 646.722 seconds after input load, a qualification measurement only.
- This accepts **3/52 cases**, with no gate, model, precision, or reference change. Next: execute the actual partial diagnostic summary and continue the prescribed matrix. Commit this verified case before further work.

Actual partial matrix-diagnostic evidence (2026-10-05):

- At clean `db2b51a`, execute the pure summary against the three retained complete case rasters. [Partial matrix report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-01/partial-matrix.json) includes **3 cases, 49 missing cases, and all 12 frozen groups**. The included sugar/P9/silenced-sugar groups each contain trial 0 only; every unobserved group's metrics/counts remain unavailable. No failure can be hidden by pooling or scored from missing output.
- [Executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-01/executed-verification.py) checks pinned input/mapping consistency, native mapped coordinates, unique/ranged spikes, source/artifact hashes, complete expected/included/missing coverage, and all bin sums. Every singleton pooled metric equals its independently verified complete case metric exactly. This is actual partial diagnostic execution, not evidence for five-trial pooling or full matrix acceptance.
- Preserve the final **312-passed / zero-skipped** [application report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-01/application-tests.xml) with this checkpoint. All recorded pure-unit quality/import checks remain valid; no application source changes here. Next: two-class trial 0 at 0.1 seconds, with all engine repeats and per-case gates. Commit this verified report before that execution.

Next prescribed case execution (2026-10-05):

- At clean launch checkpoint `1548295`, start the installed `qualify-parity --experiment two-class --duration-s 0.1 --trial 0` command with fixed Metal precision and fresh `data/results/milestone-4-parity-two-class-1000-0-20261005-01`. The reference build and both engine preparations finish; paired first observation is running. This case is pending and does not increase the accepted count.
- All source work and verified evidence are committed before launch. Inspect complete repeats, cause files, actual queues, and every case gate before acceptance; obtain bounded Astra judgment if a first divergence needs interpretation. Current acceptance remains **3/52**. Push remains pending because only the public reference `upstream` remote exists.

Complete two-class trial-0 acceptance (2026-10-05):

- From launch checkpoint `1548295`, the installed `qualify-parity --experiment two-class --duration-s 0.1 --trial 0` command completes all three engines twice in the fresh recorded output and exits successfully. [Case](../../evidence/milestone-4/cases/two-class-1000-0/case.json). All nine validity/causal/pending checks and eleven unchanged metric gates pass. Both paired executions have no state-budget violation or spike difference.
- Brian2 and MLX produce exactly **1,811 spikes / 370 active neurons**, with identical pinned identifiers and integer steps. CPU PyTorch produces 1,779 spikes / 385 active neurons: active Jaccard `364/391`, total count error `32/1811`, neuronwise error `218/1811`, common-support correlation `0.9849183597914548`, and 1,135 timing matches / F1 `227/359`. MLX passes every absolute and paired gate; no weaker comparator score changes the fixed floors.
- [Independent executed verification](../../evidence/milestone-4/cases/two-class-1000-0/executed-verification.py) checks source hashes against launch/current sources, pinned data/mapping, the exact code-4 / 23-channel canonical schedule, every native repeat field, complete paired/reference/CPU digest coverage, actual final pending original-row sets, and separately recomputed exact metrics and dynamic-program timing matches. [Verification](../../evidence/milestone-4/cases/two-class-1000-0/verification.json), [24-file native archive](../../evidence/milestone-4/cases/two-class-1000-0/observations.zip); all archive hashes match preserved originals. Full local builds/results remain preserved.
- Driver elapsed time is 637.168 seconds after input load, qualification timing only. This accepts **4/52 cases**. Next: refresh partial diagnostics and execute the shortest three-engine silent control. Commit this verified case before proceeding. The application remains at 312 passing tests, with its separately recorded 203-test scientific regression; numerical/reference sources are unchanged.

Four-case diagnostic refresh (2026-10-05):

- At clean `f95cbf8`, rerun the unchanged executed summary against all four retained complete cases. [Refreshed report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-02/partial-matrix.json) includes **4 cases, 48 missing cases, and all 12 groups**; unavailable groups remain explicit. Every singleton pooled metric and bin sum equals the corresponding complete case result.
- [Executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-02/executed-verification.py) records the current source and artifact hashes. This updates diagnostic evidence only; no model, gate, application code, or matrix-acceptance claim changes. Commit this verified refresh before the shortest silent control.

Shortest silent-control execution (2026-10-05):

- At clean launch checkpoint `f75cdb8`, start `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment silent --duration-s 0.1 --trial 0 --output data/results/milestone-4-parity-silent-1000-0-20261005-01`. Preserve all fresh native/physical observations and each independent repeat. The control is running and is not yet accepted; current acceptance remains **4/52 cases**.
- Next: inspect complete output, independently verify exact three-engine silence, empty canonical channel geometry, actual queues, full native replay/coverage, and unchanged empty/undefined metric rules. The existing non-silent 1,000-step verifier deliberately rejects an empty reference and must not be used to claim this control. Record its separate verification before acceptance, then continue remaining frozen trials/horizons and batch checks. All current source/evidence changes are committed; push remains pending without a user-owned remote.

Complete shortest three-engine silent-control acceptance (2026-10-05):

- The installed command launched at `f75cdb8` completes the full pinned-connectome silent trial 0 for 1,000 steps, including fresh Brian2/MLX paired first/repeat and original CPU first/repeat. The automatic [case report](../../evidence/milestone-4/cases/silent-1000-0/case.json) passes all nine case checks and eleven frozen metric checks; no first spike difference or common-history state-budget violation occurs.
- A separate [executed parent verifier](../../evidence/milestone-4/cases/silent-1000-0/executed-verification.py) checks actual native rasters before mapping, exact zero events in all three engines, canonical `(1, 1000, 0)` channel geometry, pinned input/mapping/source hashes, complete phase/physical/due coverage, and every first/repeat native field's dtype, shape, and bytes. All 18 actual future original-row queue sets are empty and agree. [Verification](../../evidence/milestone-4/cases/silent-1000-0/verification.json).
- Both candidate metric records match all **19 frozen empty-metric fields** independently: agreement Jaccard and timing F1 equal 1, count errors equal 0, and undefined ratios/correlations/timing-error/rate-error fields remain null. The [24-file raw archive](../../evidence/milestone-4/cases/silent-1000-0/observations.zip) matches every preserved original hash; no missing output is treated as silence.
- This accepts **5/52 cases only**. Current application/scientific checks remain 312/203 passed, zero skipped, with unchanged numerical/reference sources. Commit this verified control before the reviewed adjudication implementation or another case. The remaining 47 cases, full prescribed batch/repeat checks, matrix report, and performance remain open.

Per-case scientific adjudication review assignment (2026-10-05):

- At clean `361c748`, dispatch fresh-context `/root/review_case_adjudication` to **GPT-6 Astra at explicit `xhigh`**. Resolve how a concrete completed case can receive recorded scientific adjudication when its first spike difference is explained by rounding but the automatic report conservatively blocks every difference. Preserve the automatic report, bind the actual review scope/evidence, require independent parent verification, and retain every frozen fixed/paired/causal/replay gate.
- This review cannot alter model, precision, thresholds, references, physics, scope, or application/data contracts. It does not duplicate the completed four-trial first-difference classification or approve the not-yet-executed sugar trial-1 singleton. Await the completed review and verify/commit its decision before dependent implementation. Exact silent-control qualification remains independent running work.

Completed per-case adjudication policy (2026-10-05):

- Fresh Astra `xhigh` review is complete and independently checked at `10abe44`. [Decision and limits](../../evidence/milestone-4/case-adjudication/astra-review.md), [executed verification](../../evidence/milestone-4/case-adjudication/executed-verification.py), and [bound source/evidence record](../../evidence/milestone-4/case-adjudication/parent-verification.json). Preserve the original automatic report; a separate parent decision can accept an independently explained first difference only while every other validity/metric/native replay/own-ledger requirement passes.
- The only permitted false current case check is `first_different_spike_explicitly_none`. Any common-history budget failure still blocks acceptance. The prior batch classification requires explicit corresponding-native-evidence applicability before it can inform a singleton; this policy approves no not-yet-executed case. No model, gate, numerical method, command, application/data contract, or database/API schema changes.
- **21 causal/replay intent tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/policy-tests.xml). The first policy-verifier attempt exposed the historical sugar report's earlier explicit check format and stopped before output; the successful record checks that report separately and the exact current format on all four later cases. Commit this completed policy before implementing/testing the small evidence-only verifier, then execute sugar trial 1. Acceptance remains **5/52**.

Reviewed-case conjunction implementation (2026-10-05):

- At `a810fcd`, add the pure qualification [review prerequisites](../../../src/fly_brain/qualification/adjudication.py) and enforce its framework-free import boundary. Require the prescribed case, exact current nine/eleven check sets, only the first-spike check false, every frozen metric true, complete common-history audit with no budget violation, and an explicit first cause. This function checks prerequisites; it does not grant scientific approval.
- Twelve intent cases prove that an explained first spike cannot waive any fixed/paired metric. **324 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/conjunction-tests.xml). Ruff formatting/linting covers all 149 files; strict Pyright reports zero errors/warnings; all three import contracts and the unchanged 38-package offline lock pass. An initial strict typing diagnostic was resolved with explicit string-set types before this checkpoint.
- Commit this passing unit before adding case/audit refusal tests, rounding checks, and evidence binding. The original reporter, numerical/reference sources, and the separately recorded 203-test scientific regression remain unchanged; case acceptance stays **5/52**.

Reviewed-case prerequisite refusal coverage (2026-10-05):

- At `73bec21`, add nineteen refusal cases for every changed/failed validity flag, missing/extra validity or metric names, a first-step pre-threshold budget violation, truncated auditing, absent/out-of-horizon causes, empty affected-neuron sets, and an unprescribed silent trial. No application source changes in this unit.
- **343 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/prerequisite-refusal-tests.xml). All 149 files pass Ruff checks/formatting; strict Pyright has zero errors/warnings. Previously verified import/lock checks remain unchanged. Commit this passing test unit before native rounding checks; full evidence binding and independent case scoring remain next. Acceptance stays **5/52**.

Native rounding-prerequisite verification (2026-10-05):

- At `ef56d5c`, add the pure [native rounding checker](../../../src/fly_brain/qualification/rounding_review.py), within the enforced framework-free boundary. Preserve reference float64 volt values and MLX float32 millivolt values before comparison; require aligned finite native arrays, agreed eligibility, actual strict stored-precision predicates, the complete first-difference set, and unchanged state-error/margin budgets. This checks necessary evidence; it does not infer a scientific classification.
- Eight intent tests cover valid native predicates and refusal of omitted affected neurons, incorrect spike decisions, eligibility mismatch, budget failure, nonfinite values, wrong precision, and wrong geometry. **351 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/native-rounding-tests.xml). All 151 files pass Ruff checks/formatting; strict Pyright has zero errors/warnings; all three import contracts pass (106 modules / 455 dependencies).
- The parent executes the checker against the existing 138,639-neuron saved batch context, including every native threshold predicate and the full differing-neuron set. [Retained-context record](../../evidence/milestone-4/case-adjudication/retained-native-prerequisites.json). No device rerun, new cause classification, singleton approval, or gate change is claimed. Commit this passing unit before evidence hash/replay binding and independently scored singleton execution. Acceptance remains **5/52**.

Original case-evidence hash binding (2026-10-05):

- At `654ab3f`, add the qualification-only [file binding adapter](../../../src/fly_brain/qualification/adapters/case_binding.py). Require the complete original report/input/environment/native/phase/physical/final-state artifact set, both cause archives when a spike differs, exact manifest coverage, and matching SHA-256 (Secure Hash Algorithm 256-bit) content hashes. File operations remain at the domain edge; the adapter grants no scientific approval.
- Six real-file intent tests refuse changed reports, missing required originals or repeat cause contexts, and missing/extra manifest entries. **357 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/file-binding-tests.xml). All 153 files pass Ruff checks/formatting; strict Pyright has zero errors/warnings; all three import contracts pass (107 modules / 458 dependencies). The new binder also verifies all 24 preserved originals of the accepted silent case against its existing independent manifest.
- Commit this verified unit before complete coverage/replay binding and independent singleton scoring. The original automatic report, scientific execution, numerical methods, and case count remain unchanged; acceptance is **5/52**.

Complete case-replay coverage (2026-10-05):

- At `21fe89e`, add the qualification [complete replay adapter](../../../src/fly_brain/qualification/adapters/case_replay.py). Independently require the complete 32-step phase-block intervals, each block's native/queue/due coverage, every reference physical queue step including final state, the complete causal horizon, and the CPU initial/every-step native states. Existing dtype/shape/byte repeat checks also include all saved cause contexts. Identical truncated repeats cannot pass.
- Eight real-file tests cover a complete partial final block and identical first/repeat omissions of a phase tail, initial CPU state, final physical queue, due/native/queue digest coverage, or causal horizon. **365 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/complete-replay-tests.xml). All 155 files pass Ruff checks/formatting; strict Pyright has zero errors/warnings; all three import contracts pass (108 modules / 461 dependencies). The adapter also verifies the actual complete silent case and every saved native replay field.
- Commit this passing unit before digest-value validation and the independently scored reviewed-case proof. Numerical/reference functions, original automatic reports, and case acceptance remain unchanged at **5/52**.

Complete replay digest-value checks (2026-10-05):

- At `39e2fcb`, require valid 64-character hexadecimal content digests for every recorded phase, device queue, due-row set, physical queue step, and CPU native state. Five new faults prove that identical first/repeat files with malformed digest values fail despite complete-looking row counts.
- **370 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/digest-value-tests.xml). Full Ruff formatting/linting and strict Pyright pass. The actual accepted silent case passes the stronger checker. Commit this working state before cause-identity binding and final reviewed-case proof; acceptance remains **5/52**.

Reviewed decision case/cause identity binding (2026-10-05):

- At `7eb9369`, add the pure exact case/cause identity check: reviewed experiment, integer horizon, trial, first step, and complete affected-neuron tuple must equal the completed execution. Seven intent cases refuse another experiment/horizon/trial/step/neuron set or an omitted cause.
- **377 application tests pass, zero failures/errors/skips**. [Report](../../evidence/milestone-4/case-adjudication/cause-identity-tests.xml). Full Ruff formatting/linting and strict Pyright pass. One initial test insertion split an existing branch and failed collection; it was corrected before the successful run and commit. The failed report remains in `data/results/milestone-4-reviewed-cause-identity-20261005-01.xml`.
- Commit this passing identity unit before composing the independent counter/fraction/correlation/timing proof and executing sugar trial 1. All original reports, numerical/reference functions, and the frozen acceptance gates remain unchanged. No review inference from prose or broad check waiver is implemented; acceptance stays **5/52**.

Independent complete-score verification (2026-10-05):

- At `2722175`, execute a separate [Python counter/fraction/statistics scorer](../../evidence/milestone-4/case-adjudication/independent-score.py), using none of the application metric or gate functions. Recompute all **19 metric fields and 11 frozen checks** from the actual normalized native-coordinate records of all five accepted cases, including exact silence and CPU diagnostics. [Verified results and input hashes](../../evidence/milestone-4/case-adjudication/independent-score-verification.json).
- Every rational value and its encoded floating value matches exactly. Independently evaluated host diagnostic floats match within `1e-12`; that verification comparison never relaxes a case gate. All eleven independently recomputed fixed/paired gate booleans exactly match the recorded reports. A separate dynamic program verifies maximum matching cardinality at each 0/1/10-step window, and a trial-exchange counterexample refuses cross-trial matches despite equal pooled counts.
- The executed script passes Ruff formatting/linting. Existing 377 application / 203 scientific tests remain their separately recorded unchanged-source results. Decision confidence **99%** at `2722175`: use this scorer with the tested prerequisite, native-cause, hash, identity, and replay checkers for the next complete singleton. Commit this working proof before launch. No new case acceptance or full-matrix approval is claimed; acceptance stays **5/52**.

Next full sugar trial execution (2026-10-05):

- At clean `3b9e881`, launch `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment sugar --duration-s 0.1 --trial 1 --output data/results/milestone-4-parity-sugar-1000-1-20261005-01`. First launch check: 06:20:01 UTC. Preserve each engine's fresh complete first/repeat evidence and the unchanged automatic report/status.
- This trial is running and is **not accepted**. The earlier batch first-cause classification does not approve this singleton. On completion, independently recompute every metric/gate, verify complete native/physical/own-ledger replay, and inspect the entire first-cause context. Require explicit parent applicability or a new bounded cause review before a separate reviewed-case acceptance decision. Current acceptance remains **5/52**; all current work is committed before launch.

Partial matrix diagnostics with exact silence (2026-10-05):

- At clean `0148592`, execute the existing verified partial-matrix checker over all five accepted actual case rasters. [Report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-03/partial-matrix.json) retains all 12 prescribed groups, **5 included / 47 missing** case identities, explicit unavailable groups, and the zero-event silent bin.
- All 19 pooled metric fields of each included singleton equal its complete per-case record; every 100 ms bin count equals the actual spike count. [Executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-03/executed-verification.py) preserves source/artifact hashes. This is diagnostic evidence only; pooling never grants case acceptance. Commit the verified refresh while sugar trial 1 continues independently. No application source changes or new case pass.

Sugar trial-1 first-cause equivalence preflight (2026-10-05):

- At `f39d48f`, independently inspect the completed first singleton execution while its repeat continues. Its first different spike is step 999, neuron 41,514 / identifier 720575940620025620, with no common-history state-budget violation. All **108 corresponding current/preceding native context arrays** match the previously classified batch cause in dtype and bytes; native shapes also match except the documented scalar queue-offset storage representation. Actual clocks, source cursors, and due-mask hashes agree. [Executed comparison](../../evidence/milestone-4/cases/sugar-1000-1/executed-context-equivalence.py), [complete field mappings and hashes](../../evidence/milestone-4/cases/sugar-1000-1/context-equivalence-preflight.json).
- The legacy writer wrapped native int32 scalar offsets in length-one arrays; the current writer stores scalar arrays. The comparison explicitly documents that container-shape mapping without changing native payload bytes or accepting any other shape/precision change. This is necessary local applicability evidence, **not singleton classification or acceptance**. Complete singleton repetition, CPU comparisons, all eleven metric gates, full own-ledger/finiteness checks, and a final parent applicability decision remain pending. Commit this verified preflight before further work; acceptance remains **5/52**.

Complete sugar trial-1 reviewed acceptance (2026-10-05):

- The installed execution launched at `3b9e881` completes both fresh Brian2/MLX and original CPU runs. The [automatic report](../../evidence/milestone-4/cases/sugar-1000-1/case.json) retains `case_accepted: false`, `scientific_review_required: true`, and its actual first spike difference; the original [exit status 1](../../evidence/milestone-4/cases/sugar-1000-1/execution-status.json) remains recorded. Only `first_different_spike_explicitly_none` is false; all eight other validity checks and all eleven fixed/paired metric checks pass.
- Brian2 has **1,572 spikes**, MLX **1,571**, and the original CPU core **1,511**. MLX active Jaccard is 1; relative count/neuron errors are exactly `1/1572`; common-support correlation is `0.9999443982342281`; timing F1 is exactly `3142/3143`. A separate [executed verifier](../../evidence/milestone-4/cases/sugar-1000-1/executed-verification.py) independently reproduces all 19 metric fields and every gate, validates native coordinates/mapping/pins/regenerated input/source, and proves full native/physical/cause repetition and complete observation coverage. [Verification](../../evidence/milestone-4/cases/sugar-1000-1/verification.json).
- The only raster difference is the previously classified near-threshold decision at step 999, neuron 41,514. The singleton's own complete common-history audit has no budget failure. All 108 corresponding actual native current/preceding arrays and snapshot metadata match that reviewed batch cause under the recorded offset-container mapping; canonical trial input, actual leaves/weights/order, clocks, and eligibility agree. The prior batch review classified this cause; the parent verified its applicability to this singleton. Astra did not review or accept the singleton itself.
- Each engine's actual 18 future original-row queue sets is independently reconstructed from its own native spike history; complete final states remain finite and repeat. Cross-engine state/queue equality after the first spike difference is inapplicable. The [26-file raw archive](../../evidence/milestone-4/cases/sugar-1000-1/observations.zip) matches every preserved original hash, including both cause contexts.
- Engineering decision at `ee08474`, confidence **99%**: the separate [parent reviewed decision](../../evidence/milestone-4/cases/sugar-1000-1/reviewed-decision.json) accepts this case under the prospective rounding rule while preserving the original report and all other gates. This accepts **6/52 cases only**, with no tolerance, numerical-method, model, reference, output-contract, or scope change. Commit this verified case before the two-trial diagnostic refresh and next prescribed trial; 46 cases, complete batch/repeat checks, full parity, and performance remain open.

Two-trial sugar partial diagnostic verification (2026-10-05):

- At clean `7851afb`, extend the executed evidence checker to actual multi-trial groups. [Partial report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-04/partial-matrix.json) retains all 12 frozen groups and **6 included / 46 missing** identities. Both actual sugar trials contribute to pooled count/rate diagnostics and independently counted 100 ms bins; timing matches remain within their own trial/neuron/window. All 19 fields are independently reproduced with counters, rational arithmetic, statistics, and separate maximum-match dynamic programs. [Executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-04/executed-verification.py).
- Preserve sugar trial 1 in `automatic_unaccepted_cases_preserved` while its exact case/cause identity and bound complete parent decision qualify it in `parent_reviewed_accepted_cases`. Every local review/verification/archive hash and external review hash is checked before using that disposition. Group failure coverage uses the verified scientific case disposition; no pooled metric grants acceptance or hides an automatic result.
- Decision confidence **99%** at `7851afb`: retain these separate statuses and the fully verified multi-trial diagnostics. No application source, schema, case gate, or numerical method changes. Existing 377 application / 203 scientific tests remain their recorded unchanged-source results. Commit this verified report before sugar trial 2; acceptance remains **6/52**.

Sugar trial-2 complete execution (2026-10-05):

- At clean `743a859`, launch `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment sugar --duration-s 0.1 --trial 2 --output data/results/milestone-4-parity-sugar-1000-2-20261005-01`. First launch check: 06:40:56 UTC. All verified source/evidence changes are committed before execution; each engine receives fresh first/repeat state.
- The execution completes with exit status zero in 640.622 seconds after input load. Its independent verification and acceptance are recorded below. This is qualification timing; full matrix/batch/performance requirements remain open. Push remains pending without a user-owned remote.

Complete automatic-case independent verifier (2026-10-05):

- At `840e327`, extend the separate [automatic 1,000-step verifier, preserved byte for byte](../../evidence/milestone-4/cases/sugar-1000-2/executed-verification.py) to require the exact current nine/eleven check sets, full native/physical/due coverage and replay, actual-source native paths/precision/finiteness, canonical trial input, exact common-history final queues, and all **19 independently recomputed metric fields / 11 gates**. A first difference or silent reference is outside this verifier's scope and fails; no reviewed-case waiver is applied.
- Execute it against the already accepted complete P9 trial-0 case launched at `5ae0cf9`. [Control verification](../../evidence/milestone-4/case-adjudication/automatic-verifier-control.json) rechecks all 24 original hashes and reproduces the CPU timing diagnostics through separate matching windows. The original accepted P9 [raw archive](../../evidence/milestone-4/cases/p9-1000-0/observations.zip) remains its versioned trace source. This is a verifier regression, not a new case execution or duplicate acceptance.
- The script passes Ruff formatting/linting. Application/numerical sources and the existing 377 application / 203 scientific results remain unchanged. Commit this passing verifier before inspecting the running sugar trial-2 result; acceptance stays **6/52**. Complete longer horizons, prescribed batch checks, and performance remain open.

Complete sugar trial-2 case acceptance (2026-10-05):

- At clean `c6a6f46`, independently verify the completed execution from `743a859` with the committed automatic 1,000-step verifier. [Case report](../../evidence/milestone-4/cases/sugar-1000-2/case.json), [verification](../../evidence/milestone-4/cases/sugar-1000-2/verification.json), and [executed verifier](../../evidence/milestone-4/cases/sugar-1000-2/executed-verification.py) record all nine case checks, eleven fixed/paired metric gates, and all nineteen independently recomputed metric fields.
- Brian2 and MLX have **1,535 exactly matching spikes**. All MLX primary metrics are exact agreement; original CPU PyTorch has 1,581 spikes, activity Jaccard `19/23`, relative count error `46/1535`, neuron count error `214/1535`, common-support correlation `0.982663832153464`, and timing F1 `464/779`. No common-history budget violation or first spike difference occurs in all 1,000 steps.
- Every native phase, physical queue, due-row digest, final array, and actual spike raster repeats exactly within each engine. Actual final future original-row queue sets agree across Brian2/MLX; source hashes, input pins, neuron mapping, canonical trial stimulus, native precision, and complete observation coverage pass. The [24-file raw archive](../../evidence/milestone-4/cases/sugar-1000-2/observations.zip) matches every preserved original hash; all eight copied evidence files match the executed proof output.
- This accepts **7/52 cases only**. Six cases have exact MLX/reference rasters; sugar trial 1 retains its separate reviewed decision and original automatic refusal. No application or numerical source changes. Existing 377 application / 203 scientific test results remain their separately recorded unchanged-source evidence. Commit this verified case before refreshing partial diagnostics or starting the next case; 45 cases, prescribed batch/repeat checks, full parity approval, and performance remain open.

Three-trial sugar partial diagnostic verification (2026-10-05):

- At clean `8fa78ba`, rerun the committed multi-trial checker against all seven versioned cases. The [partial report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-05/partial-matrix.json) records **7 included / 45 missing** cases in all 12 prescribed groups. [Executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-05/executed-verification.py) independently reproduces all nineteen pooled metric fields and every actual trial/pooled 100 ms bin. Sugar trials 0, 1, and 2 contribute; timing matches remain within each trial and neuron.
- Sugar trial 1 remains explicitly listed as originally unaccepted automatically and separately accepted by its bound parent review. No pooled metric changes an individual gate or supplies matrix acceptance. Both copied files match the executed output; application and numerical sources remain unchanged. Commit this verified diagnostic before sugar trial 3; acceptance remains **7/52**.

Sugar trial-3 complete execution (2026-10-05):

- At clean `8b5cf1c`, launch `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment sugar --duration-s 0.1 --trial 3 --output data/results/milestone-4-parity-sugar-1000-3-20261005-01`. First launch check: 06:55:37 UTC. All preceding verified work is committed; the output is fresh and each engine runs first/repeat state independently.
- The complete first/repeat execution finishes with exit status zero in 641.917 seconds after input load. Independent verification and acceptance are recorded below; this is qualification timing only. The remaining matrix, prescribed batch checks, full parity, and performance remain open. Push remains pending without a user-owned remote.

Prescribed-horizon evidence verifier (2026-10-05):

- At `2e63105`, remove fixed 1,000-step assumptions from the [automatic case verifier](../../evidence/milestone-4/case-adjudication/automatic-case-verifier.py). Canonical input, native observation coverage, clock bounds, last-consumed/future physical queue slots, and metric exposure now use the exact prescribed case horizon. Every original nine/eleven gate, precision/source check, exact common-history raster requirement, and independent nineteen-field score remains mandatory. Silent or reviewed-difference cases require their separate verification.
- The [three actual regression controls](../../evidence/milestone-4/case-adjudication/automatic-horizon-verifier-controls.json) independently reverify P9 trial 0, sugar trial 2, and outgoing-silenced sugar trial 0. All original raw manifests, actual queue sets, coverage, metrics, and gates match. The earlier verifier remains byte-identical in the sugar trial-2 artifact, including the original control's program hash. Ruff formatting/linting pass; no application/numerical source changes.
- Decision confidence **99%** at `2e63105`: commit this bounded verification-tool update before dependent use. These controls execute saved 1,000-step evidence; longer native cases remain unexecuted and unaccepted. No new case execution or acceptance is supplied by this regression. Sugar trial 3 is independently running; acceptance remains **7/52**.

Complete sugar trial-3 case acceptance (2026-10-05):

- At clean `c14311a`, run the committed prescribed-horizon verifier against the complete execution launched at `8b5cf1c`. All nine case checks, eleven fixed/paired gates, and nineteen independently recomputed metric fields pass. [Case report](../../evidence/milestone-4/cases/sugar-1000-3/case.json), [verification](../../evidence/milestone-4/cases/sugar-1000-3/verification.json), and [executed verifier](../../evidence/milestone-4/cases/sugar-1000-3/executed-verification.py).
- Brian2 and MLX have **1,584 exactly matching spikes**. All MLX primary metrics show exact agreement. Original CPU PyTorch has 1,558 spikes, active Jaccard `167/180`, count error `13/792`, neuron count error `23/264`, common-support correlation `0.9911242661219075`, and timing F1 `1057/1571`. All 1,000 steps have no common-history budget violation or first spike difference.
- Native phase/state, actual physical queues and due rows, final arrays, and spike coordinates repeat exactly within every engine. Source/input/mapping/stimulus/precision checks and complete observation coverage pass; actual future original-row queue sets agree across Brian2/MLX. The [24-file archive](../../evidence/milestone-4/cases/sugar-1000-3/observations.zip) matches every original hash, and all eight copied artifacts match the executed verification output.
- This accepts **8/52 cases only**: seven exact MLX/reference rasters and sugar trial 1's unchanged reviewed acceptance. No application or numerical source changes; the separately recorded 377 application / 203 scientific test results remain unchanged. Commit this verified case before the partial diagnostic refresh or next case. The remaining 44 cases, required batch/repeat gates, full parity approval, and performance remain open.

Required one-second batch evidence review (2026-10-05):

- At clean `f3abcaf`, prepare the [bounded batch verification assignment](../handoffs/astra-full-batch-verification.md) for fresh-context GPT-6 Astra at explicit `xhigh`. Determine sufficient native/replay evidence for actual sugar/P9 four-trial one-second batches versus independent trials 0–3, including the unchanged original CPU comparator. The earlier 0.1-second memory proof qualifies neither the required duration nor all independent trials.
- This is a read-only scientific evidence-method review. Await completion and parent source/evidence verification before dependent batch implementation. Sugar trial 3's existing CPU executions are independent and remain running; no source, metric, scope, or acceptance changes are authorized by dispatch. Acceptance remains **7/52**.
- Dispatched from `52a8784` to `/root/review_full_batch_verification`, fresh-context `gpt-6-astra` / `xhigh`. The child owns only this bounded read-only review; Sol retains all implementation and case verification.

Sugar trial-4 complete execution (2026-10-05):

- At clean `9a71a4c`, launch `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment sugar --duration-s 0.1 --trial 4 --output data/results/milestone-4-parity-sugar-1000-4-20261005-01`. First launch check: 07:08:25 UTC. All preceding verified work is committed; this trial remains an independent singleton, as prescribed.
- The complete first/repeat execution finishes with exit status zero in 639.533 seconds after input load. Its independent verification and acceptance are recorded below; this is qualification timing only. Full matrix/batch/performance requirements remain open.

Four-trial sugar partial diagnostic verification (2026-10-05):

- At clean `8427094`, the committed checker independently reproduces all nineteen pooled metric fields and all actual trial/pooled 100 ms bins for the eight versioned cases. [Partial report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-06/partial-matrix.json) and [executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-06/executed-verification.py) preserve all 12 prescribed groups and **8 included / 44 missing** cases. Sugar trials 0–3 are independently executed singleton inputs to the diagnostic; this is not a batch execution.
- Timing matches remain within each trial and neuron. Sugar trial 1 retains its original automatic refusal and separate bound parent acceptance; no pooled metric grants acceptance. Both copied files match the executed output. No application/numerical source changes; sugar trial 4 remains independently running and unaccepted. Commit this verified diagnostic now; acceptance remains **8/52**.

Required batch-method review resolved (2026-10-05):

- `/root/review_full_batch_verification` returns its completed source-grounded decision: use actual four-trial sugar/P9 one-second executions, full native per-trial equality with matching independent runs, and fresh batch repetition. [Recorded review and mismatch conditions](../../evidence/milestone-4/batch-verification/astra-review.md). Original CPU collection already supports a real four-row model; MLX needs a small internal collector/verifier around the existing observer. No numerical-core change is required.
- Sol independently inspects the observer/ledger/hash/CPU schedule and verifies [all 13 reviewed source hashes](../../evidence/milestone-4/batch-verification/source-verification.json) against assignment `52a8784`. The [executed parent proof](../../evidence/milestone-4/batch-verification/executed-verification.py) additionally compares the retained actual 0.1-second MLX batch with all four completed singleton observations: every native phase, boundary queue, due-mask block and all thirteen final fields match exactly, with canonical input and bound original artifact hashes. [Parent verification](../../evidence/milestone-4/batch-verification/parent-verification.json).
- Confidence **99%** at `c114523`: accept this evidence method and commit the completed review/verification before dependent internal batch implementation. A differing digest requires bound fresh observations; same-engine spike differences cannot use the cross-engine rounding policy. Existing 0.1-second proof, fixture tests, and source reasoning do not close the required one-second duration, batch repetition, or CPU batch gates. Acceptance remains **8/52**; sugar trial 4 is independently running. No application or numerical source changes occur in this decision checkpoint.

Internal four-trial MLX collector checkpoint (2026-10-05):

- At `4119254`, implement the reviewed [MLX batch collector](../../../src/fly_brain/qualification/adapters/mlx_batch_collect.py) in the qualification adapter. Four-trial geometry varies; numerical arithmetic stays invariant. Success requires complete native phase/queue/due capture, spike coordinates, and fresh-state repetition. The collector injects the existing execution/connectome/stimulus, creates fresh state and ledger, streams bounded blocks, rejects failed ledger or missing coverage, and writes complete native final state. No single-case runner, numerical core, public interface, or output contract changes.
- **13 real Metal observer/collector tests pass, zero failures/errors/skips**, covering populated/empty fixtures, every actual native phase/final field, physical queue and due digests, spike coordinates, fresh repeat, existing observer/batch equivalence, and forced final-trial/final-slot ledger failure. [Report](../../evidence/milestone-4/batch-verification/collector-tests.xml). The [application report](../../evidence/milestone-4/batch-verification/collector-application-tests.xml) passes **377 tests**, zero failures/errors/skips.
- [Verification](../../evidence/milestone-4/batch-verification/collector-verification.json): all 158 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; all three import contracts pass across 110 files / 472 dependencies. Existing 203-test scientific evidence is unchanged; this focused run does not claim a new full-suite result. Commit this passing working state before adding the batch/singleton verifier. Acceptance remains **8/52**; sugar trial 4 is independently running against unchanged numerical/singleton sources, and required one-second batch execution/repetition remains open.

Complete sugar trial-4 case acceptance (2026-10-05):

- At clean `71c9b3b`, independently verify the complete execution launched at `9a71a4c`. All nine case checks, eleven fixed/paired gates, and nineteen independently recomputed metric fields pass. [Case report](../../evidence/milestone-4/cases/sugar-1000-4/case.json), [verification](../../evidence/milestone-4/cases/sugar-1000-4/verification.json), and [executed verifier](../../evidence/milestone-4/cases/sugar-1000-4/executed-verification.py).
- Brian2 and MLX have **1,437 exactly matching spikes**, with exact agreement on all MLX primary metrics. Original CPU PyTorch has 1,593 spikes, active Jaccard `303/319`, count error `52/479`, neuron count error `188/1437`, common-support correlation `0.9871903593609298`, and timing F1 `1076/1515`. All 1,000 steps have no common-history budget violation or first spike difference.
- Every engine's native phases/states, physical queues, due records, final arrays, and raster repeat exactly. Complete coverage, canonical stimulus, source/input/mapping/native precision checks pass; actual future original-row queue sets agree across Brian2/MLX. The [24-file raw archive](../../evidence/milestone-4/cases/sugar-1000-4/observations.zip) matches every original hash and all eight evidence copies match the executed output. The case's executed sources match launch/current source; the separately committed batch collector was not used by this singleton run.
- This accepts **9/52 cases only** and completes all five sugar singleton trials at 0.1 seconds. Eight accepted cases have exact MLX/reference rasters; sugar trial 1 retains its original automatic refusal and separately verified reviewed acceptance. Commit this verified case before the five-trial diagnostic or next case. All remaining 43 cases, required one-second batch/repeat checks, full parity approval, and performance remain open.

Complete shortest sugar group diagnostic (2026-10-05):

- At clean `501fc9b`, independently reproduce all nineteen pooled metric fields and actual per-trial/pooled 100 ms bins for all nine accepted cases. [Partial matrix report](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-07/partial-matrix.json) and [executed verification](../../evidence/milestone-4/matrix-diagnostics/partial-20261005-07/executed-verification.py) preserve all 12 required groups and **9 included / 43 missing** cases.
- Sugar's 0.1-second group now includes exactly trials 0–4 with no missing, invalid, or scientifically failed trial. Each has its own complete three-engine first/repeat evidence. Sugar trial 1 still retains its original automatic refusal and separate bound parent acceptance. Timing matches remain within their own trial/neuron; pooled diagnostics do not change any case gate. This is the first complete five-singleton group, not a batch pass or full-matrix acceptance.
- Both copied artifacts match the executed output. Commit this verified report before the next case or batch-verifier implementation. Acceptance remains **9/52**; all longer horizons, remaining shortest trials, required batch/repeat checks, full parity, and performance remain open.

First one-second sugar case execution (2026-10-05):

- At clean `55ea35f`, launch `MLX_ENABLE_TF32=0 uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment sugar --duration-s 1 --trial 0 --output data/results/milestone-4-parity-sugar-10000-0-20261005-01`. First launch check: 07:23:30 UTC. All preceding working states are verified and committed. This is the prescribed **10,000-step** singleton with two fresh executions per engine, unchanged numerical sources, fixed precision, and a fresh output.
- Engineering decision at `55ea35f`, confidence **99%**: advance the required sugar duration now that its five shortest trials are complete, while independently qualifying the reviewed batch-verification adapter. This tests the central experiment over the next required horizon before filling the other remaining shorter trial groups; the complete 52-case scope is unchanged.
- This case is running and unaccepted. Require all fixed/paired metric gates, all-neuron common-history budgets and first-cause interpretation, every actual queue/native repeat, complete 313-block/10,001-snapshot coverage, canonical prefix/input/source/mapping/precision checks, and independent parent verification. Acceptance remains **9/52**; the remaining matrix, actual one-second batch/repeat checks, full parity approval, and performance remain open.

Complete batch-phase rules checkpoint (2026-10-05):

- At `4cf2356`, add [pure batch phase-evidence rules](../../../src/fly_brain/qualification/batch_evidence.py) and include them in the enforced framework-free boundary. Require the full prescribed horizon, exact block order/partial tail, all four singleton identities, and every native/queue/due hash. A changed digest returns an explicit unresolved block/trial/field; it cannot infer a numerical tolerance result or grant batch acceptance.
- **395 application tests pass, zero failures/errors/skips**, including eighteen new intent cases for complete 35/1,000/10,000/100,000-step coverage, identical truncated streams, missing/malformed field hashes, changed native/queue/due evidence, duplicate/wrong-size blocks, and missing singleton identities. [Test report](../../evidence/milestone-4/batch-verification/phase-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/phase-verification.json).
- All 160 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 111 files / 476 dependencies; the unchanged lock resolves 38 packages offline. Commit this passing unit immediately. This is phase evidence only: canonical identity, final native arrays/spikes, CPU snapshots, and actual one-second batch/repeat execution remain required. No numerical or running singleton source changes; acceptance remains **9/52** and the one-second sugar case is still running.

Actual batch-phase rule control (2026-10-05):

- At clean `f4994c8`, run the committed pure phase rules on the retained actual 0.1-second four-trial MLX batch and the four matching singleton observations. [Control record](../../evidence/milestone-4/batch-verification/actual-phase-control/actual-phase-control.json) and [executed verification](../../evidence/milestone-4/batch-verification/actual-phase-control/executed-verification.py) revalidate every original artifact hash bound by the completed parent proof. All 32 native phase/queue/due blocks match for each trial.
- Both copied files match the executed output and bind the exact committed phase-rule source. This is a saved-evidence regression, not a new execution or batch acceptance. The 395 application / 13 focused Metal results remain their separately recorded evidence; canonical identity/final-array/spike/CPU checks and actual one-second batch/repeats remain open. Commit this verified control now. The one-second sugar case remains running, and acceptance stays **9/52**.

Complete CPU batch snapshot rules (2026-10-05):

- At `85c3c75`, add pure complete native snapshot coverage and batch/singleton comparison alongside the committed phase rules. Require the initial step -1 and every actual step through the prescribed final horizon, all four trial digests and matching independent identities. A changed digest identifies an unresolved trial/step; exact hashes do not replace canonical input, final-array, spike, or fresh-repeat verification. No executing singleton, CPU observer, or numerical source changes.
- **401 application tests pass, zero failures/errors/skips**, including six new intent cases for complete native equality, changed/swapped/missing trials, omitted initial/final snapshots, wrong chronology, absent trial hashes and malformed digests. [Report](../../evidence/milestone-4/batch-verification/native-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/native-verification.json). All 160 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 111 files / 476 dependencies.
- Commit this passing state immediately, before the final native-array/spike adapter. The one-second sugar case remains running and unaccepted; acceptance remains **9/52**, and the required actual one-second batch/repeat checks remain open.

Native batch final-field checkpoint (2026-10-05):

- At `73d369d`, add the small qualification-owned [native final-field validator](../../../src/fly_brain/qualification/adapters/batch_native.py). It requires every MLX phase/final field, all nineteen physical Boolean queue slots, or all five original CPU float32 fields including its nineteen-slot neuron-payload buffer. Enforce actual one/four-trial geometry, original float32/Boolean/int32 precision, int64 coordinate dimensions, complete field sets and finiteness. The singleton MLX's existing flattened fields are preserved. No engine, running singleton, or public contract changes.
- **417 application tests pass, zero failures/errors/skips**, including sixteen new cases covering both engines and geometries, missing/extra state, cast precision, omitted queue slots, nonfinite state and incomplete coordinate arrays. [Report](../../evidence/milestone-4/batch-verification/fields-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/fields-verification.json). All 162 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 112 files / 479 dependencies.
- Commit this passing working state immediately. Exact trial equality, validated spike coordinates, canonical identity, fixture execution and actual one-second batches/repeats remain required. The independent one-second sugar case remains running and unaccepted; acceptance stays **9/52**.

Native batch spike-coordinate checkpoint (2026-10-05):

- At `0406861`, add actual trial-separated spike validation to the native adapter. Reuse the established coordinate rules for original int64 precision, pinned neuron/horizon bounds and duplicate refusal. Preserve actual four-trial identity; repeated neuron/step pairs across different trials remain valid, while pooled counts cannot hide missing/malformed trial coordinates. The existing singleton MLX implicitly has trial row zero.
- **425 application tests pass, zero failures/errors/skips**, including eight new cases covering identical coordinates across trials, empty singleton raster, out-of-bounds neuron/step/trial, duplicates, cast coordinates, absent batch trials and malformed shapes. [Report](../../evidence/milestone-4/batch-verification/spikes-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/spikes-verification.json). Four initial strict-typing errors on the dynamically loaded array were corrected with a guarded native type annotation; all 162 Python files pass Ruff formatting/linting, strict Pyright reports zero errors/warnings, and three import contracts pass across 112 files / 481 dependencies.
- Commit this passing state before exact final native/raster comparison. No core, observer or running singleton changes; acceptance stays **9/52**. Canonical identity, fixture execution and actual one-second batches/repeats remain open.

Exact batch final-state comparison checkpoint (2026-10-05):

- At `973f5ee`, compare each actual batch trial's complete native final fields and raster with its corresponding singleton. Validate both complete native geometries before comparing bytes. The original MLX queue is compared slot-by-slot within the same engine; the CPU float32 payload buffer retains its own trial-first layout. Same-engine spike, Boolean, integer clock and CPU refractory/spike-state differences fail the exact requirement. Continuous byte differences return explicit unresolved field names; no tolerance or causal acceptance is inferred.
- **432 application tests pass, zero failures/errors/skips**, including seven new cases for both engines, per-trial continuous differences, same-engine spike changes, discrete queue/clock/input/refractory changes, and a signed-zero difference in the final CPU payload slot. [Report](../../evidence/milestone-4/batch-verification/finals-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/finals-verification.json). All 162 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 112 files / 481 dependencies.
- Commit this passing state immediately before connecting the checks to actual fixture collectors. Canonical input/source/case binding, real fixture qualification and actual one-second batches/repeats remain required. No engine, observer or running singleton changes; acceptance remains **9/52**.

Saved batch-evidence adapter checkpoint (2026-10-05):

- At `c5cc980`, connect the pure complete coverage rules and native final/raster comparator in the small internal [batch evidence adapter](../../../src/fly_brain/qualification/adapters/batch_verify.py). Read the actual existing singleton MLX/Brian2 two-hash format, four-trial MLX streams, original CPU snapshots and native final archives. Compare each prescribed identity; retain explicit unresolved stream and continuous-field differences. Keep at most the batch final arrays and one singleton's final arrays in memory. No public command or singleton/engine source changes.
- **434 application tests pass, zero failures/errors/skips**. Two new file integration checks exercise both complete saved geometries, populated per-trial spike coordinates, the final partial block/snapshot, changed trial-3 digests and omitted final coverage. [Report](../../evidence/milestone-4/batch-verification/saved-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/saved-verification.json). One initial fixture typing error was corrected by assigning its stream name before the loop. All 164 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 113 files / 488 dependencies.
- Commit this passing state before actual fixture qualification. Saved synthetic equality is not batch acceptance: canonical input/source/case binding, actual four-trial engine execution and fresh repetitions remain required. The one-second sugar case remains independently running and unaccepted; acceptance stays **9/52**.

Actual batch collector/verifier fixture qualification (2026-10-05):

- At `7b54c4a`, execute real populated/empty 101-step, six-neuron, four-trial fixtures through the new MLX collector and unchanged CPU collector. Compare both fresh batch repetitions with four actual independently initialized singleton collections; those singleton MLX observations use the unchanged Brian2/MLX paired collector. Every native MLX phase/queue/due block, CPU initial-through-final snapshot, final native field and trial-separated spike raster matches. All eight small Brian2 singleton builds have complete causal coverage and no spike/budget difference.
- **Seven focused real Metal/reference checks pass, zero failures/errors/skips**, in 55.01 seconds, with 123 dependency warnings. [Report](../../evidence/milestone-4/batch-verification/fixture-tests.xml), [verification/source/artifact hashes](../../evidence/milestone-4/batch-verification/fixture-verification.json), and [complete collected native evidence](../../evidence/milestone-4/batch-verification/fixtures.zip). The sandbox attempt stopped at import without Metal access; the authorized device-access rerun executed every check. All 165 Python files pass Ruff formatting/linting and strict Pyright reports zero errors/warnings. Application code is unchanged since its separately recorded 434-test pass; the prior complete 203-test scientific run is not rerun or enlarged by this focused result.
- Commit this passing fixture implementation and execution evidence immediately. The full one-second sugar singleton has completed its first paired execution and is repeating it. Its first spike difference is step 5,719, with no common-history budget violation; its scientific interpretation and full case acceptance remain unresolved. Canonical full-network batch identity and prescribed one-second batch/repeat execution remain open. Acceptance stays **9/52**; no full-network batch or parity pass is granted.

First one-second sugar cause review preparation (2026-10-05):

- At clean `c71df83`, independently verify and preserve the completed first paired execution's new cause at step 5,719, neuron 100,750 / FlyWire identifier 720575940630820919. [Preflight/source/artifact hashes](../../evidence/milestone-4/one-second-sugar-cause/first-cause-preflight.json), [executed proof](../../evidence/milestone-4/one-second-sugar-cause/executed-preflight.py), and [immutable first-observation archive](../../evidence/milestone-4/one-second-sugar-cause/first-observation.zip) bind all 112 native context arrays, complete 313-block / 10,001-physical-snapshot first-run coverage and every executed source against launch/current source. Direct current pre-threshold and previous pre/before/end all-neuron voltage/conductance budgets pass.
- Actual strict predicates differ with agreed eligibility: Brian2 pre-voltage `-0.04499995946946667` volts, MLX exactly `-45.0` millivolts. Host-comparison error `0.00004053053332597756` millivolts is below the unchanged `0.0014499995946946668` millivolt budget. These are prerequisites only. No source or numerical change occurs; the full execution continues its fresh repeats/CPU checks. All three evidence copies match the executed output.
- Prepare the [bounded cause assignment](../handoffs/astra-one-second-sugar-cause.md) for fresh-context Astra at explicit `xhigh`. Request scientific classification of this complete new cause, not case approval; the earlier sugar-trial-1 review cannot classify it. Commit this verified preparation before dispatch. Acceptance remains **9/52**; full metrics/replays/case acceptance and prescribed batch checks remain open.

First one-second cause review dispatched (2026-10-05):

- At clean `2c9fd6b`, dispatch `/root/review_one_second_sugar_cause` with fresh context, explicit `gpt-6-astra` and `xhigh`. [Dispatch and assignment hash](../../evidence/milestone-4/one-second-sugar-cause/dispatch.json). The assignment is read-only and excludes dependent implementation, full-case acceptance and any tolerance/model/reference changes. Sol continues only independent batch identity work while awaiting the completed result.
- The existing one-second execution and every current owner remain unchanged. The review is pending; no classification or acceptance is implied by dispatch. Commit this record now. Acceptance stays **9/52**.

Canonical batch trial identity checkpoint (2026-10-05):

- At clean `1cdf02c`, add the qualification-owned [canonical stimulus identity rules](../../../src/fly_brain/qualification/batch_identity.py) to the enforced framework-free boundary. Independently supplied canonical generation must match actual native batch/singleton event bytes, trial order, complete horizon/channel shape, targets/rates, seed/generator and declared event hashes. Every singleton must have its actual prescribed identity. Equal bytes in silent trials cannot hide swapped identities; casts, corrupted bits and altered metadata are refused.
- **448 application tests pass, zero failures/errors/skips**, including fourteen new checks using actual frozen generator output for sugar, P9 and silence, swapped/missing identities, wrong order/seed/generator/channel/rate/hash, changed event bytes, truncated horizon, cast precision and noncanonical bit values. [Report](../../evidence/milestone-4/batch-verification/identity-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/identity-verification.json). All 168 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 114 files / 492 dependencies; the unchanged lock resolves 38 packages offline.
- Commit this passing unit immediately. Full input pins/mapping, executed source/environment and accepted singleton-case binding remain required alongside actual one-second batch/repeat execution. No numerical or executing singleton source changes occur. Astra's independent first-cause classification is pending and the one-second case remains unaccepted; acceptance stays **9/52**.

One-second sugar first-cause classification verified (2026-10-05):

- `/root/review_one_second_sugar_cause` completes its fresh-context Astra `xhigh` review and bounded reproducibility follow-up. It classifies this new step-5,719 / neuron-100,750 difference as explained finite-precision trajectory roundoff, confidence **99%**, with no indicated implementation change. [Recorded classification, source/array details and limits](../../evidence/milestone-4/one-second-sugar-cause/astra-review.md). This finding classifies the cause only; it does not approve the complete case.
- At clean `9ab33d5`, Sol inspects and independently executes the exact [host diagnostic](../../evidence/milestone-4/one-second-sugar-cause/executed-host-proof.py). [Structured parent proof](../../evidence/milestone-4/one-second-sugar-cause/parent-host-proof.json) confirms 9,723 preceding matching spikes, complete affected set, original deliveries/weights/leaves/input gates, corrected eligibility from preceding clocks, and 206 available updates from the last common reset. All 31 due / 3 discarded / 28 accepted rows reconstruct the saved voltage/synaptic values at both retained steps exactly in both native precisions. Direct reference clock/raster/source/hash controls and every copied artifact pass.
- Commit this completed review and verification before dependent case adjudication. The complete one-second execution remains active and unaccepted; its fixed/paired metrics, fresh native/physical/cause repeats, own future queues and independent full-case verification remain required. The existing 448 application / seven focused real batch checks are unchanged separate evidence. No source or numerical change occurs; acceptance stays **9/52**.

Completed cause-to-execution binding checkpoint (2026-10-05):

- At clean `7e5d80b`, add the qualification-owned completed-review binding in [case binding](../../../src/fly_brain/qualification/adapters/case_binding.py). Require this prescribed case and complete first-cause set, a completed explained-roundoff classification, all seven bound review artifacts, the exact launch, complete original first-observation files and every original archive member byte. This binds a classification; it does not grant case acceptance.
- **461 application tests pass, zero failures/errors/skips**, including thirteen new intent checks for pending/unexplained reviews, wrong identities, changed/missing proof, changed native cause, incomplete manifests/archives, wrong launch, and failed budget/threshold prerequisites. [Report](../../evidence/milestone-4/case-adjudication/review-binding-tests.xml) and [verification/source hashes](../../evidence/milestone-4/case-adjudication/review-binding-verification.json). All 169 Python files pass Ruff formatting/linting, strict Pyright reports zero errors/warnings, and three import contracts pass across 115 files / 497 dependencies. The same adapter independently binds the actual one-second first execution to all eight committed review/decision hashes.
- Commit this passing state immediately before full reviewed-case verification. Both paired executions are complete; the original CPU reference execution continues. Complete metrics, fresh native/cause/physical replay and each engine's own future queues remain required. No executing singleton or numerical source changes occur; acceptance stays **9/52**.

Complete reviewed-case verifier preparation (2026-10-05):

- At clean `f5d1091`, prepare [the complete reviewed-case verifier](../../evidence/milestone-4/case-adjudication/reviewed-case-verifier.py) from the preserved automatic variable-horizon verifier and prior complete reviewed singleton proof. Bind the actual completed cause decision; validate the actual horizon, native complete repeats and cause descriptors, each engine's own eighteen future delivery sets, unchanged eleven gates and all nineteen independent metric fields. Score every event after the fork as well as the common prefix. Preserve the original automatic rejection/report and archive all original scientific artifacts before a separate parent decision.
- Ruff lint/import sorting, formatting and syntax checks pass. **Four actual process refusal controls pass** for a wrong reviewed cause, failed metric, budget failure and incomplete audit; none creates acceptance output. [Control record](../../evidence/milestone-4/case-adjudication/reviewed-verifier-controls.json). The separately recorded 461-test application pass remains the unchanged application regression. The new complete verifier has not yet been executed on a completed reviewed case; that positive qualification remains required.
- Commit this working verification tool immediately. The one-second run continues in its first CPU execution; no engine or executing source changes occur. Acceptance remains **9/52**. Milestones 0–3 are complete; Milestone 4 is in progress; Milestones 5–7 remain open. The 2026-10-05 morning planning estimate is approximately 40% of Milestone 4 work / 55% across all milestones, distinct from 9/52 accepted case identities. The first one-second pair takes 2,890 seconds through both paired executions; the observed CPU stream rate projects roughly 100–110 minutes for a full repeated one-second case. The remaining 122.2 biological seconds of prescribed singleton horizons imply roughly nine days of serial verification before batches, final profiling, reproduction and review. Budget 10–14 days of continuous execution provisionally; ten-second execution and final scientific outcomes are not yet measured.

Bounded qualification overlap decision (2026-10-05):

- At clean `786d334`, the existing sugar one-second session is confirmed live in `cpu-first`; all 52 recorded executed source hashes remain unchanged. The authorized process inspection shows the owned Python process at 950,960 KiB resident memory on this 32 GiB machine. Confidence **90%**: start the independent prescribed P9 one-second trial 0 while this CPU validation continues, with at most two owned full-network jobs. [Decision and evidence](../../evidence/milestone-4/parallel-execution/decision-20261005-01.json). Both executions retain their canonical stimuli, fresh repeats, one CPU thread per process and every original gate. This changes qualification scheduling only; overlapping elapsed times are excluded from later performance measurements.
- Commit this decision before launch. No source changes or new case acceptance occur; acceptance remains **9/52**.

One-second P9 qualification launch (2026-10-05):

- At clean `59cd9b6`, execute `MLX_ENABLE_TF32=0 UV_CACHE_DIR=/private/tmp/fly-brain-uv-remediation-cache uv run --locked --group qualification --no-sync fly-brain qualify-parity --experiment p9 --duration-s 1 --trial 0 --output data/results/milestone-4-parity-p9-10000-0-20261005-01`. Session `88326` is confirmed live in `paired-first`; its environment, canonical stimulus, reference job and all recorded sources match the launch/current checkpoint. [Launch binding](../../evidence/milestone-4/parallel-execution/p9-launch-20261005-01.json). The existing sugar session continues its CPU validation unchanged.
- Commit this verified launch record before further independent batch binding work. No new case acceptance is implied; acceptance remains **9/52**.

Saved batch stimulus boundary checkpoint (2026-10-05):

- At clean `cac5b4b`, add the qualification-owned [saved stimulus reader](../../../src/fly_brain/qualification/adapters/batch_stimulus.py). Strict Pydantic metadata, existing native uint8 event geometry/bits, archive/whole-trial hashes, exact step size, seed provenance, channel/rate order and provided input pins are required before returning an immutable stimulus. Preserve the existing writer/file format; perform no event or precision conversion. Independently read both actual one-second sugar/P9 saved inputs through this boundary.
- **475 application tests pass, zero failures/errors/skips**, including fourteen new real-file roundtrip/corruption tests for single/four-trial input, altered hashes, cast precision, noncanonical bits, omitted rows/trials, wrong input/channel metadata, invalid seed type, step size/version and extra arrays. [Final report](../../evidence/milestone-4/batch-verification/stimulus-tests-final.xml), [initial report](../../evidence/milestone-4/batch-verification/stimulus-tests.xml), and [verification/source/input hashes](../../evidence/milestone-4/batch-verification/stimulus-verification.json). Correct the initial unsupported float `Literal` annotation by typing the step size as float and requiring its exact value explicitly. All 171 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 116 files / 503 dependencies.
- Commit this passing state immediately. Canonical generation, neuron mapping, executed source/environment and accepted singleton-case binding remain required alongside actual one-second batches/repeats. Both full executions continue with their recorded sources unchanged; acceptance stays **9/52**.

Batch source and execution-settings checkpoint (2026-10-05):

- At clean `9c52433`, add the qualification-owned [environment/source binding](../../../src/fly_brain/qualification/adapters/batch_environment.py). Require complete strict saved metadata, fixed package versions/precision/compilation/CPU dtype and one CPU thread. Each recorded module must match current source and its actual launch bytes supplied by the composition root; require all numerical/observer modules. Compare hardware/Python/platform/CPU settings and all shared source hashes across four independently identified records. Additional batch-only sources remain individually bound. Keep the Git reader injected; no framework enters the domain.
- **488 application tests pass, zero failures/errors/skips**, including thirteen real-file/injected-launch checks for missing identities, changed versions/modes/threads/hardware, stale or missing numerical source, different launch bytes and additional individually bound sources. [Report](../../evidence/milestone-4/batch-verification/environment-tests.xml) and [verification/source hashes](../../evidence/milestone-4/batch-verification/environment-verification.json). A separate actual-Git compatibility control binds all 52 shared source hashes and execution settings across five existing environment records. Those different cases serve as environment controls only; their batch trial/input/case identity is not claimed. All 173 Python files pass Ruff formatting/linting; strict Pyright reports zero errors/warnings; three import contracts pass across 117 files / 508 dependencies.
- Commit this passing state immediately. Input pins/mapping, accepted exact singleton identity and actual one-second batch/repeat execution remain required. Sugar is in its fresh CPU repeat; P9 continues its first pair. No executing source changes occur; acceptance stays **9/52**.

One-second sugar timing failure and remediation handoff (2026-10-05):

- At clean `3b6290c`, independently score all three completed first-run native rasters while the CPU repeat continues. [All nineteen independently reproduced fields and eleven gates](../../evidence/milestone-4/one-second-sugar-metric-failure/first-metrics.json), [executed proof](../../evidence/milestone-4/one-second-sugar-metric-failure/executed-first-metrics.py), and [original native/mapped spike coordinates](../../evidence/milestone-4/one-second-sugar-metric-failure/first-native-spikes.npz) match their executed copies. Every captured source/current/launch hash and pinned input hash passes. The independent dynamic-program scorer reproduces the application exactly.
- **The timing floor fails:** MLX timing F1 **2966/3713 = 0.7988149744142203** against required **0.95**; 13,347 timing matches from 16,752 reference / 16,665 MLX spikes. The unchanged CPU baseline scores 0.3982965635535577. All other ten gates pass, including activity 409/413, count error 29/5584, neuron count error 347/16752 and correlation 0.9996497886766692. Better-than-CPU timing does not replace the absolute floor. The explained first fork cannot waive this failure; full case acceptance is blocked by this explicit fixed gate.
- Prepare [the bounded remediation review](../handoffs/astra-one-second-timing-remediation.md) for fresh-context Astra at explicit `xhigh`, asking for the smallest scientifically supported correction or diagnostic under unchanged model/reference/gates, including an honest assessment of the current float32 representation. Preserve and finish both currently live runs; launch no additional full cases and make no dependent numerical changes before the completed review is independently verified. Commit this complete failure evidence and handoff before dispatch. Acceptance stays **9/52**; all 52 cases remain required. The earlier 10–14-day planning estimate excludes this newly required remediation and must be reassessed after the supported remedy is known.

Timing remediation review dispatched (2026-10-05):

- At clean `1babf5c`, dispatch `/root/review_one_second_timing_remediation` with fresh context, explicit `gpt-6-astra` and `xhigh`. [Assignment binding and dispatch](../../evidence/milestone-4/one-second-sugar-metric-failure/dispatch.json). Its initial source inspection confirms the current two-stage float32 voltage rounding; it is evaluating bounded algebraically equivalent local host replays. That progress is not a completed recommendation or qualified remedy. Sol awaits the result and continues only independent evidence checks.
- Commit the dispatch now. Both live executions remain preserved; new full-case launches and dependent numerical implementation remain on hold. No acceptance criterion is relaxed; acceptance stays **9/52**.

Morning status reassessment after the timing failure (2026-10-05):

- At clean `7763b15`, Milestones 0–3 remain complete within their recorded scope; Milestone 4 is active and Milestones 5–7 are not started. Estimated engineering work completed remains approximately **40% of Milestone 4 / 55% overall**. These are planning judgments, not measured acceptance percentages. The measured count remains **9/52 accepted cases (17.3%)**, with 43 still required.
- The independently verified one-second sugar timing score is 0.7988149744142203 against the unchanged 0.95 floor. The fresh-context Astra `xhigh` remedy review remains active. Its local host calculations suggest a candidate arithmetic correction, but neither the recommendation nor a replacement full-case pass is complete. Preserve both live executions and the numerical-development hold pending the completed, independently verified review.
- Revised provisional planning range: **two to three weeks of continuous machine availability**, conditional on a supported correction passing qualification. The previously estimated roughly nine days of remaining serial singleton verification excludes remedy/requalification, actual batches, benchmarking, installation reproduction and final review. Ten-second executions remain unmeasured. An 85%-confidence completion date is not supported yet; this range is a conditional planning estimate and must be revised after the remedy and longer runs are qualified.
- The latest recorded application pass remains 488 tests with zero failures/errors/skips. The working tree is clean before this documentation-only checkpoint; no executing source, acceptance criterion or case disposition changes.

Completed timing review and prospective prototype decision (2026-10-05):

- At clean `2d0d8d7`, the assigned fresh-context Astra `xhigh` subagent completes its [bounded review](../../evidence/milestone-4/timing-remediation/astra-review.md). Sol inspects and independently executes the exact [host diagnostic](../../evidence/milestone-4/timing-remediation/executed-host-diagnostic.py); its complete output reproduces the reviewer result byte for byte. [Parent result](../../evidence/milestone-4/timing-remediation/parent-host-diagnostic.json) and [bound decision](../../evidence/milestone-4/timing-remediation/review-decision.json). No device qualification or full-network correction is inferred.
- Confidence **95%** in the next action: qualify the single-state float32 increment expression `v + (d*(v+52) + c*g)`, with `d` constructed by once-rounded host `expm1(-0.1/20)` and existing `b`/`c`. Record the prospective expression in the baseline before dependent implementation. The 206-update host replay repairs this local predicate and reduces its error to 0.0000014311366 millivolts; it does not prove a free-running case pass or eliminate the single-state precision limit. Require the complete native/scientific/scalar/layout/repeat/batch/observer/state/event/queue checks before adoption. Any adopted arithmetic needs its own complete 52-case qualification; do not transfer old accepted cases.
- The preserved sugar session `3625` finishes at 6,279.312 seconds (about 1 hour 45 minutes), exit 1, with `case_accepted=false`. Its original report explicitly retains the failed timing floor and scientific-review requirement. Independent archival verification of the terminal failed case remains next work. P9 session `88326` is still live. No executing source changes occur; no additional full cases launch. The old implementation retains its nine accepted cases; no replacement implementation has accepted cases yet.
- Commit this verified host-review and prospective decision immediately. The two-to-three-week estimate remains conditional on successful native/full-case qualification; the existing architectural and application checks are unchanged separate evidence.

Completed failed-case archival proof (2026-10-05):

- At clean `50840f3`, independently verify and preserve the terminal one-second sugar case, retaining `case_accepted=false`. [Complete failed-case proof](../../evidence/milestone-4/one-second-sugar-metric-failure/completed-case/verification.json) and [exact executed verifier](../../evidence/milestone-4/one-second-sugar-metric-failure/completed-case/executed-verification.py). The unchanged acceptance function explicitly refuses the failed timing floor. All nineteen metrics and eleven check results are reproduced by the bound independent scorer; explaining the first cause grants no exception.
- All native phase/state/spike/cause/final files, physical reference queues and CPU observations repeat exactly. Verify complete 313-block / 10,001 reference-queue / 10,001 CPU-snapshot coverage per execution, every original cause descriptor, canonical input/mapping/pins, all current/launch sources, and each engine's own eighteen future original-row delivery sets after the fork. The [archive](../../evidence/milestone-4/one-second-sugar-metric-failure/completed-case/observations.zip) contains all 26 original scientific artifacts, every member checked against its original bytes. Original raw data and standalone results remain intact.
- Commit this complete failure record immediately. Nine cases remain accepted for the original arithmetic; the proposed increment prototype has no accepted full cases. P9 remains preserved under its original source. Next action is isolated native prototype qualification; no production arithmetic or acceptance change occurs here.

Isolated native increment-prototype checkpoint (2026-10-05):

- At clean `c88300b`, execute the reviewed increment prototype on actual Metal with precision zero and compilation disabled, without changing production or P9 source. [First result](../../evidence/milestone-4/timing-remediation/native-local/first-result.json), [separate fresh-process repeat](../../evidence/milestone-4/timing-remediation/native-local/repeat-result.json), [exact executed prototype](../../evidence/milestone-4/timing-remediation/native-local/executed-prototype.py) and [array/source verification](../../evidence/milestone-4/timing-remediation/native-local/verification.json). All 39 native arrays retain identical dtype, shape and bytes across processes. Preserve the full 227-step / 206-update original/candidate/candidate-repeat local phases and all-neuron one-step values/predicates.
- The original function exactly reproduces the saved cause; the candidate matches the reviewed host voltage, spikes at step 5,719 and resets correctly, with reference error 0.0000014311366 millivolts. The all-neuron voltage calculation matches the host exactly. Applying the change only to the already-drifted preceding state retains the same different predicate, as predicted; no free-running network result is inferred.
- Preserve the initial failed extra host-synaptic byte assertion and its [diagnostic](../../evidence/milestone-4/timing-remediation/native-local/synaptic-underflow-inspection.json). Thirty-seven host subnormal products differ from device signed zero by at most 1.17477e-38 millivolts. Candidate synaptic bytes match both the unchanged native core and the original recorded state exactly. Correct this additional host check to require those native invariants and explicitly record underflow; change no model, device calculation or approved tolerance.
- Commit this verified native unit immediately. The complete unchanged scientific/scalar/layout suite, observer/repeat/batch/queue checks and prospective adoption decision remain required. P9 is live in its original CPU validation. New full cases remain on hold; acceptance stays nine cases for the original implementation and zero for the prototype.

## Milestone 5 — Complete-brain benchmark and profiling

Status: not started.

Acceptance: the full pinned dataset completes within local memory, preserves approved parity, and has measured load time, first-run compilation, warm simulation, timesteps per second, biological-time/wall-time ratio, peak unified memory, synchronization, and collection overhead.

Profile before optimizing. Candidate experiments include edge-list gather/multiply/scatter-add, `mx.compile`, destination-sorted reduction, active-neuron propagation, and batched independent trials. Sol may perform measured local optimizations that preserve the approved update structure. Sparse representation changes, scientific-operation fusion, update-order changes, and custom Metal kernels require a bounded Astra handoff with regressions defined first. Preserve the correct baseline as an oracle and reject optimizations without material measured improvement.

## Milestone 6 — Reproducibility and upstream preparation

Status: not started.

Acceptance: pinned dependencies, Apple-silicon installation instructions, example commands, benchmark methodology, numerical tolerances, known limitations, licence notices, and focused tests are complete. Execute the documented clean-install/test workflow and prepare a focused upstream-reviewable patch.

Obtain a bounded final Astra scientific review covering contract compliance, test adequacy, claims, benchmark validity, CPU fallback, hidden semantic changes, and the distinction between exact and statistical parity. Sol verifies the returned evidence and applies any precise requested corrections before finalization.

## Milestone 7 — Finalization

Status: not started.

Acceptance: final corrections are applied; the complete approved verification suite has run with no silent skips; all completion requirements above have direct recorded evidence; commits and working tree are understood; and numerical/performance conclusions accurately state their limits. Prepare the final upstream handoff.

## Current checkpoint and constraints

Milestone 2 completion checkpoint: `fe5f269` on `main`. Milestone 3 implementation is committed at `c863ed8`; its two complete normal-installation sugar runs and complete silent control close integration, with independently verified file/output-tool checks above. Sugar repeat evidence is committed at `ee6bd37`. Checkpoint `e766ea2` requires each verified step to be committed before the next begins. The architecture hold was released at `d834713`; the independently verified manual accumulation-design handoff was integrated at `8b7fdb7`.

Milestones 1–3 are complete within their recorded envelopes. All 24,576 prescribed cases pass through the actual layout under the [recorded input-state accounting decision](../../evidence/milestone-2/initial-state-cast/astra-review.md#recorded-engineering-decision). All 99 original-state one-step conversion limitations remain visible; original-state trajectory gates pass. Complete device fields/events and controlled original/silenced full-network pulses pass. Two complete sugar outputs repeat byte for byte; the complete silent control has zero events; existing comparison tools consume both. Next work is Milestone 4's full-network scientific comparison and causal audit. Later milestones remain open.

The latest default application run passes **488 tests**, zero failures/errors/skips; the complete scientific suite records **203 passed tests**, zero failures/errors/skips, including 41 CPU setup/observer checks. These are separate suites. The internal batch collector additionally passes 13 focused real Metal observer/collector tests, zero failures/errors/skips, with all quality checks recorded. Ruff, strict Pyright, and all three import contracts pass. Complete shortest reference/MLX/CPU transparency and raw replay, actual queue/due agreement, live causal auditing, and sampled single/four-trial concurrent memory are verified. **Nine three-engine cases are accepted (9/52)**: all five sugar trials at 0.1 seconds, plus P9, silenced sugar, two-class, and silent trial 0 at that horizon. Eight accepted rasters match MLX/reference exactly; sugar trial 1 has a separately verified parent acceptance under the prospective explained-roundoff rule. Every fixed/paired metric and complete causal/native replay requirement passes. The silent control independently matches all 19 frozen empty-metric fields. Batch trial 1's first difference has a verified bounded roundoff classification. Reviewed pure group coverage/calculations/bin composition passes focused intent checks; recorded partial reports preserve missing identities and independently reproduce pooled metrics within actual trial boundaries. Complete matrix reports remain open. The remaining 43 cases, prescribed full repeat/batch gates, full parity approval, and benchmark speed remain open. Existing data, results, and standalone artifacts are preserved. New runs require a fresh output directory. Engineering choices remain delegated to Sol; use bounded Astra review where deeper numerical judgment is needed.

Delegation setup (2026-10-04): [the versioned bounded subagent skill](../../../skills/bounded-subagent/SKILL.md) is installed through a symlink at `~/.codex/skills/bounded-subagent`, with automatic discovery enabled. At the user's request, model and reasoning effort are resolved from user instructions or project rules rather than fixed in the reusable skill. The bundled `quick_validate.py` passed; the installed link, file contents, and parsed interface metadata were verified. A read-only `gpt-6-astra` subagent at explicit `xhigh` completed the workflow review and four hypothetical dispatch checks: an explicit Sol/high pair, the project's Astra/xhigh pair, missing choices without defaults, and explicitly requested inheritance. It found no material defects. These were instruction/tool-contract checks, not four live dispatches. At that setup checkpoint, Sol retained the user's selected `max`; the updated goal now requests `xhigh`. The existing manual assignment and scientific evidence retained their owner. This setup did not start Milestone 2 or run additional numerical checks.

Git remote `upstream` is the public reference repository. No user-owned push destination has been supplied; local commits have not been pushed. Do not assume permission or write access to the upstream repository.

## Refactor and enforcement checkpoint 2026-10-06

Archived from the active milestone at `f2de8f01a2e5311a94ac4e520572925d23ce6f78`. These statements retain
their original checkpoints, including completed imperatives and superseded
status. Current instructions and progress remain in the root milestone.

- Quality tooling and the shared commit/push hooks are installed. At `b932298`,
  the standalone metric engine has **17 source-only passes**, zero failures,
  errors, or skips. [Report](../../evidence/code-quality/metric-intent-tests.xml).
  At `003ac89`, **29 quality tests** pass with zero failures, errors, or skips,
  including 12 controlled hook checks for child failures, missing tools,
  unchanged boundary debt, staged defects, and actual push rejection.
  [Report](../../evidence/code-quality/hook-intent-tests.xml). Apple-silicon
  [continuous integration](../../../.github/workflows/quality.yml) is configured at
  `c053f05`. At `1376e40`, [hosted run 37328288754](https://github.com/PraxisMechanica/fly-brain-mlx/actions/runs/37328288754)
  passes every step and uploads both [metric reports](https://github.com/PraxisMechanica/fly-brain-mlx/tree/edfbb9dcfb477bf788740ca9096165518d21231a/docs/evidence/code-quality/ci-1376e40).
  The first hosted run passed its checks but excluded hidden evidence paths;
  the corrected uploader preserves the two reports. Their nine comparisons
  pass, covering 232 files / 25,207 nonblank lines, average/max complexity
  5.37 / 28 and health/maintainability 69.05 / 69.05. Five additional real import
  fixtures reject aliases, type-only imports, indirect paths and re-exports;
  weakening transitive enforcement stops detecting the indirect defect.
  Eight index-guard fixtures reject untracked/ignored source and typing stubs,
  accept staging repairs and non-source evidence, and prove that disabling the
  guard hides the defect. They use real source-only Git repositories; the
  pipeline probe controls only the downstream metric exit.
  The shared check now passes **49 quality tests**, zero failures/errors/skips;
  formatting, lint, strict typing, all three import contracts, and staged/full
  commit metric checks pass. [Test report](../../evidence/code-quality/index-intent-tests.xml).
  [Recorded coverage limits and definite clock finding](https://github.com/PraxisMechanica/fly-brain-mlx/blob/edfbb9dcfb477bf788740ca9096165518d21231a/docs/agent/quality-coverage.md):
  the full 37-rule architecture result is **ANALYSIS FAILED (COV002)**.
  Keep feature/numerical work held while that required enforcement is incomplete.
- The user approved native GitHub stacking on 2026-10-06. Stack #7 merged
  into `main`: [local checks](https://github.com/PraxisMechanica/fly-brain-mlx/pull/5),
  [hosted checks](https://github.com/PraxisMechanica/fly-brain-mlx/pull/6), and
  [boundary coverage](https://github.com/PraxisMechanica/fly-brain-mlx/pull/8).
  The merged head is `5efda389aabf5fa46b176dffb7fef6c69572685d`.
  Original PRs 1–4 are closed; all original refs, incoming work, and evidence
  remain preserved. Bulk metric dumps are excluded from the review diffs.
- The latest 2026-10-06 instruction requests direct commits when the commit
  and push hooks can run the checks. Deliver the authorized refactor/cleanup
  changes directly to `main` with both hooks. Confidence in this delivery choice
  is 99% at `5efda389aabf5fa46b176dffb7fef6c69572685d`. The earlier proposed fourth PR
  is superseded. PR cleanup no longer requires waiting for the merged layers.
- The complete structural analyzer is still missing, so feature/numerical work
  remains held. The latest user amendment on 2026-10-06 releases the hosted-cache
  approval hold through the non-production authorization in `AGENTS.md`.
  Repository variable `QUALITY_CI_TEMP_DB_CACHE_APPROVED` is now verified true;
  hosted run 37468037333 passed every job step at
  `68bc087a56884cf0cff4f62c956806bec228cbad`. Its saved staged and actual-commit
  metric reports both pass. This proves the configured gate at that revision;
  it does not complete the structural catalog. Prior skips are not passes.
  Local checks preserve their cache outside fixture cleanup. All three
  reconstructed layers passed their
  native commit/push hooks.

- Quality work resumed at `876cb157b403c6e65d96aa3d411ae8686988cf06` under the
  user's instruction to continue and deliver through local hooks. Confidence in
  this scope is 95%. The first repair injects the same typed timing clock into
  the simulation service and result writer through bootstrap. Eleven focused
  tests and strict typing pass; the ambient-clock control is rejected. Numerical
  backend sources, spike schema, and report fields are unchanged. Test artifacts
  are retained. Full checker coverage remains incomplete; scientific/performance
  implementation is still held.

- At `23dac175679b8cbc6b102c4ecc143e9a85a34487`, the clock repair is committed
  and pushed with both configured hooks passing. The full source inventory
  contains 238 Python/stub files, including 60 retained evidence-source records.
  The bounded qualification-boundary reviewer used fresh `gpt-6-astra` at `xhigh`
  and returned a 94%-confidence prospective decision. Parent source inspection
  confirms its findings: retain qualification-owned independent expectations,
  expose neutral actual native observations through narrow ports, and replace
  private layout/closure introspection. The accepted review is recorded at
  `docs/evidence/code-quality/qualification-boundary-20261006/astra-review.md`.
  Start with the actual reduction-row capability; preserve core/ledger scheduling
  and validate native bytes/ownership. A rewritten observer or ledger requires
  the fresh transparency/integrity and complete-shortest-run proof in that review.
  No new scientific case acceptance or arithmetic mode is approved.

- The first boundary slice replaces private `partial.args[1]` layout recovery
  with a qualification-owned typed actual-row reader. Neutral host observations
  now live outside the concrete backend; row arrays preserve native bits in
  immutable detached storage. The bound reduction descriptor reports the actual
  exact-count guard/fallback choice. Eighteen native/value tests, seven real
  paired/repeat/batch/singleton tests, and five source-only graph/hook tests pass
  with no failures or skips. Four direct real-device comparisons reproduce all
  96 old-reader arrays' dtype, shape, and bytes. Full typing and lint pass.
  The core, reducer, and ledger files are byte-unchanged; existing layout,
  accumulation, advance, and original preparation statements are preserved.
  Fresh test outputs and `row-verification.json` in the boundary evidence folder
  retain the proof and initial sandbox/caller failures. No full pinned-network
  case was rerun, and no acceptance transferred. Remaining concrete execution,
  state, and observation-policy dependencies still need the complete port slice.

- At `68bc087a56884cf0cff4f62c956806bec228cbad`, finish the analyzer's Python
  declaration-inventory and native Pyright resolver foundations. Forty-one
  source-only fixtures pass with no failures/errors/skips; strict typing,
  formatting, and lint pass. Actual aliased/re-exported/type-only protocol calls
  resolve to their defining method. Coverage/framing/resolution weakening loses
  detection of the same defects. Discovery parses 249 Python/stub files and
  3,332 named declarations across the six explicit roots, including all sixty
  retained evidence-source files. The compact component proof is recorded at
  `docs/evidence/code-quality/architecture-foundations-20261006/verification.json`.
  These are foundations, not complete symbol/role/resource/effect classification
  or whole-application enforcement. The 37-rule result remains COV002.

- At `0a313d02b56d886542d130134346506106a5f926`, the analyzer foundations are
  committed and pushed with both native hooks passing. Hosted run 37471806648
  completes every job step successfully. Its scope is the configured gate,
  not complete structural enforcement.
- Separate pure comparison scoring/result construction from reader orchestration.
  The four scoring function ASTs, result body, and first-read/prepare ordering
  remain unchanged. All 81 original/new serialized fixture pairs match; the
  shared-buffer regression detects an intentionally reordered reader control.
  Seventy-nine focused application/file/CLI cases and six source-only hook cases
  pass with no failures/errors/skips. A fourth import contract rejects direct,
  aliased, type-only, transitive, and re-exported rule-to-service dependencies;
  weakening scope/transitive enforcement loses detection. Strict typing,
  formatting, lint, and all four import contracts pass. Numerical backend,
  qualification adapters, scientific contract, and data remain unchanged.
  Compact proof: `docs/evidence/code-quality/comparison-rules-20261006/verification.json`.
  No case acceptance transfers; the full structural result remains COV002.

- Both the comparison repair `aaafbf60522e30f4ec2bd8d5ab098d12148b1297` and
  parallel assignment record `f0d8116d0e0bd640a78ce918d273fe931e583647` are pushed
  with native hooks passing. Hosted runs 37479774365 and 37480391382 succeed.
- Three new source-only metric controls pass. They measure a real staged source
  regression, individually reverse CQ001/CQ002/CQ003 in an isolated comparator
  copy, and prove the corresponding diagnostic disappears from the unchanged
  native snapshots. Equal/repaired source passes. The installed analyzer stays
  unchanged; other rules still reject the shared regression. Health and
  maintainability remain the same heuristic, not independent architecture proof.
  Compact evidence: `docs/evidence/code-quality/metric-weakening-20261006/verification.json`.

- Integrate the composition worker `05dd2202b99a8a5d97acc3119176e92769326dd2`
  against parent `db6be047c7cab56b4be7295b6ac78af50add0f63`. Bootstrap now only
  assembles typed owned commands; domain services execute workflows. All 150
  combined behavior/file/CLI/boundary cases pass with no failures/errors/skips.
  Source and raw-record hashes plus three preserved function ASTs are verified.
  Four new source scopes reject concrete dependencies and prove scope weakening.
  The initial duplicate-entry test assertion is repaired; evidence and outputs
  remain preserved. Compact proof:
  `docs/evidence/code-quality/composition-refactor-20261006/parent-integration.json`.
  No numerical, observer/ledger, reference or output-schema source changes and
  no new scientific case acceptance; full structural coverage remains COV002.

- Composition integration is pushed as `471ab69` with both native hooks
  passing. Previous main revision `db6be047c7cab56b4be7295b6ac78af50add0f63`
  also passes every step of hosted run 37483019029. Integrate the committed native
  semantic/graph component `ffbc2fec0db074754d3f457ac78a52728b4282bd` against
  that composition revision: all eight source hashes match and 84 parent source
  fixtures pass without failures/errors/skips. The resolver records native
  declaration identities, nominal class locations and explicit lexical targets;
  transitive paths and cycle witnesses retain exact source evidence. Missing
  structured types, alias ownership, control flow, implicit/runtime dispatch and
  effects still fail COV002. The native-types follow-up and independent opaque
  qualification-session slice have explicit separate ownership in the assignment
  record. Compact proof:
  `docs/evidence/code-quality/architecture-symbols-20261006/parent-integration.json`.

- Native resolver integration is pushed as `a9453aa` with both native hooks
  passing; composition revision `471ab69` passes hosted run 37506222834. Integrate
  ownership worker `d6e8d43d8cd756d1a7d260bffd419da0ab1bd449` against that combined
  source. Thirty-five exact changed/new files are reviewed and reconciled:
  274 files, 3,770 declaration occurrences and 198 neutral exports; all 62 frozen
  historical/reference provenance records are preserved. Reconciliation has
  zero gaps. Only the proved bootstrap/comparison mixed-role findings are removed;
  thirteen other recorded findings remain. Seventy-six parent policy/index cases
  pass without failures/errors/skips. The canonical policy now requires indexing;
  omitting its exact input loses detection, while nearby measurement JSON stays
  allowed. Compact proof:
  `docs/evidence/code-quality/architecture-ownership-20261006/parent-integration.json`.
  The first parent hook passes 219 quality cases but rejects a test-file
  complexity regression; typed literal helpers repair it without rule changes.
  Complete structural enforcement remains COV002; the live registry fixture is
  reconciliation evidence, not an application-compliance certificate.

- Ownership registry integration is pushed as
  `c5296da3fd66ff3d48348a919bd1a44e5b01b496` with both full native hooks passing.
  Review `3613b96dac3c6c9bcc411301de3f828d25846839` resolves the two actual runtime
  parents after 95 source hashes and the current registry/scheduling record are
  verified. Native execution/state are simulation-run children; reference
  builds/fresh processes are qualification-case children. The two attribution
  uncertainties are cleared; eleven other recorded findings remain. Sixty-seven
  parent policy cases pass. Initial prose count and old live-registry expectation
  are corrected without app/scientific source changes. Reference and remaining
  probe repairs wait for the assigned session contract; native reducer probes
  retain their separate consumer boundaries. Compact proof:
  `docs/evidence/code-quality/resource-ownership-review-20261006/parent-integration.json`.
  The first parent hook rejects a small health regression after 219 source
  cases pass; separate runtime-parent cases preserve all checks and repair it.
  Full rule/alias/effect/control-flow and historical resolution remain COV002.

### Earlier documentation checkpoints

## Documentation checkpoint

At `710a267`, centralize twelve agent documents and preserve their original text
apart from link rebasing and historical notices. During that edit, incoming
quality work commits `aebad54`, `b932298`, and `003ac89` remain preserved on their assigned
branch. The first documentation push is blocked by then-unindexed incoming test
files; the owner subsequently commits them. No hook is bypassed.

The reconstructed documentation layer separates the human README, active plan,
scientific contract, developer workflow, and dated history. Source checkpoint
`5efda389aabf5fa46b176dffb7fef6c69572685d`; confidence in this scope is 98%.
Current preservation checks cover twenty authored documents and 738 local
links/anchors with zero errors. Linked local contents and 43 exact external
destinations were opened and reviewed; historical citations retain their scope. Complete milestone/reference history, twenty
scientific table rows, 87 numeric inline expressions, and the coefficient code
block remain unchanged. All 831 original versioned data/evidence files retain
their identity and working contents. Native commit/push checks are required
before delivery. The former hosted-cache approval hold is released by the latest
user amendment; hosted verification results retain the revision scope above.

[Original documentation verification](https://github.com/PraxisMechanica/fly-brain-mlx/blob/edfbb9dcfb477bf788740ca9096165518d21231a/docs/evidence/documentation/organization-20261005/verification.json)
records the earlier 755-link check, fourteen parsed command examples, successful
help/task-list checks, and required hook pass at `a47cb1b`. Those results retain
their original checkpoint scope. The initial broken README anchor was repaired;
the CLI help check used a task cache after a sandbox cache error. No installation
or simulation was needed. Application/scientific suites were not rerun for this
documentation-only reapplication.


### Typed observation storage correction — 2026-10-06

Worker `a58be25e17edf9e800edd85692db46adfcce783f` replaces dynamic
attribute interception/type-shadowed arrays with truthful private snapshots and
36 typed properties across nine frozen records. Parent integration at `54aea507`
verifies eight source/test hashes, all 43 raw artifact hashes and the actual
committing-hook result. Fresh parent checks pass 106 native Metal cases (27
upstream warnings) and 66 value/alias/package/canonical-port cases with no
failures/errors/skips. Independent source/value probes preserve 108 other source
files, nine constructor signatures, 55 public values, 31 native dtype guard
outcomes, ten pure/snapshot/digest bodies and all 30 prior fixture assertion
ASTs. The initial review script incorrectly expected a qualification-only owner
for the Metal fault fixture; its existing system-test owner is preserved.

Exact metadata reconciles 289 files, 3,989 declaration occurrences and 266
neutral exports with zero gaps, retaining all 62 frozen provenance records and
eleven recorded findings. Compact evidence is
`docs/evidence/code-quality/session-storage-transparency-20261006/parent-integration.json`.
Array-facing dataclass reflection now exposes actual snapshots; no production
consumer uses the former representation. Legacy collectors remain active.
Complete pinned transparency/four-trial transient-memory proof, caller migration
and full 37-rule enforcement remain required; no new scientific acceptance.


### Seeded acquisition boundary — 2026-10-06

Worker `b8d490a35b75d7b4fea9f8799a7554bae1888e49` separates fresh NumPy
SeedSequence/PCG64 acquisition from explicit-input stimulus/mask/fan-in rules.
Required typed consumers and live assembly/callers move together. Parent at
`3f62a6a` verifies all 29 source hashes, 11 raw result hashes, 54 old/new full
records and the exact 29-row policy delta while preserving typed storage.
Fresh checks pass 144 focused cases and 26 native effect/canonical source-hook
cases with no failures/errors/skips. The full pinned 138,639-neuron identity
and four-trial, 1,000-step sugar event schedule preserve native bytes and
metadata, hash `444385040e153d7666e83f345707d998e22b541a39fa753d87d1a6e94f5705c2`.
An initial summary probe used nonexistent Stimulus.trials; corrected to actual
trial_indices and reran all event/metadata/artifact checks. No device run was
needed. Exact metadata covers 299 files, 4,078 declaration occurrences and
278 neutral exports with zero gaps, preserving 62 frozen records. Only the
three proved STATE001 findings are cleared; eight other findings and COV002
remain. Compact proof:
`docs/evidence/code-quality/seeded-input-boundary-20261006/parent-integration.json`.

The existing purity owner now receives the immutable CausalAudit transition,
all live paired/capture folds and only required fixture changes. Native-type
source remains rejected by its metric gate; its verified candidate is retained.
The metric review establishes Python aggregation undercount without granting
the bridge a pass; a separately assigned correction preserves the original
archive, other languages and all regression predicates. Pinned session
qualification runs independently; no collector activation or new acceptance.


### Immutable causal audit transition — 2026-10-06

Worker `42d94b0e8f78aca7f0b21d8a2c3ea33b525b0e2d` turns the four-field
audit into a frozen value and pure advance_audit transition, with every live
paired/capture fold rebound before context selection. Parent at `fe61472`
verifies eight source hashes and nine raw result hashes, 576 successful
original/new prefixes, three capture blocks and 37 original assertion ASTs.
Fresh parent checks pass 86 CPU and 24 real paired-observer cases (90 upstream
warnings), no failures/errors/skips. The first CPU collection used the original
editable path because environment overrides ended at the preceding policy
command; rerun explicitly targets worktree source and fresh outputs.

Step/finiteness precedence, pre/before/end and v/g ordering, exact strict budget,
first-neuron/fork latching and subsequent finite checks remain. Failed pure
steps/blocks return no value and publish no partial audit/context; old malformed
input partial mutation is separately demonstrated and explicitly retired.
Exact eight-row policy integration reconciles 300 files, 4,109 declarations and
278 neutral exports with zero gaps; only STATE002 is cleared. Seven findings
and complete37-rule COV002 remain. Compact proof:
`docs/evidence/code-quality/immutable-audit-transition-20261006/parent-integration.json`.
No numerical mode, backend/reference/queue/ledger/provider/RNG/serialization or
scientific acceptance changes. Identifier boundary review remains read-only;
collector migration waits for complete committed pinned preservation evidence.


### Python whole-file metric correction — 2026-10-06

Worker `88c6eaa2e8a22db51396393b263d61f20de81870` corrects the documented
whole-file Radon aggregation, changing only Python algorithm/cache identity and
package version to 0.1.1. Original package archive/reports and shared runtime
remain unchanged. The exact authored patch reconstructs all 20 installed files;
36 native dependency version pairs and lock resolutions remain equal. A fresh
frozen offline runtime install reuses 37 packages with zero downloads.

Parent at `e9c62fd` verifies eight committed input hashes, all 20 archive/runtime
files and original 20 shared runtime files. Only its own dependency link moves
to the independently verified runtime. The first application failed atomically
because a text diff omitted binary archive data; the corrected full-index/binary
patch is applied and verified. Exact policy merge adds two quality fixture rows
and updates the canonical input guards. Parent tests pass 85 cases with no
failures/errors/skips; same qualified analyzer on both staged sides passes
mean/max 20.93/129 to 20.89/129 and health/maintainability 35.62 to 35.64.
Missing/ignored provenance, both archives and patch reject until staged; each
individual weakening loses its diagnostic. No baseline/threshold/source-padding
change. Worker initial health rejection and genuine preservation of both archive
SHA checks within one provenance invariant stay recorded. Full structural
coverage remains COV002 with seven recorded findings, and no bridge/scientific
acceptance is granted. Compact proof:
`docs/evidence/code-quality/python-metric-aggregation-20261006/parent-integration.json`.


### Complete pinned observation preservation — 2026-10-07

Worker `c11065cf827946923976726a47814f32d0bb75f2` completes all five pinned
1,000-step modes at a58be25e: ordinary, legacy, session, fresh repeat and actual
four-trial session. Parent at e923c31 verifies all485 raw hashes/lengths and
three committed file hashes, all seven pytest reports,180,000 independent
checks and5,664 native array comparisons. Full source/instrumentation identities
stay retained. Parent updates only the proof regeneration API to current
schedule with explicit uniforms; all30 assertion ASTs stay exact.

First parent controls pass9 then fail on missing fresh artifact parent, corrected
without source changes. Corrected whole-file metric rejects combined helper/test;
separation by proof value, artifact/memory recorder, native mode, orchestration
and test responsibilities preserves all24 top-level class/function ASTs and
all30 assertions. Missing hashlib and unmerged import group during extraction
are fixed before verification. Parent separated controls pass10 (27 upstream
warnings), pure retained comparer repeats all5,664 arrays, and strict Pyright
has no errors/warnings. Original bulk arrays/source copies remain untouched.

Measured four-trial MLX used peak5,009,460,504bytes and sampled simultaneous
active+cache max9,512,195,175bytes are separate from traced host/RSS counters.
Full-block active+cache varies only168,352bytes; no summed/instantaneous/universal
capacity claim. Exact policy covers309 source files/4,209 declarations with
zero gaps and seven recorded findings. Proof:
`docs/evidence/code-quality/qualification-session-pinned-20261006/parent-integration.json`.
No production activation/scientific acceptance; caller migration stays with
its existing owner, including required test-only historical oracle and actual
source-identity updates. Complete37-rule analysis still fails COV002.
