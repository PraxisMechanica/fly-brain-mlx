# Bounded one-second timing remediation review

Reviewer: `/root/review_one_second_timing_remediation`, GPT-6 Astra at explicit `xhigh`. Assignment checkpoint: `1babf5c49443cb8b56f79eae24c866f811e1292d`, main. Project review is read-only. Sol retains implementation ownership. No device/full-network execution, project edits, Git mutation, network calls, nested delegation, or changes to the two live runs occurred.

**Recommendation: qualify one small single-state float32 prototype that evaluates the same coupled voltage solution in increment form. Do not declare a repaired case or launch another full case from this review alone.** Confidence is **95%** that this is the smallest scientifically supported next action. Whether it can pass every fixed timing gate, especially at ten seconds, is unresolved.

For each available neuron, using the old `v` and old `g`, evaluate these separate float32 operations with compilation disabled:

```text
d = float32(expm1(-0.1 / 20))      # host float64 construction, one cast
v_next = v + (d * (v + 52) + c * g)
g_next = b * g
```

Here `d = -0.004987520631402731`, and `b = 0.9801986813545227` and `c = 0.004937935154885054` retain their current values. Do not calculate `d` as `float32(a_float32 - 1)`: that gives `-0.004987537860870361` and preserves the existing coefficient error. All gating, strict threshold, reset, recurrent accumulation, stimulus, clocks, and queues stay as specified. This is the exact coupled linear solution expressed differently, not an Euler step: `d=exp(-h/20)-1`, `c=(a-b)/3`, and the voltage uses old `g`.

This recommendation selects a **bounded prototype**, not a qualified production replacement. It adds no state array, changes no public application programming interface or database schema, and does not require persistent compensation. Record the new implementation expression and coefficient prospectively in the numerical contract, under the user's delegated engineering authority, before dependent implementation. The analytical model and every acceptance number remain unchanged.

## Recorded failure and drift

The saved native spike archive has SHA-256 `6bb67da558892f81eb759596072bb06515a4987aadb9ff65bf05181143d55d5e`. The host diagnostic checks that hash, the first-cause archive hash, all 112 native cause array descriptors, the completed review's host-proof/source hashes, and the exact reference clock. It reads the original coordinates, without output conversion or a new simulation.

I reproduce 13,347 ten-step matches, 12,323 exact matches, and 12,592 one-step matches. Thus timing F1 is still `2966/3713 = 0.7988149744142203`. With unchanged total counts, at least 2,527 additional matches would be required to reach 0.95. The failure is not a one-spike accounting discrepancy.

The first affected neuron's recorded event moves from reference step 5,719 to MLX step 5,720. The next neurons with different exact event sets first differ at 5,748, 5,763, 5,773, 5,784, 5,799, and 5,809. In all, 368 neurons have different exact step sets. Every event can still be matched within ten steps in the first six 100-millisecond bins. The four later bin-local timing F1 values are approximately 0.78705, 0.41178, 0.39065, and 0.35440. These bin-local scores are diagnostic only; they exclude cross-bin matches and are not replacements for the whole-case score. The script separately records globally matched events by reference bin, including the two boundary-crossing differences.

From step 5,719 onward, the saved rasters have 7,029 reference and 6,942 MLX events, with 3,624 matches: F1 is 0.5187889199055186. This progression is consistent with amplification after the already explained finite-precision fork. It is not a fixed timestamp shift. A raster cannot prove that every later difference has this one cause; this review does not independently classify every later event or discard any post-fork score. The existing own-engine finite/event/queue ledgers and repeats remain required.

## Arithmetic evidence

Current `src/fly_brain/simulation/backend/core.py:137` evaluates `(-52 + a*(v+52)) + c*g` and stores a single float32 value each step. This introduces two additions at the absolute voltage scale. The stored `a` differs from the analytical value by `-1.7053552681112194e-8`; the proposed `d` differs from its analytical value by `+1.7591495534569068e-10`. The increment form reduces that absolute coefficient error by about 97 times, forms the small increment first, and performs one final addition to the absolute voltage. It does not remove final state rounding or the existing `b`/`c` errors.

I use the completed review's exact 29 delivery records, native weights and actual 256 count leaves to compare five predetermined arithmetic methods from the common step-5,492 reset to step 5,719. This is a 206-update, one-neuron incoming-event replay, not closed-loop network prediction. All variants have no earlier spike; the original and generated reference reproduce their saved native values exactly at both 5,718 and 5,719. The two variants labeled `host_diagnostic_*` evaluate the voltage expression in host float64 and round once solely to isolate error sources; they are not proposed implementations or hidden CPU fallback.

| Voltage evaluation | Step-5,719 voltage, millivolts | Error against native reference, millivolts | Largest local voltage error, millivolts | Actual strict predicate |
| --- | ---: | ---: | ---: | --- |
| Current expression | -45.0 | -4.053053332597756e-5 | 4.35863434518069e-5 | false |
| Only regroup `-52 + (a*(v+52)+c*g)` | -44.99997329711914 | -1.3827652466602558e-5 | 2.2237613023889935e-5 | true |
| Proposed increment form | -44.99995803833008 | +1.431136595897442e-6 | 1.4608218492639935e-5 | true |
| Single rounding with stored coefficients, host diagnostic | -44.99997329711914 | -1.3827652466602558e-5 | 1.8422915758264935e-5 | true |
| Single rounding with unrounded coefficients, host diagnostic | -44.99995803833008 | +1.431136595897442e-6 | 1.4608218492639935e-5 | true |

Every variant keeps the same synaptic trajectory in this replay; its maximum error remains `7.4177575157818865e-6` millivolts. A one-step substitution into the actual already-drifted step-5,718 state does not fix the first predicate for **any** tested variant. The gain requires executing the candidate from fresh state; no boundary patch, saved-state substitution, reference mask, or late correction is justified.

An independent 25-state, threshold-disabled, 10,000-step host grid uses the Cartesian product of initial voltages `[-256,-52,-45,0,256]` and synaptic values `[-1024,-100,0,100,1024]`. Maximum voltage error is `0.0006913478480328195` millivolts for the current and merely regrouped forms, versus `0.00038146972585195726` for the increment form. This extra grid reaches about 353.206 millivolts, so it is explicitly an additional host diagnostic outside part of the ordinary envelope, not a native qualification pass. The maximum error divided by the unchanged trajectory budget is about 0.44022, 0.45101, and 0.25097 respectively.

The exact six initial states from `tests/qualification/test_mlx_core.py:47` are also evaluated against the generated native reference expression on the host. All methods retain the same limiting maximum voltage error, `0.00038146972623565034` millivolts, and synaptic error, `0.00021828870384865695`. The candidate's maximum budget fraction is 0.25096692515503255. This demonstrates the remaining single-state rounding limit rather than claiming that the new expression eliminates it. No native test or scientific suite was run by this reviewer.

## Single-state limit and possible later representation work

Binary32 stores 24 significant binary digits. Its spacing at -45 millivolts is `2^-18 = 3.814697265625e-6` millivolts; half-spacing is `1.9073486328125e-6`. The unchanged quarter-unit-in-the-last-place counterexample still maps a positive reference margin to exact equality. Local accumulation error and rounding amplified by the leak can also reach roughly `0.000382` millivolts. Fused operations, regrouping, or a better coefficient cannot retain information discarded by every persistent state write. Synaptic state still has its own float32 decay and final accumulation rounding. Therefore no single-state expression provides universal float64 threshold equivalence.

That impossibility is **not** evidence that the fixed 52-case statistical requirements are impossible. The supported small candidate should be qualified before introducing more state or broad observer changes. Conversely, the one-neuron result does not establish that the remaining cases, or even a fresh whole sugar second, pass. Do not tune successive expressions against failed case scores. If the qualified candidate later misses another fixed timing floor, retain the failure and request a new bounded assessment using its own first-cause data.

A technically plausible escalation would retain normalized high/low float32 components for **both** voltage and synaptic state and use error-compensated sums/products plus split coefficients. This is approximately 48 significant binary digits in a qualified normal-range algorithm, not IEEE binary64's 53 bits, not double precision merely because two arrays are present, and not an automatic error bound through arbitrary cancellation/underflow/overflow. The exponent range remains that of float32. The current 4097 splitter, device subnormal behavior, operation order, and renormalization would each need qualification. Native Metal float64 and CPU propagation remain excluded.

Such persistent pairs are **outside the current recorded contract**: `docs/mlx-port-baseline.md:291` expressly requires one rounded state and no correction across timesteps. A further explicit engineering decision must amend that clause and the single-state coefficient/state wording before dependent implementation. It must specify exact pair arithmetic, constant construction, initial conversion, accumulation with both old components, zero-count copying of both components, reset `(rest,0)/(0,0)`, and freezing of both components.

For a normalized nonoverlapping pair `(v_hi,v_lo)` and exact float32 threshold -45, a valid strict threshold is `(v_hi > -45) OR ((v_hi == -45) AND (v_lo > 0))`; normalization must be an actual invariant. Collapsing `v_hi+v_lo` to float32 before the predicate throws away the improvement. The existing observer, ledger, cause capture, repeat hashes and review prerequisites must observe/hash both native components and validate that exact predicate. Host float64 decoding may be used for independent tolerance comparisons, never to advance or choose candidate spikes. A paired implementation cannot be certified by unchanged observers that silently cast to float32. The old single-state quarter-ULP limit remains historical evidence; a new representation needs its own exact-equality, neighboring-pair and rounding-limit tests. This contingency is not approved for implementation by the present recommendation.

## Minimum next work before any full rerun

1. Sol independently executes the attached host diagnostic, checks its source and recorded hashes, records this bounded decision and limits, then commits the documentation checkpoint. Preserve and finish the existing sugar CPU repeat and P9 pair under their recorded source; a new isolated prototype must not mutate their captured source files.
2. Prototype only the increment expression and its once-rounded `expm1` coefficient with existing uncompiled MLX arrays, under precision setting zero. Verify the local incoming-event replay on device from its actual common reset; preserve the candidate's complete native phase trace and correct first strict predicate. This is a diagnostic fixture, never a replacement for a free-running case. Also require all-neuron arithmetic from the saved preceding state to reproduce the host candidate prediction without pretending that this late substitution repairs the run.
3. Run the unchanged complete scientific core/reference/factored/bucketed suite and prescribed scalar/cancellation cases, including the six-state 10,000-step test, ordinary firing fixtures, the discriminating coupled-versus-Euler case, strict equality and adjacent float32 values, the quarter-ULP limitation, reset/freeze and input gates, delay/self-edge/duplicate-edge/queue wraps, silence and both input classes. Preserve every original budget. Requalify the existing representative fan-in/layout checks; unchanged accumulation code does not make altered trajectories qualified.
4. Prove exact repeatability in fresh state/processes and exact singleton/batched/chunked agreement for the candidate's native voltage, synaptic state, clocks, events, phase hashes, and own queue ledgers. Verify ordinary/observed execution transparency and native float32 recording. Run the applicable application and architecture checks without silently skipping required scientific tests. Commit each verified implementation step separately.
5. Only after those gates pass and Sol records the prospective production adoption may fresh full cases resume. Start with the failed sugar one-second identity under the same canonical input and all fixed/paired gates, full cause capture and repeats. Previously accepted cases are historical evidence for the old arithmetic; the new numerical implementation needs its own required 52-case, repetition and one-second four-trial batch evidence. Preserve all old failed and accepted artifacts. Do not reuse old acceptance or promote the full candidate based on the local probe.

## Reproduction and scope

Exact source: `/private/tmp/astra_timing_remediation_diagnostic.py`.
Exact output: `/private/tmp/astra_timing_remediation_diagnostic.json`.
Source SHA-256: `505abc523d23b0de374f81af1c3593a78d9ac7c7d7dd96e8e0ed4893cc2519dd`.

From `/Users/ocasta/Code/fly-brain`:

```sh
.venv/bin/python /private/tmp/astra_timing_remediation_diagnostic.py > /private/tmp/astra_timing_remediation_parent_check.json
```

NumPy is 1.26.4. The program uses only host NumPy/standard-library calculations and read-only evidence, with no imports of live application engines. It loads numerical helper definitions from the already bound host proof without executing that proof's `main`. Compare the new JSON structurally with the supplied output. The source hash remains valid if the source file is copied unchanged; a different output destination has no effect.

No full case is accepted, no floor/tolerance/threshold/reference/stimulus changes, and no final CPU repeat or P9 disposition is inferred. The earlier completed cause review remains its owner's work and is used as bound evidence, not relabeled as this review's solution. The bounded remediation recommendation is complete; Sol's exact next action is independent host verification and a committed prospective prototype decision.
