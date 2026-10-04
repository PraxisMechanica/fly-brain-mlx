# Pinned fly-brain reference baseline

Date: 2026-10-04. Scope: Milestone 0 and the bounded numerical-contract review. The reviewed contract below is approved for Milestone 1 implementation and qualification, not a claim that an MLX implementation has passed. [milestone.md](../milestone.md) owns project scope, acceptance, and progress; the [handoff](handoffs/astra-numerical-contract.md) records the review outcome.

## Source and reproducible reference environment

Repository: <https://github.com/eonsystemspbc/fly-brain>.

Pinned commit: `a3db62f9436074e485c0278290c2164ed6150808`. The import is a merge on `main`, preserving upstream ancestry. Implementation, data, scripts, environment files, and licence files are unchanged relative to the pin. The [pin record](upstream-pin.json) is machine-readable.

Relevant implementations:

- [Orchestrator](../code/benchmark.py) and [command-line entrypoint](../main.py).
- [Brian2 CPU/Brian2CUDA runner](../code/run_brian2_cuda.py).
- [Original paper implementation](../code/paper-phil-drosophila/model.py).
- [PyTorch runner](../code/run_pytorch.py).
- [GeNN runner](../code/run_genn.py), [Brian2GeNN runner](../code/run_brian2_genn.py), and [NEST GPU runner](../code/run_nestgpu.py).
- [NEST neuron kernel](../scripts/nestgpu_source_files/src/user_m1.cu).

Reference environment: macOS 15.3.1 on `arm64`, Python 3.10.14, Brian2 2.8.0, NumPy 1.26.4, PyTorch 2.11.0, pandas 2.3.3, and PyArrow 25.0.1. [requirements-reference.txt](../requirements-reference.txt) pins all 36 resolved packages; [requirements-reference.in](../requirements-reference.in) records direct dependencies. Brian2CUDA 1.0a7 requires Brian2 2.8.0; its CUDA packages are unnecessary for this CPU baseline. This is a reference environment, not a verified MLX installation.

Commands executed from the repository root:

```sh
git fetch --depth=1 upstream main
git rev-parse upstream/main
uv venv --python 3.10 .venv
uv pip compile --python-version 3.10 --python-platform aarch64-apple-darwin requirements-reference.in -o requirements-reference.txt
uv pip install --python .venv/bin/python -r requirements-reference.txt
.venv/bin/python scripts/run_reference_baseline.py --output data/results/mlx-reference-20261004
.venv/bin/python scripts/inspect_reference_contract.py --output data/results/mlx-contract-inspection-20261004
.venv/bin/python -m pytest -q tests/test_reference_contract.py --junitxml=docs/evidence/milestone-0/reference-tests-final.xml --disable-warnings
```

The [baseline harness](../scripts/run_reference_baseline.py) invokes the unchanged orchestrator for the shortest supported CPU experiment: sugar, 0.1 seconds, one trial. It redirects the result CSV, spike directory, and standalone build into a new destination and limits compilation to two jobs. These operational overrides do not change equations, stimuli, integration, or recording. It refuses an existing destination, avoiding upstream's `shutil.rmtree(output_dir)` and preserving persisted results. A rerun needs a fresh output path. The harness also checks the returned status because upstream catches runner exceptions and can finish orchestration despite a failed benchmark.

## Neuron equations and parameters

Brian2 declares two state variables in volts and one per-neuron refractory duration:

```text
dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
dg/dt = -g / tau               : volt (unless refractory)
rfc                           : second
```

`g` is a voltage-valued synaptic state, despite being called conductance in some code. It is not a separate physical conductance in siemens. A delivered recurrent event adds its weight to `g`; external Poisson stimulation instead adds directly to `v`.

| Parameter | Reference value |
| --- | --- |
| Resting voltage `v_0` | −52 mV |
| Reset voltage `v_rst` | −52 mV |
| Strict threshold `v_th` | −45 mV |
| Membrane timescale `t_mbr` | 20 ms |
| Synaptic decay `tau` | 5 ms |
| Ordinary refractory duration `t_rfc` | 2.2 ms |
| Activated-neuron refractory duration | 0 ms |
| Recurrent delay `t_dly` | 1.8 ms |
| Weight scale `w_syn` | 0.275 mV per signed connectivity unit |
| External scaling `f_poi` | 250 |
| One external event's voltage increment | 68.75 mV |
| Default clock timestep | 0.1 ms |

Initialization: all neurons have `v=v_0`, `g=0`, and `rfc=t_rfc`. Brian2 supplies the `lastspike` and `not_refractory` state. No background drive is added to inactive neurons.

The runner leaves `defaultclock.dt` at the Brian2 default; the value above was observed in the installed version and the full reference run. A port must not inherit an unknown process-global clock silently.

## Exact discrete linear integration

`NeuronGroup(..., method='linear')` requests Brian2's exact linear state update, not Euler integration. For a non-refractory neuron, writing all times in ms and state in mV, let:

```text
h = 0.1
a = exp(-h / 20)
b = exp(-h / 5)
g_next = b * g
v_next = -52 + a * (v + 52) + (5 / 15) * (a - b) * g
```

Both expressions use the old state. Refractory neurons keep both variables unchanged. The generated implementation multiplies the effective integration time by `int(not_refractory)`; this produces the identity update while refractory. [Generated update and observed schedule](evidence/milestone-0/reference-schedule.json) retain the actual code, including temporary variables and assignment order.

The non-legacy generated refractory comparison is:

```text
not_refractory = timestep(t - lastspike, dt) >= timestep(rfc, dt)
```

The tested 2.2 ms boundary resumes integration at step 22 after a spike labelled step 0. Use the observed/generated comparison rather than inferring an inclusive boundary from prose documentation. The documentation's illustrative expression and this generated code are not interchangeable at the endpoint.

## Per-timestep schedule, spikes, and delays

The actual schedule is:

1. `groups`: update refractory availability and integrate `v` and `g`.
2. `thresholds`, order 0: test `v > v_th` with refractory gating and update `lastspike` for emitted spikes.
3. `thresholds`, order 1: record spike indices and the current clock time.
4. `synapses`, order −1: deliver due recurrent `g += w` events.
5. `synapses`, order 0: apply external Poisson voltage increments.
6. `resets`: reset neurons that emitted spikes in this timestep.
7. `end`: post-reset state is available; the diagnostic state monitors record here.

The clock label is the beginning of the timestep. A spike is timestamped `step * dt`, although integration for that step has already occurred. Do not shift timestamps by one timestep when collecting outputs.

Every recurrent connection uses Brian2's constant 1.8 ms delay. A source spike labelled 0 ms delivers `g` at the synapse slot labelled 1.8 ms, after that step's integration. The first influence on destination voltage occurs in the integration labelled 1.9 ms. The delay test observes zero destination `g` at step 17, `g=1 mV` at step 18, and unchanged destination voltage at step 18.

The threshold is strict: equality does not spike. Reset text is `v = v_rst; w = 0; g = 0 * mV`. `w` is not a neuron state variable here; that assignment is a local reset temporary. The test verifies that resetting a source neuron does not zero its synaptic weight. Implementing it as a synaptic-weight mutation would change the model.

Both `v` and `g` are flagged `unless refractory`. Incoming writes to these variables are ignored while refractory. Delivered inputs are discarded, not buffered until release. The thresholder immediately sets `not_refractory=False` on firing, including neurons with `rfc=0`. Thus incoming writes on that firing step are already blocked before reset. The review's pre-reset monitors verify this distinction; reproducing only the post-reset state would conceal it.

## Activation and silencing

`neu_exc`, `neu_exc2`, and `neu_slnc` are FlyWire identifier lists converted to array positions in the runner. Brian2 creates one `PoissonInput(N=1)` per activated neuron, targeting `v`, with the class's rate and weight 68.75 mV. It sets `rfc=0` for both activation classes. For fixed `N=1`, each timestep's input count is Bernoulli with probability `rate_hz * dt_seconds`. The default second-class rate is zero.

Upstream experiments in `benchmark.EXPERIMENTS`:

| Experiment | First activation class | Rate | Second class | Silencing |
| --- | --- | --- | --- | --- |
| `sugar`, default | 21 listed gustatory receptor neurons | 200 Hz | empty | empty |
| `p9` | two listed P9 neurons | 100 Hz | empty | empty |

The shortest reference run used sugar. The original paper helper's default input rate is 150 Hz, the current Brian2 runner's base parameter is 100 Hz, and orchestration replaces it with the experiment rate. A port must consume the experiment rate rather than selecting one of these defaults by name.

Because stimulation occurs after threshold checking, an external event influences a later threshold test. The deterministic diagnostic uses a guaranteed event every timestep (`rate=10000 Hz`) on one activated neuron. It produces spikes at 0.1 and 0.3 ms and post-reset/end voltages `[16.75, -52, 16.75, -52, 16.75]` mV. A new event on a firing timestep is blocked by the updated refractory flag; reset then clears the state. This diagnostic is evidence about placement, not a proposed physiological experiment.

Brian2 silencing only sets weights whose **presynaptic** index is in the silencing set to zero. The neuron may still receive input and emit recorded spikes. Incoming connections remain. This matches the paper's description of eliminating neuronal outputs but differs from the upstream README's to-and-from wording and some other backends. The review selects outgoing-only silencing; the other descriptions do not override the executable reference.

Externally supplied stimulus schedules are required for cross-engine comparison. Upstream does not currently expose such a schedule through its CLI. Its future adapter must preserve the reviewed stimulation slot, amplitude, target, reset interactions, and refractory behavior. That implementation is not part of this baseline.

## Data, ordering, and weight direction

[Input evidence](evidence/milestone-0/input-summary.json) records the schema and hashes:

- `data/2025_Completeness_783.csv`: 138,639 rows, unique integer FlyWire identifier index, one `Completed` column. `pd.read_csv(..., index_col=0)` preserves row order. Mapping is `flyid2i = {id: position for position,id in enumerate(df_comp.index)}`; the inverse is used for output.
- `data/2025_Connectivity_783.parquet`: 15,091,983 rows. Required fields are `Presynaptic_Index`, `Postsynaptic_Index`, and `Excitatory x Connectivity`. Identifier, unsigned connectivity, polarity, and pandas index fields are also present.
- Both index columns range from 0 to 138,638. Brian2 calls `syn.connect(i=pre, j=post)` in input row order, then assigns `signed_connectivity * 0.275 mV` to each resulting edge.
- `Connectivity` ranges from 1 to 2,405 and sums to 54,492,922. Polarity is +1 for 9,059,302 rows and −1 for 6,032,681 rows. The signed connectivity sum is 10,496,512. These are measured file summaries; connection-row count and the sum of anatomical connectivity weights describe different quantities.
- CSV SHA-256: `52b0ac6094cd32c546f8d4c341e094376f48f4e791f8db9b166de5dff8199ea4`.
- Parquet SHA-256: `efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347`.

PyTorch builds a matrix with row=postsynaptic, column=presynaptic, float32 signed connectivity values. Its recurrent propagation is `spikes @ weights.T`, then scaling by 0.275. Coalescing repeated entries can alter summation order. No MLX representation equivalence, identifier-column consistency audit, or sparse conversion is yet claimed; those belong to Milestone 2.

## Randomness and trial execution

The current CLI has no seed argument. Neither the Brian2 CPU/Brian2CUDA runner nor the PyTorch benchmark runner supplies a seed or shared stimulus schedule. The full-data baseline is unseeded, and its exact spike count is not an expected result for later independent runs.

Brian2 owns `PoissonInput` randomness and supports `brian2.seed`; C++ standalone and runtime generators are different execution paths. CPU `n_run=1` uses C++ standalone. CPU `n_run>1` uses independent joblib runtime workers. CUDA uses standalone. Equal input rates and nominal seed numbers do not establish event identity across those paths.

PyTorch's `PoissonSpikeGenerator` accepts a generator, but the benchmark does not supply one. It generates a full `(n_run, neurons)` Bernoulli tensor each step, including zero-rate entries, and batches trials. Its numerical state and weight matrix use float32 by default; the observed Brian2 state uses float64. GeNN and Brian2GeNN have their own seed environment variables; those still do not provide a common stimulus stream.

## Spike-output and benchmark contracts

The reference emits a Brotli-compressed Parquet file with one row per spike. The successful run's actual schema is:

| Column | Type | Meaning |
| --- | --- | --- |
| `t` | double | Brian2 seconds; PyTorch's legacy `t` instead uses ms |
| `time_ms` | double | Canonical time in ms for both current runners |
| `trial` | int64 | Zero-based trial index |
| `neuron_index` | int64 | Position in the completeness CSV |
| `flywire_id` | int64 | Identifier recovered from that position |
| `exp_name` | string | Backend/duration/trial experiment name |

Current path contract: `data/results/<optional-label>/<optional-round_XX>/<backend>_t<duration>s_n<trials>.parquet`. For the baseline it is `spikes/reference/round_01/brian2cpp_t0.1s_n1.parquet` inside the fresh harness destination. The backend key is `brian2cpp`. Empty DataFrames can infer different dtypes upstream; empty-output dtype policy needs an explicit integration test and reviewed decision.

The orchestrator's result CSV fields are `framework`, `n_run`, `t_run`, `setup_time`, `build_time`, `sim_time`, `total_time`, `realtime_ratio`, `spikes`, `active_neurons`, `status`, `timestamp`, `backend_key`, `experiment`, `experiment_key`, `run_label`, `round`, and `spike_path`. Labeled outputs also get a manifest with spike schema version `1`, time column `time_ms`, and time unit `ms`.

Brian2 records detailed timings for identifier mapping, data loading, neuron/synapse/Poisson construction, standalone build, simulation, spike extraction, collection, and saving. `simulation_total` includes the standalone executable invocation, not just timestep arithmetic. The total is an accounted sum of selected phases, not process startup-to-exit wall time. PyTorch assigns build time zero and its timed simulation includes spike discovery and host transfers when recording. These fields cannot by themselves establish comparable peak memory, compilation/warm-up, synchronization, or steady-state GPU throughput.

## Existing comparison tools

- [compare_ground_truth.py](../code/compare_ground_truth.py): Brian2 CPU reference, active overlap, shared-active firing-rate correlation, and spike-count ratio. Its `MATCH`/`CLOSE` labels are heuristic thresholds, not an approved MLX acceptance rule.
- [compare_spike_outputs.py](../code/compare_spike_outputs.py): normalizes canonical `time_ms` to seconds, groups by trial and FlyWire identifier, computes active Jaccard/precision/recall, rates, errors, and greedy one-to-one spike-time matching. Timing defaults to an inclusive 1 ms window. Pearson is undefined for fewer than two shared neurons or constant rate vectors. Empty-network overlap/matching metrics are represented as zero.
- [compare_backend_to_brian2.py](../code/compare_backend_to_brian2.py): round-based backend-vs-reference reports; timing computation is off unless `--include-timing` is supplied.

Each tool has a fixed backend registry or argument choices, so MLX is not currently selectable. Integration will need a focused registry extension. The acceptance protocol below fixes the timing window, undefined cases, coverage, baseline comparison, and thresholds before validation. Comparing unrelated random schedules would mix stimulus variance with backend error. Existing rounded summaries and shared-active-only rate correlations are insufficient to execute the new gate without a focused validation adapter.

## Observed backend disagreements and adjudication

| Concern | Brian2 CPU reference | Other implementation evidence |
| --- | --- | --- |
| Integration | Exact coupled linear update | PyTorch/GeNN/NEST use Euler-style updates |
| External input placement | After threshold, before reset | PyTorch adds stimulus before integration and threshold |
| Refractory state | Freeze `v` and `g`; gate threshold and incoming writes | PyTorch counter gates delayed `g` input only; voltage and threshold continue; `g` decays |
| Delay effect | Source spike at step 0 delivers `g` at 18; voltage first changes at 19 | Measured PyTorch source spike at step 0 changes destination `g` at 20 and voltage at 21 |
| Silencing | Zero outgoing weights only | README says both directions; GeNN removes incoming and outgoing edges; NEST suppresses spike emission; PyTorch runner ignores silencing |
| Second input class | Separate rate and activation list supported | PyTorch benchmark ignores `neu_exc2`; NEST sets second-class rate to zero |
| Threshold | Strict `>` | NEST kernel uses `>=` |
| Precision | Observed float64 | PyTorch default float32 |

PyTorch's delay difference follows its previous-step spike propagation, 19-slot buffer (`int(1.8/0.1)+1`), and use of old conductance for the current voltage update. [Raw diagnostic trace](evidence/milestone-0/reference-schedule.json) confirms the observed steps without choosing whether the discrepancy is acceptable.

The reset's `w=0` is not a weight mutation: the focused test proves synaptic weights survive. The review selects Brian2 CPU's discrete behavior for every row above. PyTorch remains a measured comparison baseline, not an alternative model to blend into MLX. The paper supports the continuous equations and output-elimination interpretation; Brian2 source, generated code, and probes resolve the discrete details that the paper does not specify.

## Publication and licensing

The [published model](https://www.nature.com/articles/s41586-024-07763-9) states the same voltage/synaptic equations and describes silencing as eliminating neuronal outputs. Its experiments used FlyWire v630. It does not settle the precise discrete scheduling or backend differences above. Full text was retrieved through the [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11446845/fullTextXML); [equation/provenance evidence](evidence/milestone-0/publication-source.json) records the reviewed sections. Published predictive accuracy cannot be transferred to a new v783 backend simply because a run completes.

The root [LICENSE](../LICENSE) is GNU General Public License version 2 (GPLv2). The original paper-model subtree retains its [MIT licence and copyright notice](../code/paper-phil-drosophila/LICENSE). NEST source headers carry their own GPL notices. Preserve all of these; a distributed derivative of the root project must follow its source and notice conditions. No licence was replaced, and no proprietary relicensing is proposed. Data-specific reuse notices and publication attribution should be checked before a wider redistribution claim; the data files do not themselves establish a separate data licence in this inspection.

## Verification, measured results, and limits

The [full-data baseline result](evidence/milestone-0/brian2-baseline.json) and [log](evidence/milestone-0/brian2-baseline.log) prove a successful 0.1-second sugar run: 1,518 spikes, 321 active neurons, 2.347 seconds network construction, 12.742 seconds build, 1.348 seconds simulation, 0.329 seconds extraction, 0.004 seconds collection, 0.014 seconds saving, and 16.824 seconds accounted total. No repeatability, parity, or MLX performance is inferred from it.

[Nine focused tests](../tests/test_reference_contract.py) passed with no skips, failures, or errors: exact leak, coupled synaptic integration, threshold equality, reset/weight persistence, stimulus placement, recurrent delay placement, refractory freezing/input loss/release, outgoing-only silencing, and PyTorch's ineffective refractory gating. [Final test report](evidence/milestone-0/reference-tests-final.xml) is retained alongside the earlier run. Assertions on analytical Brian2 double-precision states use absolute 1e-11 mV with relative tolerance zero; time assertions use absolute 1e-12 ms. These are diagnostic bounds, not approved MLX tolerances.

Tests use in-memory synthetic networks and Brian2's NumPy runtime target. They do not create or delete a database, run CUDA, exercise MLX, or claim complete Milestone 1 coverage. The full-data run separately exercises Brian2 C++ standalone. Brian2 and dependency imports produced 136 deprecation/private-API warnings; they are recorded as warnings, not skips. The final run removed a diagnostic object's unused-network warning. A schedule-capture attempt initially indexed Brian2's scalar delay as an array; that inspection error was corrected, and the successful capture reads the scalar properly.

The [inspection harness](../scripts/inspect_reference_contract.py) reproduces the recorded schedule and delay trace into a fresh directory. Its output was compared structurally with the retained evidence and matched exactly.

No upstream numerical source has been changed. The normal MLX command-line interface (CLI), full-network parity, MLX device residency, MLX memory/performance, and clean MLX installation remain unverified. The bounded review is resolved below. The next work is the small synthetic MLX kernel after the user's return to Sol.

## Reviewed discrete contract

Authority: the pinned Brian2 2.8.0 CPU model, with float64 state, the non-legacy refractory comparison, `dt=0.1 ms`, and the parameters above. Use NumPy runtime for small state traces and C++ standalone for full-network reference trials. The review replay agreed bit for bit across these two paths on the measured network; this is not a guarantee for every reduction or compiler. Record the actual compiler flags and versions in later evidence. The retained C++ build used `-O3 -ffast-math -fno-finite-math-only`; do not silently substitute a different reference.

At step `k`, before advancing the clock:

1. Derive availability `A = (k - last_spike_step >= R)`, where `R=22` ordinarily and `R=0` for every neuron occurring in either activation list, even a zero-rate list. Initially `last_spike_step=-100000000` and availability is true, matching Brian2's `lastspike=-10000 seconds`. Use integer step arithmetic, not a decrementing floating counter.
2. For available neurons only, compute `g' = b*g` and `v' = -52 + a*(v+52) + c*g`, both from the old state. Unavailable state is copied exactly. Here `a=exp(-0.1/20)`, `b=exp(-0.1/5)`, `c=(a-b)/3`.
3. Emit `S = A AND (v' > -45)`. Set `last_spike_step=k` and availability false at every emitted neuron. Record `(trial, neuron_index, k)` now. There is no threshold epsilon or second threshold test after inputs.
4. Deliver all recurrent events due at `k` into `g'` only where `A AND NOT S` holds. A spike at `k` schedules every outgoing edge for `k+18`, including self-connections and duplicate edges. Enqueue independently of the target's present availability; decide whether to discard at delivery. Never move a blocked event to the release step.
5. Apply this step's external voltage events, each worth `68.75 mV`, only where `A AND NOT S` holds. The slot is after recurrent delivery and before reset. A schedule event at step 0 ordinarily first triggers a spike at step 1.
6. For `S`, set `v=-52` and `g=0`; leave all weights unchanged. End-of-step availability remains false for spikers, including `R=0`; it is recomputed at the next step. End-state monitors observe this state.

A 19-slot queue is one valid implementation: consume and clear bucket `k % 19` and place current emissions in `(k+18) % 19`, in the delivery phase after threshold. Queue meaning, multiplicity, and due steps are exact; a different storage layout must implement the same transitions. Do not propagate the previous step's spikes and accidentally add an extra step. Destination voltage first responds at `k+19`. Require tests spanning multiple queue wraps and a target that is refractory when an event is emitted but available when it arrives.

For a spike at step 0, ordinary neurons are frozen on steps 1–21 and resume integration and input acceptance at 22, unless they fire again at 22. Zero-refractory neurons resume at 1. A held nonzero `g` is frozen, not decayed. State reset, dropped events, outgoing-only silencing, and strict thresholding are exact model rules; tolerances never excuse changing them.

Run exactly `N` steps for duration `N*0.1 ms`; labels are `0..N-1`. Do not flush the queue after the final step to manufacture extra output. Preserve pending events when testing chunked continuation. Derive output times on the host in float64 from integer labels: `time_ms=k*0.1`, with no floating clock accumulation or one-step shift. Require recovery of those integer labels within `1e-9 ms` through output conversion. Neuron indices, identifiers, trials, and stimulus/delay steps are exact integers. Keep FlyWire identifiers in int64, never floating point. No output column or type is changed in this review; the empty-output type decision remains an integration schema review item.

## Reviewed precision and state acceptance

Use float32 for MLX voltage, synaptic state, weights, and accumulators in millivolts, with integer clocks/indices and Boolean masks/spikes. Retain Brian2 float64 as the scientific reference. Half precision, quantization, automatic mixed precision, and hidden CPU state updates are outside the approved contract. MLX's [data-type documentation](https://ml-explore.github.io/mlx/build/html/python/data_types.html) restricts float64 to CPU operations. Its [precision documentation](https://ml-explore.github.io/mlx/build/html/usage/precision.html) warns that float32 matrix operations can use reduced precision; launch qualification and production with `MLX_ENABLE_TF32=0` (TF32 means TensorFloat-32). These documents were checked on 2026-10-04 and report version 0.32.3; MLX is not installed or pinned by this review. Sol must verify the selected release and effective setting.

Compute coefficients once in host float64 and cast once to float32. Compute `c` stably as `a * -expm1(-h*(1/tau - 1/t_mbr)) * tau/(t_mbr-tau)`; do not subtract two already-rounded float32 exponentials. The approved float32 coefficients, as exact decimal representations of their stored values, are:

```text
a = 0.9950124621391296
b = 0.9801986813545227
c = 0.004937935154885054
```

Construct each edge weight from the signed integer connectivity times `0.275` in float64, then cast once. Keep edge direction and multiplicity. Factoring the scale outside a reduction, coalescing edges, fused multiply-add operations, or compiler reassociation can change rounding. They are acceptable only after passing the same state, spike, and repeatability gates; mathematical equivalence alone is insufficient. Start with the explicit coupled update, keeping old `g` for the voltage calculation. No custom numerical kernel or alternate sparse representation is approved here.

For each recorded scalar `x` in `v` or `g`, compared in mV with reference `x_B`, require:

| Check | Allowed absolute difference |
| --- | --- |
| Isolated one-step update from the same specified initial state, including its initial cast | `2e-5 + 2e-6*abs(x_B)` mV |
| Every timestep of the small-network trajectory, including pre-threshold and post-input/end states | `1e-3 + 1e-5*abs(x_B)` mV |
| Reference float64 analytical/replay diagnostics | `1e-11` mV, relative tolerance zero |
| Reset values, frozen values within one engine, integer/Boolean state | Exact; no floating tolerance |

Do not use mean error to hide one failed neuron or step. Non-finite state always fails. In the small qualification suite, keep `abs(v)<=256 mV`, `abs(g)<=1024 mV`, at most 32 simultaneous incoming edges per target, and runs up to 10,000 steps. Include the 10,000-step linear decay probe with threshold disabled, as well as firing networks. Larger/cancellation-heavy fan-in is separately qualified before connectome rollout; passing this envelope does not prove a universal error bound.

Justification: float32 unit roundoff is `u=2^-24`; the leaky recurrence amplifies persistent local rounding by roughly `1/(1-a)=200.50` for voltage and `1/(1-b)=50.50` for `g`. Half a float32 unit in the last place (ULP) near rest, accumulated against the voltage leak, is about `0.000382 mV`. The [10,000-step probe](evidence/milestone-0/numerical-contract.json) measured maxima `0.000381470 mV` in voltage and `0.000218289 mV` in `g`, including initial `g=±1024 mV`. Its first-step maxima were `0.000002001` and `0.000008241 mV`. The chosen absolute floors leave room for rounding while the relative terms cover magnitude growth. These are engineering qualification limits supported by this envelope, not rigorous bounds for a recurrent brain or biological uncertainty estimates. An Euler first step at `g=100 mV` errs by `0.00620647 mV` in voltage and `0.01986733 mV` in `g`, exceeding the one-step limits; include that discriminating case.

Exact discrete-state requirements in the ordinary small-network suite: identical spike masks and `(neuron, step)` events, reset masks, availability before and after threshold, last-spike steps, queue due-step/source/edge multiplicity, and consumed/discarded event decisions. A floating queue payload uses the state tolerance, but its event membership cannot differ. Require leak, rest, equality/strict threshold, reset, positive and negative impulses, balanced cancellation, duplicate-edge fan-in, fan-out, self-delay, multiple queue wraps, refractory input loss/release, zero refractory, outgoing-only silencing, two activation classes, overlapping classes, zero-rate channels, empty output, trial reset, and chunked replay. None may be skipped for lack of backend support.

Near threshold, float32 cannot reproduce every float64 spike decision. The threshold-only probe supplies `-45 + ULP/4 mV`; Brian2 fires while float32 rounds to exactly `-45` and does not. Therefore:

- Keep strict `>` at the actual stored precision. Never clamp near-threshold values, add an epsilon, shift event times, or use a reference spike mask in the candidate run.
- Ordinary qualification fixtures must have a reference pre-threshold margin greater than their trajectory error budget at every available test. They require exact discrete parity. Direct predicate fixtures inject equality and the neighboring representable float32 values at the threshold slot and require the correct exact decisions.
- Maintain a separately named rounding diagnostic with the quarter-ULP counterexample. Its expected precision-dependent results are an asserted limitation, not an ordinary parity pass or a skipped test. No universal all-input float64 spike-equivalence claim is approved.
- In full-network validation, record the first different spike and its pre-threshold states/margins. Classify a first difference as consistent with roundoff only if state error is within budget, the reference margin is within that budget, and common-history input/queue/refractory checks agree. This classification does not waive any full-network gate. Once spike histories diverge, unforced long-run state closeness is no longer expected; replay the common prefix and isolate the first cause instead.

Summation order is material: the 4,097-event probe has weights `[2405 repeated 2048, 1, -2405 repeated 2048]*0.275 mV`. The real sum is `0.275 mV`; float32 serial and NumPy reduction in that order give `0.25`, while interleaved cancellation gives `0.275000006`. Thus neither arbitrary scatter addition nor a generic sum is preapproved as accurate or repeatable. Require a deterministic reduction for a fixed execution configuration, record the order, and test mixed-sign/high-fan-in cancellation against float64 before Milestone 2 completes. For diagnostics report `sum(abs(w))` and the standard rounding scale `gamma_m*sum(abs(w))`, `gamma_m=m*u/(1-m*u)`; that pessimistic scale explains conditioning but never enlarges the acceptance tolerance. The adverse case fails the current tolerance and must remain visible. A stable accumulation design that meets the bound is future implementation work; request a bounded deeper review if ordinary library operations cannot satisfy it. Do not quietly trade repeatability for atomic-add throughput.

## Shared stimuli and repeatability protocol

This specifies the mathematical/internal test input, not a new public interface or persisted production schema. Future CLI, endpoint, or output-schema changes still require the explicit human approval described in `AGENTS.md`. The diagnostic uses an internal NumPy array and does not change any existing interface.

Use one Bernoulli channel for each occurrence in `neu_exc` followed by each occurrence in `neu_exc2`, preserving list order and duplicates. Record each channel's FlyWire identifier, resolved position, class, rate, and amplitude. Each channel has event probability `p=rate_hz*0.0001` at every step, and count 0 or 1. Require `0<=p<=1`; this is Brian2's `PoissonInput(N=1)` law, not an unbounded Poisson count sampler or exponentially sampled continuous event time. Channels remain independent when their targets overlap. Set target `R=0` even if that channel's rate is zero. Baseline classes use the experiment's first rate and the explicit second rate (default zero).

Canonical generation for qualification: NumPy 1.26.4 `Generator(PCG64(SeedSequence([20261004, experiment_code, trial])))`. PCG64 is NumPy's named permuted congruential bit generator; do not replace it with an unspecified default generator. Draw float64 uniforms in row-major `(step, channel)` order, including zero-rate channels, then compare `<p` and store uint8 event bits. Generate each trial independently of batch size, worker scheduling, and engine. A shorter duration is a prefix of the longest schedule for that experiment/trial. Chunked generation must consume the same ordered stream. The acceptance matrix below fixes experiment codes; the isolated review probe uses reserved code 2 and is not a full-network schedule.

Persist/reload the generated schedule as immutable validation input once an artifact format is agreed, along with its dimensions, channel order/rates, timestep, seed tuple, generator/version, data/experiment hashes, and SHA-256 (Secure Hash Algorithm 256-bit) over canonical row-major uint8 event bytes. Retain integer event steps; a sparse replay is equivalent only if its `(step, channel)` pairs reconstruct those exact bytes, without merging independent channels or losing simultaneous events. Compare reconstructed schedule hashes at every adapter boundary. Hash equality plus metadata equality, rather than matching seeds, establishes shared input.

For Brian2 tests, replace native randomness with `SpikeGeneratorGroup` and zero-delay input `Synapses` targeting `v`, with `pre.when='synapses'`, `pre.order=0`, and the same refractory write gating. The [review probe](../scripts/probe_numerical_contract.py) exercises this with overlapping channels; the new reference test proves equality with guaranteed native Poisson input including firing-step loss. Do not add native Poisson input on top of replay. MLX consumes each event in step 5 of the reviewed schedule. The PyTorch comparison consumes the identical step's counts at its existing pre-integration stimulus input, preserving its known placement discrepancy; do not time-shift its events to improve its score.

Before any parity score, require byte-identical regeneration and reload, identical duration prefixes, distinct trial streams, and deterministic replay twice from fresh initial state. The review's [raw trace/events](evidence/milestone-0/numerical-contract-replay.npz) contain a 1,000-step, three-channel schedule with counts `[20,10,0]` and hash `f1da12a8a7f3a44198fe04a385f897f991eadea36f680bf5d668ed19343fa09d`. Two NumPy runs and two independent C++ builds all produced 43 spikes and bit-identical full traces. This qualifies the reference replay technique, not MLX repeatability.

For each implementation and fixed hardware/build/execution mode, identical repeated input must produce bit-identical states, spikes, and queue/counter state. Compare full traces in small tests and per-chunk state/event digests plus final state in full-network tests. Also compare standalone trials against batched trials: exact event/discrete equality and the state budgets above. Compilation or reduction changes constitute a new execution mode and require requalification. Different seed tuples define distinct random streams; coincident event bits, especially for zero-rate channels, do not by themselves imply seed reuse. A native stochastic run may be useful separately but cannot replace shared replay evidence.

## Full-network acceptance fixed before validation

These are conservative engineering parity requirements, not thresholds estimated from the unseeded baseline or guarantees of biological validity. They demand at least 95% event/activity agreement, at most 2% aggregate count error, and at most 5% neuronwise count error, then require MLX to meet or beat PyTorch on every primary metric. Full-network results have not been collected in this review. A failure triggers diagnosis and, if needed, a new prospective scientific review; never loosen criteria against the failed results and relabel them a pass.

Use the pinned data hashes and ordering above. Baseline Brian2 is C++ standalone float64, one independent trial per fresh initial state, with shared replay. The paired PyTorch baseline is the pinned float32 `TorchModel`/`AlphaLIF` numerical core, on CPU for a reproducible local comparator, with its Euler integration, delayed propagation, reset, and refractory behavior unchanged. Record version, device, thread settings, and reduction mode. Feed replay counts instead of sampling its Poisson generator. For all three engines supply the same outgoing-silenced connectivity and the union of activated indices to existing refractory-configuration inputs. This defines the comparison for perturbations the old benchmark wrapper ignores; label it **pinned PyTorch core with common experiment setup/replay**, not the unchanged benchmark CLI. No PyTorch repair or retuning is authorized. A different PyTorch device/path is an additional comparison, not a selectable easier baseline.

Required matrix (each trial is paired across all three engines):

| Experiment code | Configuration | Durations | Independent trial indices |
| --- | --- | --- | --- |
| 0 | Existing `sugar`, 21 channels at 200 Hz | 0.1, 1, 10 seconds | 0–4 at every duration |
| 1 | Existing `p9`, 2 channels at 100 Hz | 0.1, 1, 10 seconds | 0–4 at every duration |
| 3 | `sugar`, with all 21 activated neurons' outgoing edges zeroed | 0.1, 1 seconds | 0–4 |
| 4 | Sugar as class 1 at 200 Hz; both P9 neurons as class 2 at 100 Hz; no silencing | 0.1, 1 seconds | 0–4 |
| 5 | No activated neurons, no input, resting initialization | 0.1, 1 seconds | 0 |

This is 52 paired cases. For code 3, reuse code 0's events exactly to isolate silencing; the case code differs but its generator code is 0. Code 4 has its own fixed 23-channel schedule. Code 5 has an empty channel dimension and must stay silent at rest. The code-0 and code-1 runs at 10 seconds provide the shorter prefixes. Repeat every case twice per engine for repeatability. Verify a four-trial batch against the four individual trials on sugar and p9 at 1 second; trial 4 remains independent. Longer claimed validation horizons (100 or 1,000 seconds) must extend the same protocol and thresholds before their results are seen. This minimum matrix does not certify them.

Score each trial/duration/configuration independently, using integer spike steps and exact FlyWire mapping. Never pool trials to conceal a failure. Additionally report pooled summaries and 100 ms time-bin counts for localization. Let `B`, `M`, `P` denote Brian2, MLX, PyTorch; `C_X(i)` counts neuron `i`'s spikes and `N_X=sum_i C_X(i)`. Define a common support `U` as the union of active neurons in all three engines for that case, retaining zero counts for absent neurons. A zero in all three engines contributes no information and is excluded from rate correlation. Compute acceptance at full precision, not from the existing rounded summary strings.

| Primary metric against Brian2, for candidate X | Fixed gate for MLX | Paired gate |
| --- | --- | --- |
| Active-set Jaccard `J_X=|A_B intersect A_X| / |A_B union A_X|` | `J_M >= 0.95` | `J_M >= J_P` |
| Count error `E_N(X)=abs(N_X-N_B)/N_B`; also report signed ratio `N_X/N_B` | `E_N(M) <= 0.02` (ratio 0.98–1.02) | `E_N(M) <= E_N(P)` |
| Neuronwise error `E_1(X)=sum_{i in U} abs(C_X(i)-C_B(i))/N_B` | `E_1(M) <= 0.05` | `E_1(M) <= E_1(P)` |
| Pearson correlation of `C_X(i)/T` and `C_B(i)/T` on common `U` | `rho_M >= 0.99` when defined | `rho_M >= rho_P` when defined |
| One-to-one spike-time F1, per neuron, inclusive `abs(k_X-k_B)<=10` steps (1 ms) | `F1_M >= 0.95` | `F1_M >= F1_P` |

F1 is the harmonic mean of precision and recall, here `2*matches/(N_B+N_X)`. Match sorted times greedily in chronological order exactly as the existing comparator does, within each trial and neuron, without reusing an event. Integer steps remove floating ambiguity at the window boundary. Also report precision/recall, exact-step F1, one-step-window F1, mean/median matched absolute timing errors, shared-active correlation, and rate mean/root-mean-square errors. These are diagnostics, not substitutes for a failed primary gate. Do not compare matched-only timing error as a primary metric: losing hard-to-match spikes could misleadingly improve it.

All primary gates are conjunctive, for every case. For paired rational metrics, compare integer numerators/denominators without tolerance. For computed correlations allow at most `1e-12` comparison slack for host numerical evaluation; there is no one-spike or percentage-point degradation allowance. Thus a weak PyTorch score cannot excuse missing an absolute floor, and a strong PyTorch score raises the requirement above that floor. No averaging metrics into one score and no excluding an unfavorable trial.

Empty/undefined rules are explicit:

- If Brian2 is silent, MLX must have zero spikes exactly; any added spike fails. With both empty, Jaccard and timing F1 are defined as 1 for agreement, count/normalized errors as 0, and correlation as not applicable. This overrides the legacy comparator's zero-for-empty convention only in the future acceptance layer; that code has not been changed here. Non-silent PyTorch cannot invalidate an exact empty MLX result.
- With nonempty Brian2 and empty candidate, overlap and F1 are zero, count and neuronwise errors are 1, so the candidate fails regardless of undefined correlation.
- If a rate vector is constant or `|U|<2`, Pearson is undefined. Mark it not applicable; exact equality of the complete candidate/reference count vectors is then required for MLX instead. If only PyTorch's correlation is undefined, its paired correlation comparison is not applicable, but all other paired gates and MLX's own defined correlation gate remain mandatory. Never replace an undefined correlation with 1 or silently drop the case.
- Missing outputs, wrong data/schedule hashes, duplicate `(trial, neuron, step)` spikes, invalid times/mapping, non-finite metrics, or unequal experiment setup invalidate the case rather than receiving a score. Test empty output through the integration schema review before treating missing files as silence.

For every case report the earliest state-budget violation before any spike difference and the earliest different spike (or explicitly none), including the target, step, threshold margins, stimulus bits, due presynaptic events, reduction order, and refractory state. Small-network gating/delay errors always fail regardless of full-network scores. Any full-network first divergence outside the explained rounding condition requires investigation and blocks acceptance even if summary floors pass. If state cannot be inspected economically in the full run, localize with chunk digests and a deterministic replay around the first differing event; do not claim its cause from a raster alone. Final acceptance requires both this causal audit and every fixed/paired/repeatability gate.
