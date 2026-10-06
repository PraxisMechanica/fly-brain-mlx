# Runtime resource ownership review — 2026-10-06

Reviewer: `architecture_ownership`, inherited GPT-6.1 Sol at `xhigh`.
Read-only parent checkpoint: `a9453aa1c3c6a0f7ddbb27b16303dd0441233ecc`.
Indexed and working `tools/architecture/ownership.json` SHA-256:
`dcf449e0379f12dabb2a76284ee981e69e852bb6445e03c617912c5dac96ff18`.
The typed loader reconciles 274 files / 3,770 declaration occurrences with zero
gaps and thirteen recorded findings. This review changes no source or policy.
Its local delivery starts at `d6e8d43d8cd756d1a7d260bffd419da0ab1bd449`.

## Decisions

| Resource | Existing owner and parent | Registry relationship | Confidence |
| --- | --- | --- | --- |
| `reference_build_execution` | qualification / `qualification_case` | `storage_only`, kind `runtime` | 96% |
| `native_execution_state` | simulation / `simulation_run` | `storage_only`, kind `runtime` | 98% |

Here `storage_only` names the registry's non-independent child relationship; a
runtime process is not a database table. Neither resource currently has separate
business use cases, a public lifecycle service, or an independent authorization,
eligibility or reuse policy. Native transitions implement simulation's model;
reference fidelity and acceptance belong to qualification. Their build, advance,
read and cleanup operations do not alone justify creating another domain.
Classification does not approve the current dependency, representation or effect
boundaries. The full architecture result remains **ANALYSIS FAILED (COV002)**.

## Reference build and execution

Application source paths omit the `src/fly_brain/` prefix; line numbers refer to
the reviewed parent checkpoint. Test/tool/document paths are repository-relative.

- `qualification/adapters/parity_case.py:84–115` builds one job under a fresh
  case output, records its descriptor, then executes the qualification case.
  `case_execution.py:29–39` invokes paired collection for `first` and `repeat`.
  `paired_collect.py:53–69` scopes both generators with `closing`; its reference
  generator starts a new native process for each collection. Reusing this one
  compiled program is already part of fresh-process repeatability, not a cache
  hit or reused scientific result.
- `brian_jobs.py:51–66,167–189` validates reference input/capture shape and pinned
  Brian2/thread/build settings, creates a fresh directory, manages Brian2's
  process-global device, compiles without executing, checks the frozen flags,
  and restores the runtime device in `finally`. These are reference production
  mechanics and qualification's frozen fidelity obligations. They are not a
  second resource's independent business policy.
- `brian_jobs.py:192–231` owns the subprocess, stdout, error file and optional
  gzip recording. Exhaustion waits for a zero exit; partial closure terminates
  and, if needed, kills only that process. **A yielded final frame precedes the
  exit check.** Consumers must exhaust/close and propagate failure before
  publishing complete qualification evidence. Build products and result files
  outlive the process as preserved case evidence; this review authorizes no
  removal or new cleanup lifecycle.
- `reference_build.py:21–81,84–139` inventories effective preferences, source,
  installed generator dependencies, actual compiler/headers and linked runtime.
  `reference_identity.py:65–96` hashes supplied scientific identity and generated
  content. Its `create` has no production caller; production `reference_build`
  uses only `file_record` and `installed_packages`. Tests exercise identity
  sensitivity, but no current source implements reference eligibility, sealing,
  cache lookup, publication or a reuse service. `observer_tape.replay` is a
  recorded-wire reader, not evidence that reuse is enabled.
- The exact production `BrianJob` consumers are `parity_case`, `case_execution`,
  `paired_collect`, `paired_causes` and `reference_native`. `BrianJob`, build/run,
  raw native filename maps and build context are absent from registered neutral
  public exports. All five consumers have the same qualification owner; their
  concrete dependencies are an internal role/injection issue, not foreign-domain
  access. The job is a descriptor rather than a process handle, but it exposes
  mutable dictionaries and implementation filenames used as authority to read
  artifacts: `paired_causes.py:31–42` opens a memmap from `job.files['weights']`,
  and `reference_native.py:42–50` opens that file during scientific verification.

The accepted reference-reuse review remains a prerequisite for future reuse,
including post-build identity, two fresh native executions, full tape/native
agreement, completion after zero exits and closed writers, transitive integrity
and candidate-specific audits. It does not establish a currently independent
resource, authorize cache adoption, or prove the outstanding sealing checks.
Revisit the ownership decision if a separately operated eligibility/seal/hit
service is implemented; do not pre-create that domain in this refactor.

Smallest complete current boundary: keep original `brian_jobs`, observer and
build code behind a typed qualification-owned factory/run-reader seam. Case
orchestration receives neutral shape/capture facts and fresh-run capabilities;
the adapter retains directories, native filename mappings, process-global
Brian2 setup and subprocess cleanup. Native artifact readers return actual
detached arrays or requested original-edge weight rows, never a memmap/process
handle. Keep tape/queue/native equality and acceptance interpretation in
qualification; do not turn the producer into the scientific judge. Separate
`reference_native.verify`'s file access from its explicit-input comparisons.
`causal_reduction.py:12–25` must still pair the actual reduction leaves with
actual original reference weights, including ordered identities and padding.
No all-weights copy or host reconstruction is required by this decision.
The unchanged builder still contains global vendor setup and scientific
construction in one function. A consumer wrapper does not prove its role/effect
compliance: retain that debt until a separately allocated provider-lifetime and
source-role repair is verified. Global assembly supplies the provider factory;
case services must not configure Brian2, choose providers or open processes.

## Native execution and state

- `simulation/backend/core.py:24–53` declares device-backed `Network`, `State`
  and `StepTrace`; `initial_state:104–134` allocates trial state and physical
  queues. `engines.py:13–36` binds the concrete advancing callback to a network;
  `bucketed.py:149–198` builds network/layout and binds unchanged advancement
  and actual row reading. `runner.py:23–47` prepares, initializes, advances and
  evaluates one simulation run. No registry public export grants access to
  these objects, callbacks, streams or device arrays.
- Qualification crosses that private boundary in `parity_case.py:15,104`,
  `case_execution.py:6,20`, `paired_collect.py:8–9,41,62–67`,
  `mlx_batch_collect.py:7–8,28,39–44`, `mlx_observer.py:9–15,33–47,60–104` and
  `mlx_ledger.py:5,39–103`. It constructs state, reads network fields, sequences
  device evaluation and directly observes state/trace/queues. These are actual
  foreign private access and concrete collaborator leaks, not plain neutral
  numeric inputs. The ledger also derives receiving, last and future history
  from candidate spikes at lines 58,67–68; independent expectation ownership is
  a required part of the assigned repair.
- Neutral `simulation/observations.py` and qualification's `ReductionReader`
  already form the actual-row boundary. `ReductionRow` copies native values
  into immutable byte-backed arrays at lines 14–17,39–41. That evidence does
  not make `MLXBlock.fields`, queue arrays, `Connectome` arrays or every frozen
  record deeply immutable. NumPy numeric data do not automatically require
  collaborator ports; device runtime operations and lazy lifetimes do.
- Further live private-state/layout consumers remain:
  `connectome_pulse.py:24–42,54–83,125–166` builds/initializes a concrete run and
  checks actual fields/queues; `bucketed_fan_in.py:6–7,13–28,54–70`,
  `bucketed_scalars.py:10–12,19–30,53,113–115` and
  `device_layout_probe.py:10–11,18–24,64–100` construct/read private layouts and
  invoke accumulation. A neutral session alone cannot satisfy the latter
  probes' supplied-mask, supplied-initial-state, actual-gather and reduction
  component observations. Preserve these qualification cases and exact modes.
- A static import projection, including type-only imports, found no
  simulation-to-qualification source edge and thus no two-owner source cycle.
  It found the local cycle `bucketed.py:19 -> reduction_evidence.py:17 ->
  bucketed.Layout`; the reverse edge is under `TYPE_CHECKING`. This is a local
  representation cycle, not proof of `DEP002` between domains. Moving the two
  private layout records to a single native representation module would break
  it without changing algorithms; do not promote MLX records to neutral exports.
  The projection is not complete resolved call/capture/effect analysis.

Smallest complete native boundary: the existing assigned session worker owns
the opaque simulation factory/session/observation provider and qualification's
observer/ledger/paired/case/batch callers. Fresh repeats own fresh mutable state;
continuation retains the same session. Fixed network/layout reuse may retain
the current preparation order, but must not share trial/step scratch state or
mutable observation aliases. The provider owns device allocation, streams,
evaluation and extraction. Qualification owns independent history, threshold,
refractory, delay, receiving, tolerances and acceptance. Mechanical supplied-
operand comparisons may stay on device, with explicit operands and complete
physical queue coverage; a provider-issued acceptance result cannot replace
independent qualification.
Simulation owns the public observation/operand values; qualification declares
its narrow consumed ports. The native implementation can satisfy those ports
structurally without importing qualification's private ledger or rules. Keep
the current source direction; adding a reverse type-only dependency would also
create a domain cycle.

The accepted scheduling follow-up is
`/private/tmp/fly-brain-qualification-session-review-20261006-01.json`, SHA-256
`c7756fdd825c8c16b5c2b198917afc582e23d45e870662c8ed33f370e270ae7a`.
It requires completing/evaluating the unchanged actual step first, retaining
state/trace and immutable native pre-voltage facts, computing qualification's
independent expectations, then evaluating supplied-operand comparisons before
the next advance. The new schedule stays inactive until its recorded ordinary /
legacy-observed / new-observed / fresh-repeat exact-byte proof, all original
block/chunk/fault/four-trial/causal checks, corrupted map/operand/step/trial
rejections, snapshot lifetime and complete shortest pinned-run/memory proofs
pass. This review performs no additional numerical or kernel judgment.

## Exclusive repair allocation and parent action

These are proposed footprints, not work performed or new worker assignments.
All paths below begin `src/fly_brain/` unless shown otherwise. No two writers
may own a listed file concurrently.

| Owner / order | Minimal files and prerequisite |
| --- | --- |
| Parent now | Update only the two resource relationships and parents in `tools/architecture/ownership.json`, with this source evidence; replace the matching unresolved-resource limitation. Remove only the two derived ownership-uncertainty findings. Preserve/register concrete-access, lifecycle, mutable-representation and scientific-adoption debt, and every other finding. Reconcile exact policy/index inputs and rerun the loader/gate. |
| Existing session worker | Keep sole write ownership of `simulation/observations.py`, its new native session/provider files, `qualification/ports.py` and `qualification/adapters/{mlx_observer,mlx_ledger,paired_collect,paired_observer,paired_causes,case_execution,parity_case,mlx_batch_collect}.py`, plus its assigned tests/evidence. Preserve core/reducer/reference/build code and complete the accepted scheduling/adoption obligations. Resolve any shared caller allocation with the parent before editing. |
| Parent allocation after session handoff | Reference seam: proposed new `qualification/reference_values.py`, `qualification/reference_ports.py`, `qualification/adapters/reference_runtime.py`; integrate through `qualification/module.py` and the existing case/paired callers only after their session commit. Split file access from `qualification/adapters/reference_native.py` comparisons and replace `paired_causes.py` raw-weight access together with `causal_reduction.py`. Add exact source-only boundary/lifecycle fixtures and retained integration tests. Frozen `brian_reference.py`, `torch_reference.py`, observer generator and build settings remain unchanged. |
| Parent allocation after session contract is known | Remaining native probes: `qualification/adapters/{connectome_pulse,bucketed_fan_in,bucketed_scalars,device_layout_probe}.py`; new simulation-owned neutral reduction/actual-layout values and narrow consumer ports/provider wrappers, with local module wiring. Supply only operations the probes actually use. Rebase their independent checks on actual detached field/gather/component observations. If breaking the local cycle, allocate proposed `simulation/backend/layout_types.py`, import-only changes to `bucketed.py` and `reduction_evidence.py`, and affected owned tests to one writer. Do not change arithmetic, default `exact_counts` or order. |
| Existing symbols worker | Sole ownership of the native structured-type bridge and its fixtures. Parent uses that bridge to detect vendor/member/alias/capture leaks; this review does not duplicate it. |
| Parent integration | Reconcile each final committed source/declaration/binding/export set, integrate rejection fixtures for direct, aliased, type-only, re-exported, transitive, captured and factory-return leaks, and update shared configuration/status/index. No broad export, generated-source exemption or debt baseline. |

Native reducer consumers `accumulation_probe`, `factored_probe` and
`fan_in_probe` also call private simulation kernels. They need separately
allocated consumer capability boundaries for complete architecture enforcement;
they do not establish an independent execution-state resource or belong to the
session worker automatically. Active tests/support must follow these same
boundaries: notably `tests/qualification/{conftest,test_mlx_observer,
test_mlx_ledger,test_paired_observer,test_paired_collect,test_mlx_batch_collect,
test_case_execution,test_batch_verify}.py` and `tests/support/qualification.py`.
Simulation-owned implementation tests can inspect their own private values;
cross-domain tests gain no exemption from foreign private access.

Frozen historical drivers directly reference these implementations, including
full paired/four-trial proofs, exact-count witnesses, MLX component diagnostics
and the retained original ledger/prototypes. Preserve all sixty evidence-source
records and both adapted references with exact provenance. Analyze their source
at its recorded applicability; missing historical environment/import resolution
is a coverage gap, and definite historical boundary findings remain findings.
Do not rewrite archives, skip them, broaden exports to make them pass, or treat
the newly repaired live reader as the original producer's code.

## Verification and limits

The review used source reads, registry validation, declaration reconciliation and
a static import projection; no application, database, reference build or science
run started. External raw source/projection evidence is retained at
`/private/tmp/fly-brain-resource-review-source-manifest-20261006-01.json` and
`/private/tmp/fly-brain-resource-review-policy-result-20261006-01.json`.
The source manifest binds 95 simulation/qualification/configuration/review paths;
it is an inventory, not a claim that every semantic effect was resolved.
Rechecking those hashes found no change during the source review.

`env -u QUALITY_BASE -u QUALITY_HEAD UV_CACHE_DIR=/private/tmp/fly-brain-documentation-uv-cache-20261005 PRE_COMMIT_HOME=/private/tmp/fly-brain-ownership-precommit-20261006-01 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/fly-brain-ownership-20261006-01/src:/private/tmp/fly-brain-ownership-20261006-01 just check`
exited zero: 160 quality tests passed in 32.32 seconds; Ruff formatting/lint,
strict Pyright (zero errors/warnings), three import contracts and staged/commit
metrics passed. The staged comparison has identical source metrics: 248 files,
27,363 nonblank lines, average/max complexity 5.23/28 and health/maintainability
69.49/69.49. Raw output:
`/private/tmp/fly-brain-resource-review-just-check-20261006-01.log`.
The native commit hook reruns the same required gate; its raw output is retained
at `/private/tmp/fly-brain-resource-review-native-commit-20261006-01.log` and its
completion result accompanies the commit handoff.

The gate validates this worker's unchanged local source at `d6e8d43`, not
the parent's staged integration or future resource repairs. All scientific
acceptance, including reference-cache disablement and the failed one-second
case, retains its original scope. Unknown alias/effect flow, full rule coverage,
historical resolution, neutral-array ownership and future reuse/adoption remain
explicit limits; resolving these two ownership decisions is not a full pass.
