# Pinned fly-brain reference baseline

Historical reference record from 2026-10-04. Source inventories, CLI behavior,
package counts, commands, and implementation status below describe that
checkpoint. The active [numerical contract](../numerical-contract.md) owns
approved scientific requirements; [milestone.md](../../../milestone.md) owns
current progress and authorized work. Historical commands use retired paths;
use the [developer workflow](../development.md) for current commands.

Current architecture note (2026-10-04): numerical statements and measured historical commands below retain their original scope. Source links now resolve to the installed package or the retired-source record. Use the current uv commands in [README](../../../README.md) for reproduction; the standalone scripts and Conda workflows are retired. The architecture hold and later milestones are governed by [milestone.md](../../../milestone.md). This note does not change scientific limits or the manual review's owner.

Date: 2026-10-04. Scope: Milestone 0 and the bounded numerical-contract review. The reviewed contract below is approved for Milestone 1 implementation and qualification, not a claim that an MLX implementation has passed. [milestone.md](../../../milestone.md) owns project scope, acceptance, and progress; the [handoff](../handoffs/astra-numerical-contract.md) records the review outcome.

## Source and reproducible reference environment

Repository: <https://github.com/eonsystemspbc/fly-brain>.

Pinned commit: `a3db62f9436074e485c0278290c2164ed6150808`. The import is a merge on `main`, preserving upstream ancestry. Implementation, data, scripts, environment files, and licence files are unchanged relative to the pin. The [pin record](../../upstream-pin.json) is machine-readable.

Relevant implementations:

- [Orchestrator](architecture-remediation.md#retired-source) and [command-line entrypoint](../../../main.py).
- [Brian2 CPU/Brian2CUDA runner](../../../src/fly_brain/qualification/adapters/brian_reference.py).
- [Original paper implementation](architecture-remediation.md#retired-source).
- [PyTorch runner](../../../src/fly_brain/qualification/adapters/torch_reference.py).
- [GeNN runner](architecture-remediation.md#retired-source), [Brian2GeNN runner](architecture-remediation.md#retired-source), and [NEST GPU runner](architecture-remediation.md#retired-source).
- [NEST neuron kernel](architecture-remediation.md#retired-source).

Reference environment: macOS 15.3.1 on `arm64`, Python 3.10.14, Brian2 2.8.0, NumPy 1.26.4, PyTorch 2.11.0, pandas 2.3.3, and PyArrow 25.0.1. [requirements-reference.txt](../../../uv.lock) pins all 36 resolved packages; [requirements-reference.in](architecture-remediation.md#retired-source) records direct dependencies. Brian2CUDA 1.0a7 requires Brian2 2.8.0; its CUDA packages are unnecessary for this CPU baseline. This is a reference environment, not a verified MLX installation.

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

The [baseline harness](architecture-remediation.md#retired-source) invokes the unchanged orchestrator for the shortest supported CPU experiment: sugar, 0.1 seconds, one trial. It redirects the result CSV, spike directory, and standalone build into a new destination and limits compilation to two jobs. These operational overrides do not change equations, stimuli, integration, or recording. It refuses an existing destination, avoiding upstream's `shutil.rmtree(output_dir)` and preserving persisted results. A rerun needs a fresh output path. The harness also checks the returned status because upstream catches runner exceptions and can finish orchestration despite a failed benchmark.

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

Both expressions use the old state. Refractory neurons keep both variables unchanged. The generated implementation multiplies the effective integration time by `int(not_refractory)`; this produces the identity update while refractory. [Generated update and observed schedule](../../evidence/milestone-0/reference-schedule.json) retain the actual code, including temporary variables and assignment order.

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

[Input evidence](../../evidence/milestone-0/input-summary.json) records the schema and hashes:

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

- [compare_ground_truth.py](architecture-remediation.md#retired-source): Brian2 CPU reference, active overlap, shared-active firing-rate correlation, and spike-count ratio. Its `MATCH`/`CLOSE` labels are heuristic thresholds, not an approved MLX acceptance rule.
- [compare_spike_outputs.py](../../../src/fly_brain/comparison/service.py): normalizes canonical `time_ms` to seconds, groups by trial and FlyWire identifier, computes active Jaccard/precision/recall, rates, errors, and greedy one-to-one spike-time matching. Timing defaults to an inclusive 1 ms window. Pearson is undefined for fewer than two shared neurons or constant rate vectors. Empty-network overlap/matching metrics are represented as zero.
- [compare_backend_to_brian2.py](architecture-remediation.md#retired-source): round-based backend-vs-reference reports; timing computation is off unless `--include-timing` is supplied.

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

PyTorch's delay difference follows its previous-step spike propagation, 19-slot buffer (`int(1.8/0.1)+1`), and use of old conductance for the current voltage update. [Raw diagnostic trace](../../evidence/milestone-0/reference-schedule.json) confirms the observed steps without choosing whether the discrepancy is acceptable.

The reset's `w=0` is not a weight mutation: the focused test proves synaptic weights survive. The review selects Brian2 CPU's discrete behavior for every row above. PyTorch remains a measured comparison baseline, not an alternative model to blend into MLX. The paper supports the continuous equations and output-elimination interpretation; Brian2 source, generated code, and probes resolve the discrete details that the paper does not specify.

## Publication and licensing

The [published model](https://www.nature.com/articles/s41586-024-07763-9) states the same voltage/synaptic equations and describes silencing as eliminating neuronal outputs. Its experiments used FlyWire v630. It does not settle the precise discrete scheduling or backend differences above. Full text was retrieved through the [Europe PMC API](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11446845/fullTextXML); [equation/provenance evidence](../../evidence/milestone-0/publication-source.json) records the reviewed sections. Published predictive accuracy cannot be transferred to a new v783 backend simply because a run completes.

The root [LICENSE](../../../LICENSE) is GNU General Public License version 2 (GPLv2). The original paper-model subtree retains its [MIT licence and copyright notice](../../../code/paper-phil-drosophila/LICENSE). NEST source headers carry their own GPL notices. Preserve all of these; a distributed derivative of the root project must follow its source and notice conditions. No licence was replaced, and no proprietary relicensing is proposed. Data-specific reuse notices and publication attribution should be checked before a wider redistribution claim; the data files do not themselves establish a separate data licence in this inspection.

## Verification, measured results, and limits

The [full-data baseline result](../../evidence/milestone-0/brian2-baseline.json) and [log](../../evidence/milestone-0/brian2-baseline.log) prove a successful 0.1-second sugar run: 1,518 spikes, 321 active neurons, 2.347 seconds network construction, 12.742 seconds build, 1.348 seconds simulation, 0.329 seconds extraction, 0.004 seconds collection, 0.014 seconds saving, and 16.824 seconds accounted total. No repeatability, parity, or MLX performance is inferred from it.

[Nine focused tests](../../../tests/qualification/test_reference_contract.py) passed with no skips, failures, or errors: exact leak, coupled synaptic integration, threshold equality, reset/weight persistence, stimulus placement, recurrent delay placement, refractory freezing/input loss/release, outgoing-only silencing, and PyTorch's ineffective refractory gating. [Final test report](../../evidence/milestone-0/reference-tests-final.xml) is retained alongside the earlier run. Assertions on analytical Brian2 double-precision states use absolute 1e-11 mV with relative tolerance zero; time assertions use absolute 1e-12 ms. These are diagnostic bounds, not approved MLX tolerances.

Tests use in-memory synthetic networks and Brian2's NumPy runtime target. They do not create or delete a database, run CUDA, exercise MLX, or claim complete Milestone 1 coverage. The full-data run separately exercises Brian2 C++ standalone. Brian2 and dependency imports produced 136 deprecation/private-API warnings; they are recorded as warnings, not skips. The final run removed a diagnostic object's unused-network warning. A schedule-capture attempt initially indexed Brian2's scalar delay as an array; that inspection error was corrected, and the successful capture reads the scalar properly.

The [inspection harness](../../../src/fly_brain/qualification/adapters/schedule_probe.py) reproduces the recorded schedule and delay trace into a fresh directory. Its output was compared structurally with the retained evidence and matched exactly.

No upstream numerical source has been changed. The normal MLX command-line interface (CLI), full-network parity, MLX device residency, MLX memory/performance, and clean MLX installation remain unverified. The bounded review is resolved below. The next work is the small synthetic MLX kernel after the user's return to Sol.

