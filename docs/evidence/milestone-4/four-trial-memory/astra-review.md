# Bounded first-difference scientific decision

Review requested at `1b33fab`; parent verification completed at `c8a9e01` on 2026-10-05. The fresh-context subagent `/root/review_first_full_divergence` used **GPT-6 Astra at `xhigh`**. Its read-only assignment was to classify the first complete-network spike difference against the existing [roundoff condition](../../../mlx-port-baseline.md#reviewed-precision-and-state-acceptance). Parent settings and the earlier manual assignment were preserved.

**Accepted decision:** the observed difference is consistent with the prospectively approved roundoff condition. No scientific or observation defect blocks that bounded classification. This decision does not accept a full-network case or waive any metric. The missing MLX spike remains in every required comparison.

The first different spike is at step **999**, neuron **41,514**, identifier **720575940620025620**. Brian2 fires; MLX does not. Both neurons are available and their preceding last-spike step is 773.

| Quantity | Millivolts |
| --- | ---: |
| Reference threshold margin | +0.0000153406537473 |
| MLX threshold margin | -0.0000152587890625 |
| Absolute pre-threshold voltage error | 0.0000305994428089 |
| Unchanged trajectory budget | 0.00144999984659346 |

The error is about 2.11% of the budget. The reference margin is also within that budget. No earlier all-neuron phase-state budget violation was observed, and actual common-history queue, input, refractory, and availability checks pass.

Astra independently inspected the [raw current/preceding context](trial-1-spike-context.npz), pinned input rows, executed observer proof, and causal audit. The parent reproduced the material checks and records them in [astra-parent-verification.json](astra-parent-verification.json):

- Original edge **7,516,497**, source **69,593**, signed count **34**, delivers at step **998** from a source spike at step **980**. Its native reference weight is **9.350000000000001 mV**. All 120 occupied device leaves and eight padding leaves agree with the pinned input.
- The selected factored reduction reproduces the actual MLX synaptic result **23.155155181884766 mV** byte for byte. Ordered original-weight addition reproduces the reference result **23.15515233840891 mV** byte for byte.
- The local float32 voltage and synaptic update reproduces the actual current pre-threshold MLX state byte for byte. The preceding end-state voltage error is already **0.0000290937989931 mV**; the discrepancy is accumulated floating-point error, not solely a final threshold cast.
- All 38 saved actual reference queue slots match original-row expectations. The complete stimulus regenerates byte for byte. The current stimulated channel targets neuron **108,426** after threshold and cannot explain this decision at neuron 41,514.
- All-neuron budgets pass for every saved preceding phase and current pre-threshold phase. The largest measured context budget fraction is below **0.167**.

Scope: neither reviewer nor parent reran the complete first-spike replay during this review. Earlier common-history coverage relies on the completed 1,000-step observed execution and inspected audit implementation. These local reproductions do not provide an exact decomposition of every earlier rounding contribution. The isolated Milestone 2 stored-initial-state exception is not used here.

Engineering decision at `c8a9e01`, confidence **99%**: record this classification and proceed with the independent CPU comparator observer. Keep four-trial repetition, independent trials 1–3, the prescribed one-second batch checks, all three-engine metrics, and every case in the frozen 52-case matrix open. No tolerance, acceptance threshold, numerical method, or model contract changes.
