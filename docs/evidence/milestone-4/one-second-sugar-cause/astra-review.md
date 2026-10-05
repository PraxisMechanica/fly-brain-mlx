# One-second sugar first-cause classification

Completed reviewer: `/root/review_one_second_sugar_cause`, fresh-context **GPT-6 Astra at `xhigh`**, assignment `2c9fd6b`. The reviewer made no project changes, device simulations, network calls or nested delegations. A bounded follow-up supplied the exact host diagnostic. Sol inspected and independently executed it at clean `9ab33d5` before recording this finding. Confidence: **99%**.

**Classify the first difference as explained finite-precision trajectory roundoff under the existing policy.** No observed defect or missing observation blocks this bounded classification. No implementation change is indicated. This finding does not accept the complete case or waive any gate.

## Actual cause

Sugar trial 0, 10,000 steps: the complete first-difference set is neuron position **100,750**, FlyWire identifier **720575940630820919**, at step **5,719**. All **9,723 preceding spikes** match exactly. Actual strict predicates and availability match the saved masks for all 138,639 neurons at both retained steps.

Brian2's native pre-threshold voltage is `-0.04499995946946667` volts and passes its strict `> -0.045` predicate. MLX is exactly `-45.0` millivolts and fails its strict `> -45` predicate. Their error is `0.00004053053332597756` millivolts, below the unchanged `0.0014499995946946668` millivolt budget. This is accumulated trajectory roundoff; directly casting the current Brian2 voltage does not explain the result by itself.

The preceding end voltage is Brian2 `-45.03064854666253` / MLX `-45.03068923950195` millivolts; preceding synaptic state is `13.25429732646695` / `13.254303932189941` millivolts. The last common spike is step **5,492**. Both retained steps are beyond the ordinary 22-step refractory interval. Current all-neuron eligibility from preceding end clocks agrees exactly. Reset/clock differences after this threshold fork are its consequence.

The actual full deliveries are 834 original rows at step 5,718 from source neurons 103,568 and 126,600, and 68 rows at step 5,719 from source neuron 12,494. Their spikes occur exactly eighteen steps earlier; original delivery sequences and MLX due-row identities match. None targets the affected neuron. Its 152 incoming original rows remain in stable order within 256 actual leaves; padded leaves have edge -1/count zero. Every saved reference weight equals both the actual native reference-result weight and `count * (0.275 * 0.001)` volts exactly.

Both retained-step count roots are zero. The actual compensated count/product/final trees therefore preserve the existing synaptic-state byte through the specified zero-count branch. The affected neuron is absent from all 21 input targets. At step 5,718, channel 6's target has already spiked and correctly discards its event; step 5,719 has no source event. The actual replay cursor remains 2,391.

## Independent parent reproduction

The [executed host diagnostic](executed-host-proof.py), SHA-256 `a2ef3c74aae6ff8ba94e82b2aca0ccb2ecc5e22e9a68f16ae9343fe033bbed27`, reproduces the affected neuron's trajectory from its last common reset through the first fork, with no forced intermediate state. **206 available updates**, **31 due rows / 3 discarded / 28 accepted**, reproduce both saved pre-threshold voltage and synaptic state exactly in both native precisions at steps 5,718 and 5,719. Maximum reconstructed pre-threshold voltage/synaptic errors are `0.0000435863434518069` / `0.0000074177575157818865` millivolts. [Structured output, native rows and all checks](parent-host-proof.json).

The final float32 voltage-error contributions are propagated preceding-state error `-4.045726441092287e-5`, coefficient rounding `-1.207127340308034e-7`, and operation rounding `+4.744381953969423e-8` millivolts, yielding the observed `-4.053053332597756e-5` millivolt error. The generated Brian2 expression and unchanged MLX float32/tree operation order reproduce the saved native values exactly.

Sol additionally checks the exact reference integer clock, duplicate-free complete native rasters, the first difference directly from those rasters, every recorded executed source against current source, and the original auxiliary source/destination/weight/refractory hashes. All archive members and 112 native context descriptors remain bound by the [first-cause preflight](first-cause-preflight.json). Both copied execution artifacts match their executed originals.

The review's first scratch eligibility check incorrectly used a step's own end clocks to reconstruct that same step's pre-threshold availability for neurons that had just fired. The corrected check uses preceding end clocks for current availability; preceding spikers' actual pre-masks are checked directly. That correction changed no execution evidence or implementation and is explicit in the retained diagnostic.

## Limits and next action

This is a first-cause classification and host reconstruction, not a fresh native replay or full-case acceptance. Historical common-prefix budgets and each engine's own ledgers are supported by the completed live audit and complete digest coverage; the archive does not contain every historical native state. Cross-engine continuous/queue equality is inapplicable after the fork. Finite state, own event/queue validity, complete coverage and exact native fresh repetition remain mandatory.

Preserve the active execution and original automatic report. Once it completes, independently verify all eleven fixed/paired metric gates, all remaining case checks, complete repeats/cause contexts, canonical input/source/mapping/precision, and each engine's future queues under the [prospective adjudication policy](../case-adjudication/astra-review.md). Only then may Sol record a separate reviewed-case decision. Acceptance remains **9/52** at this checkpoint.
