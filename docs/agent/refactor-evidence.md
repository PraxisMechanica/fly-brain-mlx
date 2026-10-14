# Refactor verification records

Audience: agents and maintainers. These are committed component checkpoints,
not the current work order or a complete architecture/scientific approval.
Later qualified checkpoints can replace an earlier component limitation.
The active scope, holds and remaining work belong to
[milestone.md](../../milestone.md); executable coverage belongs to
[quality-coverage.md](quality-coverage.md).

Consumed raw diagnostics and execution outputs were deleted under the current
output policy. These bounded summaries do not claim those raw proofs remain
reproducible from this checkout.

## Incremental workflow qualification

The user also requires incremental coherent commits. The following focused
workflow commits are delivered to `origin/main`:

- `fd55d95`: scoped ownership review, with metadata parsing separated from source
  review. The existing controls and affected relocation/weakening controls passed;
  metrics passed at 348 files, mean 15.36, maximum 96 and health 39.65.
- `86038e0`: canonical parity stimulus dependency contract, two files. Its live
  import check, strict typing, Ruff, ownership and native metrics passed.
- `c77c904`: changed-input selection and canonical native graph context. All 27
  cases remain; 25 affected cases passed, with two unchanged previously qualified
  controls deliberately not repeated. Strict typing/Ruff passed. Metrics kept
  mean 15.36 and maximum 96 while health improved 39.65 to 39.73.
- `83d7252`: installed commit/push hooks and hosted stage wiring, changed-source
  consistency checks, scoped native import evaluation and independent input/
  metric failure propagation. The normal mandatory commit hook and default
  cleanup passed. The hook did not execute pytest.

The first selector and optional disk-cache candidates failed native metrics and
were not committed. A completed fresh Astra review identified genuine source/
fixture simplification; the accepted selector retains every guard and case. No
threshold, metric provenance, suppression or predicate was weakened. The second
follow-up review could not start because the selected model was at capacity;
no substitute model or extra review acceptance is implied.

Parent integration controls cover doc-only skipping, affected dependencies,
staged debt hidden by an unstaged repair, actual push rejection, source-context
invalidation, native removals, child failures and cleanup safety. Newly affected
API/hook cases passed (24 cases in 2.97 seconds); the two added boundary context
cases passed in 0.23 seconds and four independent input/metric hook cases passed
in 4.05 seconds. Other unchanged cohorts were not replayed. Python deletion or
rename impact that cannot be proved fails COV002. Complete architecture coverage
and the six recorded findings remain unresolved; this is workflow qualification.

The first five focused commits are pushed at `f6763e2`. Inspection of hosted
run `38536184801` found a false zero-file submitted scope; its success is not full
range acceptance. Corrective commit `b42714d` replaces positional revision
arguments with native range traversal and explicit separate merge-parent diffs.
Six controls fail against the old code; 12 affected controls pass after repair,
including five-commit reverts, merge-only paths, hostile merge configuration,
NUL-safe names and empty ranges. Strict checks and normal commit hooks passed.
Native metrics improved mean 15.35 to 15.31 and health 39.80 to 39.88; maximum
96 is unchanged. Existing assertions, metadata and metric predicates remain.

The corrected complete `eb6fe8f..b42714d` delivery check selected 37 changed
inputs and 89 affected Python files. Inputs, formatting/lint, strict typing,
90 import module/contract checks, ownership of 27 selected sources and every
commit/merge-parent metric comparison all passed in 12.85 seconds. Regression
tests were not replayed. The two worker holds are released against this checked
parent. The correction and source-preservation clarification are pushed through
`6e64ca5`. Exact hosted run `38539655453` passed with seven changed inputs and
seven affected Python files; its quality step took 21 seconds and its complete
job took 87 seconds. It ran no pytest and uploaded zero artifacts. The earlier
zero-file result remains explicitly incomplete.

## Delivered component verification

The historical-record cleanup is delivered at `79f62ad`; generated historical
records are absent. `3c6865f` separately fixed foreign Git-index inheritance in
fixture cleanup. Their source/input preservation remains intact; deleted raw
outputs are not current reproducible proofs.

The following components are committed on parent `main`:

| Component | Parent commit | Bounded evidence |
| --- | --- | --- |
| Native structured types and checked JavaScript inventory | `9d73531`, `38ce609` | 44 type intent cases; pinned compiler inputs work inside or outside the checkout |
| Active native type-import coverage | `c4084be` | 25 distinct cases; actual bound imports/reachability, source-located missing/partial records, namespace origins, refreshed loaded inputs and unchanged precision |
| Exact neutral comparison import boundary | `76f1e5d` | 38 import cases and 15 existing commit/push cases |
| Connectome neuron and recurrent-edge array identities | `fd0a54f` | 193 input/type cases and 107 Metal/reference cases |
| Injected qualification comparison operations | `6b495a8` | Unchanged calculation files; consumer-owned scoring, coordinates, clock conversion and diagnostics |
| Native explicit-call selected signatures | `c46f98f` | 48 final-worker cases; no runtime-dispatch claim |
| Reviewed domain binding placement (OWN001) | `c688ab1` | 30 final focused cases; independently validated version 2 inputs required |
| Experiment, stimulus and observation-session identifiers | `e41d03f` | 346 worker input/type cases and 102 native cases; 43 normalized modules and 239 old assertions preserved |
| Native partial construction facts | `1610c6a` | 44 worker cases and 19 independent parent controls; static constructor/capture facts only |
| Qualification case trial labels | `f27a75b` | 193 worker cases and three native checks; all 52 catalog values/order unchanged |
| Canonical batch trial labels | `78599bd` | 57 distinct host/type cases once; wrong-space fields/keys, independent weakenings, exact integer encoding and label 3 versus singleton position 0 |
| Consumer-owned parity stimulus preparation | `eb6fe8f`, `86038e0` | Both catalog reads, seed, persistence/silencing order and errors retained; sixth live import contract checked |
| Owned spike array identifiers | `f20d6ec` | 106 CPU cases and one real Metal case passed once; eight normalized modules, 67 original assertions, array identity/bytes/layout and seven fixtures preserved |
| Injected pure reference parameters | `4c87409` | Exact factory extraction and five protected hashes; 100 CPU, six boundary, five native and two composition cases; 6,120 native tensor-byte pairs preserved without replay |
| Comparison scalar identifier keys | `fe14b74` | 32 focused cases; three identity wrappers, four unchanged calculation functions and 16 byte-exact original/new JSON/CSV outputs |
| Canonical native Python compiler context | `39c4556` | 21 defined cases; independently reconciled source/configuration/import-origin facts; equivalent read capture and record/process separation |
| Shared canonical compiler session lifetime | `7ab7d04` | 11 session and six affected context cases; unchanged report/config/hash/disposal logic and loaded-origin projection; selected-unbound stubs remain missing |
| Consumer-owned reference connectome silencing | `1b64d51` | 36 focused controls; 18 normalized modules, 70 original assertions, unchanged mapping, five protected sources and seven fixtures |
| Consumer-owned host input mapping | `9019148` | 19 focused cases without reruns; byte-exact original/candidate NPZ and JSON, four callback positions, six normalized modules and 15 original assertions |
| Injected fan-in grouping | `d0c1d6f` | Nine distinct controls; actual ordered probe flow with inert backend, existing lazy factories, required-reader type rejection and unchanged numerical bodies |
| Pure host audit rules and injected file storage | `b56caf2` | 28 affected cases; exact old/new archive/report, original assertion and error order, lazy assembly and returned artifact identity |
| Distinct row/FlyWire rasters | `6dfede5` | 117 distinct focused cases; native type arguments with resolved NumPy, 14 normalized modules, 54 old assertions, exact borrowed arrays and numerical bodies |

Every component passed its required normal commit checks and default cleanup. Joined
metric regressions were repaired without thresholds, suppressions or removed
production guards. At `f27a75b`, ownership reconciles 321 Python/stub sources with
zero mapping findings and six recorded findings. Native metrics cover 342 files:
mean complexity 15.40, maximum 96, health/maintainability 39.41, zero findings.
These are component checks, not complete architecture acceptance.

At `f27a75b`, the combined ordinary pytest selection passed **1,499 tests** with
27 dependency warnings in 423.47 seconds (423.99 seconds wall time). It contains
793 application tests and 706 quality tests. It excludes only the existing
`tests/integration/test_session_proof_artifacts.py` consumer, which requires a
fresh full native proof bundle; scientific qualification is outside this run.
Summed per-test durations are 50.95 seconds for application tests and 370.26
seconds for quality tests. The slowest case took 3.70 seconds. Import-boundary,
metric and compiler/hook fixtures dominate; this does not establish that all
historical scientific performance problems are fixed.

The first timing attempt put execution-producing fixtures under `logs`; all 71
observed failures were the unchanged scientific output-path guard. It was
interrupted and rerun with fresh fixtures under `executions`. The failed run is
not acceptance evidence. Timings and failure classification completed their
consumers; their raw outputs have no retention exception.

At that checkpoint, five comparison calculation files, four frozen sources, six
pinned input files, both licences and seven independent fixtures were byte exact.
The identifier changes preserve numerical bodies and old assertions; NewType supplies nominal
typing without new runtime validation or complete conversion-origin proof.
No full native proof bundle or scientific matrix was recreated.

All listed source components are pushed to `origin/main` through `78599bd`.
The spike identifier component passed the installed normal commit and push hooks
and default cleanup without replaying its completed regressions. Delivery uses
one ten-file component commit; the worker's earlier private ancestry is preserved
without republishing already delivered refactors. Exact hosted run `38543167157`
passed with ten changed inputs, 159 affected Python files, nine reviewed sources
and 69 import module/contract checks. The quality step took 26 seconds; the job
took 82 seconds, with no pytest and zero artifacts. `38ce609` previously repaired
the hosted compiler-layout failure in exact passing run `38505093226`.

The four-file Metrics slice passed installed commit/push hooks and exact hosted
run `38548469719`: four changed inputs, 45 affected Python files, 26 import
module/contract checks and 28 ownership sources. Its component owner ran 32
unique cases once; only the repaired weakening control and three simplified
runtime instances repeated after actual failures. The fixture's measured
complexity is 11, cognitive complexity 5 and health 48.50; repository CQ001–CQ003
passed, with no final rounded repository values retained after cleanup. The new
fixture is reviewed as `comparison/test`. Generic report identities, mixed
rasters, batch label/position contracts and lawful origins remain unresolved;
all six recorded findings remain. Hosted execution ran no pytest and uploaded zero artifacts.

The eight-file compiler-context component passed normal commit/push checks and
exact hosted run `38552915992`: eight changed inputs, three affected Python
sources, three reviewed sources and 347 unchanged records. Its quality step
took 12 seconds; its complete job took 48 seconds. Hosted execution ran no pytest
and uploaded zero artifacts. The worker retained all 21 cases; only changed or
failed controls repeated. Native metrics kept mean 15.29 and maximum 96 while
health improved 39.91 to 40.11. Configuration/source observations do not supply
missing declaration, call, effect or runtime-dispatch capabilities.

The reference-silencing component passed normal commit/push checks and exact
hosted run `38554048146`: 23 changed inputs, 73 affected Python files, 93 import
module/contract checks, 21 reviewed sources and 332 retained source records.
Its quality step took 17 seconds; the complete job took 64 seconds. Hosted
execution ran no pytest and uploaded zero artifacts. It removes the
qualification adapter's private mapping call through required consumer/provider
ports, preserving the float32 guard, call order and original rule.
Its 36 distinct focused controls qualified the affected callback, port,
composition, identity and native paths; 88 qualification cases collect. Only
failed or changed controls repeated during repair. Existing scientific
trajectories were not replayed. Worker metrics improved mean 15.21 to 15.20,
with maximum 96 and health 39.94 unchanged. Seven exact import contracts are
configured. The native framework's missing forbidden-target limit is retained
as a control; a separate required-gate coverage repair remains with its owner.

The separate configured-target coverage repair is pushed at `26e4df3`. It keeps
production complexity at 25 and the original incremental fixture byte exact.
Twenty-two distinct controls are qualified; only changed or failed controls
repeated. Worker native metrics improved mean 15.20 to 15.18 and health 39.98 to
40.01, with maximum 96 unchanged. Normal commit/push checks and exact hosted
run `38555176909` passed: three changed inputs, three affected Python files,
93 import module/contract checks and two reviewed sources. Its quality step
took 16 seconds; its job took 72 seconds, with no pytest and zero artifacts.
Missing configured first-party targets now fail COV002 before inactive-source
skipping; the separate raw-framework limitation control remains unchanged.

Source review at `2d0a7e6` distinguishes the qualification fan-in tuple aliases
`Reduction` and `Evaluation` from callable ports. Their exact classifications
are `qualification/types`; provider code, public exports, source fingerprints
and six findings are unchanged. Decision confidence: 95%. This metadata-only
correction requires no numerical execution or regression replay.

The ten-file host input-audit boundary component is pushed at `9019148` after
normal commit/push checks and exact hosted run `38559492970`: ten changed inputs,
73 affected Python files, 94 import module/contract checks, eight reviewed
sources and 348 retained records. Its quality step took 17 seconds; its complete
job took 59 seconds, with no pytest and zero artifacts. Its 19 focused cases
passed without reruns; archive
SHA-256 `bd4f62f828d09125d7929472203edd68d836a5bdb53330ebf75186d0c509e376`
and JSON bytes match the original driver. Mapping/model bytes, five protected
sources and seven fixtures remain exact. Worker metrics kept mean 15.17 and
maximum 96 while health improved 40.20 to 40.26. Required consumer/provider
readers preserve grouping, absolute counts, silencing and late bucket acquisition.
The pure bucket report receives completed data; `MappedArray` is reviewed as
`qualification/types`. Eight import contracts are configured. The separate role/persistence repair is recorded below at `b56caf2`.

The 13-file host audit role separation is pushed at `b56caf2` after normal
commit/push checks and exact hosted run `38564788054`: 13 changed inputs,
84 affected Python files, 11 reviewed sources and 350 retained source records.
Hosted execution ran no pytest and uploaded zero artifacts. Its 28 affected
controls passed in 9.14 seconds without replay. Pure rules, orchestration and
four repository operations now have separate owners; `InputAuditFiles` is a
required injected port, and assembly stays lazy. Actual returned Path reuse,
str-before-read/hash and header failure after NPZ but before artifact reading,
bucket acquisition and JSON remain unchanged.

Archive/report bytes, numerical/storage syntax, 15 original rule assertions,
67 existing fixture assertions and original raises are preserved. Five protected
sources and seven independent fixtures remain exact. Worker metrics improved
mean 15.17 to 15.10 and health 40.26 to 40.34 across 380 to 383 files; maximum
96 remains. Nine import contracts are configured. Resource, identifier,
provenance and finding inventories remain unchanged; complete effect, alias
and architectural enforcement is still missing.

The raster identifier component is pushed at `6dfede5` after normal commit/push
checks and default cleanup. All 117 distinct focused controls are qualified:
106 passed initially, ten repaired fixture-import cases then passed, and the
remaining native type case passed after supplying the installed NumPy root.
Completed cohorts were not replayed. The first native context had active
unresolved NumPy imports; both NewType bases were native Any, promoting both
aliases to the later constraint. The repaired context resolves authored/NumPy
imports, retains their actual input hashes and observes separate row/FlyWire
arguments with known ndarray bases. Dormant Python 3.14 branches in upstream
typeshed still name absent annotationlib. Projector code and specialization
expectations are unchanged; active-import rejection is separately delivered at `c4084be`.

Fourteen normalized modules and 54 original assertions retain their meaning;
340 other Python files, five protected sources and seven fixtures remain exact.
The record still borrows the original arrays with unchanged field order,
bytes, dtypes, layouts and numerical calculations. Final worker CQ001–CQ003
and parent checks passed; final rounded worker values were removed by cleanup
and are not reproduced here. Exact hosted run `38564314747` passed with 16
changed inputs, 47 affected Python files, 15 reviewed sources and 343 retained
records. It ran no pytest and uploaded zero artifacts. The six recorded findings
and lawful conversion-origin limitations remain unresolved.

The seven-file compiler-session component is pushed at `7ab7d04` after normal
commit/push checks and exact hosted run `38560890820`: seven changed inputs,
two affected Python files, two reviewed sources and 355 retained records.
Its quality step took 16 seconds; its complete job took 72 seconds, with no
pytest and zero artifacts. It shares the canonical live Program through bounded
source reads and refreshes loaded origins after a consumer, preserving the
initial source enumeration and final hashes. Eleven session cases and six
changed context cases qualified; all 21 original context cases still collect.
One weakening case accidentally ran twice; no further replay followed. Worker
metrics improved mean 15.17 to 15.14 and health 40.20 to 40.23; maximum 96 is
unchanged. At that checkpoint, selected unreferenced stubs lacked native binding;
the later enrollment repair below supplies bounded native reads, not complete
declaration coverage. The historical declaration candidate remains
unadopted and full 37-rule coverage remains COV002.

The nine-file canonical batch-label component is pushed at `78599bd` after
normal commit/push checks and exact hosted run `38571882656`: nine changed inputs,
nine affected Python files, eight reviewed sources and 356 retained records.
Hosted execution ran no pytest and uploaded zero artifacts. Fifty-seven distinct
affected cases passed once in 8.27 seconds; 11 pinned Pyright CLI invocations
cover 18 wrong-space substitutions, one shared repair, three independent
selected-module weakenings and float-key rejection. CPU artifact comparison
preserves requested label 3 versus singleton position 0, order, integer encoding
and original float-key tuple-index failure timing. Local positions and the
original position-call argument remain unchanged; no runtime int conversion
or new validation is introduced.

Seven normalized modules, ten original assertions, 354 other Python files,
five protected sources, seven fixtures and six tracked data inputs remain exact.
Worker metrics improve mean 15.06 to 15.05 and health 40.41 to 40.43 across
386 to 387 files, with maximum 96 unchanged. Fixture complexity failures were
repaired through shared diagnostics/digest setup and complete parallel snapshots,
retaining every predicate; no cohort ran until the candidate passed metrics.
The six recorded findings remain. Positional artifacts lack requested-label
metadata; lawful origins and joint stimulus/artifact identity remain unproved.

The six-file network-case selector component is pushed at `3736127` after
normal commit/push checks and exact hosted run `38577838508`: six changed inputs,
148 affected Python files, five reviewed sources and 360 retained records. Its
quality step took 26 seconds, with no pytest and zero artifacts. Twelve distinct
affected controls passed once in
5.37 seconds: twelve wrong-space field sites, a shared repair, four independent
field weakenings and four host-preservation instances. Strict typing and Ruff
passed; worker metrics improve mean 15.03 to 15.01 and health 40.52 to 40.55,
with maximum 96 unchanged. Four normalized modules, all 80 original assertions,
33 constructors, 360 other Python files, five protected sources, seven fixtures
and six tracked data inputs are preserved. Only four selector annotations and
148 identity-only element wrappers change; five empty constructors stay exact.
Passed tuple/scalar identities and host layouts are preserved. Historical
cross-site literal-tuple coalescing is outside the contract. Scientific collection
failed at the qualification conftest because no Metal device was available;
no scientific cases ran. All six findings and numerical holds remain.

The five-file fan-in grouping seam is pushed at `d0c1d6f` after normal
commit/push checks and exact hosted run `38571157980`: five changed inputs,
16 affected Python files, four reviewed sources and 359 retained records.
Hosted execution ran no pytest and uploaded zero artifacts. Nine distinct
controls are qualified; only changed assertion/harness controls repeated.
The first Metal-dependent collection attempt executed zero cases. Ordered
runtime controls execute actual probe source with inert backend dependencies,
ending before numerical evaluation; no kernel/layout cohort was replayed.

The same Connectome reaches the required grouping reader exactly once after
analysis. Both factories preserve their existing argument evaluation, default
or layout evaluator and scope. Numerical/report bodies, five protected sources
and seven fixtures remain exact. Forty-eight old composition assertions are
syntax exact; one approved joined assertion preserves its old callable predicate
and adds the reader predicate, with independent rejection checks for both.
Worker metrics improve mean 15.06 to 15.05 and health 40.41 to 40.44 across
386 to 387 files, with maximum 96 unchanged. Earlier metric failures were
repaired without removed operands or waivers. The indirect absolute-count
mapping dependency and mixed provider roles remain unresolved.

The nine-file late fan-in count boundary is pushed at `992f5a4` after normal
commit/push checks and exact hosted run `38579010733`: nine changed inputs,
33 affected Python files, seven reviewed sources and 359 retained records.
Its quality step took 17 seconds, with no pytest and zero artifacts. Twenty-six
distinct affected controls are qualified; three initial unused-import fixture
failures were repaired, and only five controls with changed inputs repeated.
Worker metrics improve mean 15.03 to 15.02 and health 40.52 to 40.60 across
390 to 391 files, with maximum 96 unchanged.

The probe preserves preparation → required count read → pure completion →
grouping → case construction and original failure order. Four host cases prove
32 exact field snapshots, 28 aliases and three matched errors. Numerical,
evaluator and NPZ-writer syntax remains exact after seam binding; no backend
trajectory ran or produced a replay archive. Six report source keys are retained
and four reviewed provider/seed modules added; this bounded capture is not
complete execution provenance. Five protected hashes and seven fixtures remain
exact. The configured mapping guard now covers both input-pattern and probe
modules; all six findings and complete structural/scientific limits remain.

The five-file native type-import guard is pushed at `c4084be` after normal
commit/push checks and exact hosted run `38568072694`: five changed inputs,
one affected Python source, one reviewed source and 361 retained records.
Typed JavaScript, native syntax and every hosted step passed, with no pytest
and zero artifacts. Twenty-five distinct controls are qualified; 13 changed
invocation-seam controls repeated after the genuine helper extraction, while
12 unchanged public controls were reused. The initial per-file/repository
complexity failure was not committed or waived. Final worker metrics improved
mean 15.13 to 15.12 and health 40.28 to 40.34 across 382 to 384 files, with maximum
96 unchanged.

The import guard owns actual parsed/bound import records and native reachability.
It rejects active missing/partially resolved modules or invalid native facts,
refreshes loaded inputs after queries, and permits actual namespace imports and
unreachable version branches. `NativeSources` is byte exact; type projection,
call/partial APIs and existing precision predicates are unchanged. Manual type
contexts still require correct import roots; computed imports, complete ancestry,
effects and runtime targets remain unproved. B now assesses the old 14-path
uncommitted declaration prototype and a minimal canonical-session observation;
its historical failing tree is preserved, not delivered or accepted.

The `Advance` finding is classified as DEP004 after the literal source/export
review at `992f5a4` (confidence 95%). ROLE006 requires a public domain contract;
`Advance` is excluded from that reviewed export set. Its ports still depend on
concrete state/trace/device types, directly and through `Execution`, so the debt
and six-finding count remain. No source, numerical behavior or export permission
changes. A fresh Astra review assesses the minimum neutral numerical value and
primitive boundary before dependent implementation; full analysis remains COV002.

The six-file selected native-source enrollment component is pushed at `98ade94`
after normal commit/push checks. Exact hosted run `38579880497` completed every
job step and its quality step successfully: six changed inputs, two affected
Python files, two reviewed sources and 365 retained records. The quality step
took 14 seconds, ran no pytest and uploaded zero artifacts. A later push cancelled
the final run status after those checks finished; completed checks were not
replayed. Twenty-one affected controls are qualified and five unchanged controls
reused; all 26 remain. Only changed repair/extraction/relocation seams repeated,
including the 13 relocated binding controls in 3.33 seconds.

Interim enrollment forces native parsing/binding and validates the actual Module,
scope, symbol table and original-file identity. Unreferenced stubs keep their
untracked flag; repeated reads retain file/tree identity and cached binding.
Session admission/disposal, CLI enumeration, report/configuration and final input
hash guards remain. Typed JavaScript, strict Pyright, Ruff, native syntax and the
new bridge-file inventory passed. Worker metrics improve mean 15.03 to 14.97
and health 40.52 to 40.71 across 390 to 392 files; maximum 96 is unchanged.
Metric failures were repaired by separating enrollment and session responsibilities,
with six verification statements and moved control bodies preserved. Complete
declarations, dormant bindings, alias/effect/call/control-flow and runtime
context equivalence remain missing; the historical prototype stays unaccepted.

The six-file Torch target-selector component is delivered at `15b8871`.
Normal commit/push checks and exact hosted run `38583143321` passed over the
`615764d..4b98632` two-commit range: eight changed inputs, 27 affected Python
files, five reviewed sources and 363 retained records. Its quality step took
23 seconds, ran no pytest and uploaded zero artifacts. Twenty-six distinct
controls passed once: 17 identity/CPU cases in 7.86 seconds and nine provenance
cases in 0.36 seconds; 18 unchanged cases were deselected.

Three target annotations use `NeuronRow`; seven authored fixture elements retain
scalar identity. Each signature has independent weakening and exact wrong-space
rejection. Ordinary versus observed CPU execution compares 520 individual arrays
across five native fields and 260 trial hashes over 25 steps, one/four trials and
empty/overlapping
channels. Production numerical/hash/launch predicates and `_SOURCES` remain
exact. The launch fixture changes only the selected launch/file key, with its
four-case truth table verified; generic all-source corruption did not establish
the selected module's guard. Its initial per-file complexity 21→22 failure was
repaired without removing either key condition. Four normalized existing modules,
eight original assertions, 361 other Python files, five protected sources,
seven fixtures and six tracked data inputs are preserved. Worker metrics improve
mean 15.01 to 15.00 and health 40.55 to 40.59; maximum 96 remains. Two existing
Torch sparse warnings occurred. Metal-dependent collection failed before
scientific cases; direct CPU controls grant no new scientific acceptance.

## Native bound-declaration observation

The four-file observer is pushed at `2e5e04b` after normal commit/push checks.
Exact hosted run `38588500963` passed every step; its quality step took 11 seconds,
ran no pytest and uploaded zero artifacts. Twenty-seven distinct controls are
qualified: the initial 26 passed in 7.52 seconds, then the added unmatched-node
control and genuinely affected inventory control passed in 1.51 seconds.
Strict Python and checked JavaScript typing, Ruff and native syntax passed.
Worker metrics improved mean 14.93 to 14.89 and health 40.86 to 41.05 across
395 to 398 files; maximum 96 remained unchanged. The single added registry row
is an architecture test; existing rows, classifications and findings are intact.

The observer reuses the qualified live session, keeps real parser-node/Symbol
identities and distinguishes local report indexes. Tracked modules and selected
unreferenced stubs retain their flags and loaded/read hashes. Native lexical
UTF-16 spans stay separate from raw alias declaration URI/range. Intrinsic dummy
ranges and a real augmented-assignment destination absent from the parsed-node
walk have explicit statuses; absence alone does not prove compiler generation.
Malformed native facts fail COV002, with same-Symbol repair and two independent
guard weakenings qualified. Complete authored bindings and dormant declarations
remain missing. The historical 14-path prototype is unchanged and unaccepted;
all six findings and complete architecture/scientific limits remain.

## Superseded declaration candidate disposition

The original candidate at `056e9f3c`, staged tree `18835a60`, was rejected and
retired from its worker checkout. Its recorded staged metric result failed CQ002: mean
complexity 15.43 to 15.83 across 335 to 348 files, with maximum 96 unchanged.
Health improved 39.35 to 39.41, but that did not waive the failed predicate.
Its historical record reports 156 source-only cases; no new cohort was run for
this disposition and no normal commit was accepted. Native bound tables did not
establish complete authored bindings, and alias target URIs could not be fused
with lexical spans. The checked canonical-session observer takes the smaller
route while keeping those capability gaps explicit.

The owner and parent verified that no current qualified mechanism imports or
requires this stack. All 13 added source/test files are our own candidate;
its only existing-file change adds eight ownership rows. Every original row,
other policy field and existing source remains exact. The parent matched both
index and working bytes to the recorded staged tree before cleanup. Remaining
capability gaps and the six findings are preserved independently of that source
candidate. No experimental source or raw diagnostic archive becomes delivered
or accepted merely to clear an uncommitted-change count.

The parent removed exactly those 13 candidate files and eight added rows,
restoring the existing policy byte for byte. Default cleanup removed their
consumed ignored diagnostics. That historical worker checkout is clean, and its
seven independent fixtures remain exact at 45,360 bytes. No existing source or
incoming work was discarded; these are disposition records, not preserved raw
reproducibility evidence.

## Source-only neutral numerical proof

The three-file symbolic proof is pushed at `5eddbf6` after normal commit/push
checks. Exact hosted run `38589126596` passed the two-commit submitted range:
six changed inputs, two affected Python sources, two reviewed sources and 369
retained records. Its quality step took 12 seconds, ran no pytest and uploaded
zero artifacts. Sixteen distinct controls qualified: the initial native closure passed
in 0.92 seconds and the remaining 15 in 6.16 seconds. After moving the actual
shared test provider into its support owner, only its origin/closure and runtime
trace consumers repeated, passing in 0.94 seconds. Three moved class AST hashes
and all 13 retained negative fixture input sets remained exact. Ruff and strict
typing passed. The initial metric failure was repaired without changing a gate:
final worker metrics across 395 to 397 files keep mean 14.93 and maximum 96,
while health improves 40.86 to 40.89. Only two simulation/test registry rows were
added; other metadata, five protected sources and seven fixtures are unchanged.

Native controls establish bounded float32/Boolean kinds, the actual primitive
overloads, concrete symbolic-provider result closure and wrong-kind/vendor/
mutable-surface rejection. Each generic bound has independent weakening.
The actual core expression and coefficient ASTs are anchored; a runtime recorder
checks all eight ordered operations and integer/float scalar kinds. Core bytes
remain SHA-256 `c4079b5d32cb05e701fcb89856a8b48066185bb5c470203e56f4785316461132`.
No device arithmetic or trajectory ran. Actual MLX carrier feasibility, aliases,
nonmutation, primitive purity and lawful provider fields remain unproved.
DEP004, all six findings and complete 37-rule COV002 remain open. The
[numerical boundary](numerical-boundaries.md) owns the constraints on live adoption.

## Reference parameter preservation

The pure reference-default extraction is checked and pushed at
`4c87409`, following the completed delegated scientific review. All 21 preserved
cases collect after genuine test-responsibility factoring, and strict typing
passes. Native metrics passed both worker parents at mean 15.22, maximum 96 and
health 39.91; parent commit/push checks also passed. Nine provenance controls
and two independent weakenings preserve the joined assertion's rejection.
Completed numerical cohorts were not replayed. Exact hosted run `38545182620`
passed with 23 changed inputs, 33 affected Python files, 21 reviewed sources and
91 import module/contract checks. Its quality step took 14 seconds, with no
pytest and zero artifacts. The [coverage report](quality-coverage.md)
owns remaining mechanism limits.

## Neuron-row reduction selectors

The 17-path selector component is delivered at `b2f4dfd`. Normal commit/push
checks and exact hosted run `38598083015` passed: 17 changed inputs, 113 affected
Python files, 30 import module/contract checks, 16 reviewed ownership sources
and 356 retained records. The hosted quality step took 20 seconds, ran no pytest
and uploaded zero artifacts. Eighty-two affected cases passed in 10.76 seconds;
only 12 genuinely changed native fixture cases repeated, passing in 11.02 seconds.

`NeuronRow` identifies global Connectome rows through reduction/audit ports;
local bucket positions remain integers. Borrowed tuples, duplicate/order/missing
behavior and existing scalar constructions remain unchanged. Six normalized
production ASTs, 73 original assertions and 14 exception contexts are preserved.
Eight actual inert-reader lookups cover both modes. Actual capture/fold/reduction
and context writing produce byte-identical old/new 62-field NPZ and JSON outputs:
SHA-256 `7ae35ee6571b5e474abe3fb86db7e350dbabe78e43d666cad8a059fdae17b7cd`
and `b7154f70536a48dc5b2305c6d759b1de61d013e6d224ce217950ddd56e200711`.
The actual batch-environment reader verifies the current source identities;
synthetic environment metadata does not establish hardware execution acceptance.
Fourteen exact registry-row deltas preserve other current policy. Five protected
sources and seven fixtures remain exact. No Metal trajectory was run; conversion
origin, aliases, VALUE001, six findings and full37 coverage remain unresolved.

## Native static type-consumer selection

The 12-path component is delivered at `dcf27bb` after normal incremental hooks.
Pinned TypeScript 5.9.3 dependency facts select changed modules and static type
consumers; ambient/global changes invalidate their native cohort. Compiler flags
have one owner, semantic checks receive the affected roots and syntax checks
receive changed files. Independently discovered inventory and source/compiler/
configuration/read hashes remain guarded. Missing, removed, nonliteral or
unsupported module scope and swallowed host-read failures fail COV002.

Fifty-one distinct controls qualify over 58 executions: the initial 46 yielded
40 passes and six failures in 23.810 seconds; six repaired failures passed in
8.878 seconds; five new guards and one genuinely changed control passed in
3.102 seconds. Original 24 assertion ASTs and seven exact ownership-row deltas
are checked independently. Worker metrics retain mean 14.93 and maximum 96
while health improves 40.86 to 40.96 across 395 to 402 files. Shared metadata,
364 other Python files, five protected sources and seven fixtures remain exact.
No parent test replay occurs. Computed provider acquisition, runtime/effect
resolution, complete architecture enforcement and scientific acceptance remain
unproved. The immediate diagnostic consumer completed before default cleanup.

## Canonical loaded-import observation

The five-path repair is delivered at `1dce138` after normal incremental hooks.
The shared parsed-import descriptor body is preserved under parameter substitution.
Non-forcing source readiness checks retain origin/hash accounting; tracked and
selected sources bind, while pending unrequested inputs remain lazy. This repairs
the false rejection of native-unreachable imports without a vendor-directory
exemption. Complete `active_imports` capability remains COV002.

Thirty-one distinct controls qualify. Twenty-four changed relocation controls
passed in 8.809 seconds; the repaired lazy-read/hash assertion and existing shared
type-driver control passed in 1.251 seconds. Unchanged controls were reused.
Strict checked JavaScript, native syntax, Ruff and Pyright pass. Worker metrics
improve mean 14.89 to 14.86 and health 41.05 to 41.13 across 398 to 400 files;
maximum 96 remains. Only the allocated test registry row is added; descriptor
predicates and shared metadata are independently checked. No query migration,
runtime/effect proof, full37 result or scientific acceptance is claimed.
Consumed diagnostics were removed before the clean handoff.

## Architecture-test performance profile

The user-requested diagnostic at `1dce138` runs only `tests/quality` in an
isolated checkout. One instrumented pass took 578.389 seconds (9m38s): 1,047
passed and two failed, over 1,049 cases. This is a profiled quality-suite result,
not a new ordinary full-suite time or an all-pass qualification. The previous
706-case quality selection took 370.26 summed test seconds; case count has
increased by 343. Profiling overhead is not separately measured. Application
and scientific suites were not run.

Python cProfile, per-test phases, 4,807 directly observed subprocesses and four
native Node CPU samples establish the bottleneck. Parent poll/select waits take
525.299 seconds, 90.8% of wall time. Setup/call/teardown totals are respectively
34.694, 540.744 and 0.363 seconds. Child lifetime categories below are diagnostic
attributions, not independent end-to-end runs or pure compiler-startup timings.

| Direct subprocess category | Count | Seconds |
| --- | ---: | ---: |
| Git commit/push, including hooks | 736 | 183.385 |
| Native compiler bridges | 256 | 96.333 |
| Pyright language server | 145 | 91.607 |
| Other Node/compiler commands | 139 | 52.756 |
| Metric analyzer | 69 | 34.259 |
| Pyright CLI | 64 | 33.353 |
| Other Git operations | 3,129 | 30.795 |
| Import Linter | 152 | 18.379 |
| Hook installation/invocation | 97 | 15.406 |

The three boundary matrix modules take 132.583 seconds and construct 49 hook
repositories with 145 commit attempts. Schema-policy cases start 49 language
servers totaling 22.154 seconds despite largely unchanged authored input.
Decoded-report corruption controls alone repeat six call observations (1.847
seconds), 15 partial observations (4.773 seconds) and eight native-impact
observations (3.534 seconds). CPU samples confirm compiler loading, parsing,
filesystem access and garbage collection; no single startup-only percentage or
prospective speedup is claimed.

A separate single complete changed-range gate over `b2f4dfd..1dce138` passed in
13.941 seconds: 16 changed inputs, ten affected Python files and no pytest.
Metrics take 10.107 seconds (72.5%); Python typing 1.264 seconds, native
TypeScript checking 0.860 seconds, native dependency selection 0.731 seconds,
six changed native syntax checks together 0.391 seconds, ownership 0.210 seconds,
and input/format/lint tasks together 0.136 seconds. It preserves nine affected
ownership reviews, 368 retained records and six findings. This range does not
activate application import-boundary evaluation; other ranges can take longer.
Nested metric Python processes are confirmed by source, not individually timed
by this parent-process tracer. The metric adapter launches Python/Radon for each
uncached blob and performs both native visitors.

The measured optimization targets are run-local immutable observations for
schema/decoded-data tests and batched native Radon calculation, preserving both
visitors, every per-file error, complete inventory arithmetic and CQ predicates.
Source/SDK/configuration/hash/lifecycle mutations still require independent
observations. Reusing a mutable repository or deleting integrity checks is not
the proposed repair. No performance optimization is yet delivered by this profile.

The first failure is a stale assertion expecting six contracts instead of the
actual ten; both success/contract predicates remain and its repaired case passes
in 0.26 seconds. An initial focused attempt failed before test execution because
the temporary parent directory was absent after cleanup; creating that parent
resolved setup. A format-only commit-hook failure was repaired without another
test run. The second failure is the disposed-session weakening fixture: after
removing the active guard, a later native binding guard rejects it. The test-only
repair is committed at `84d257d`; three affected controls pass in 1.039 seconds.
The normal lifecycle guard rejects before native access. Weakening admits the
same read into the real disposed Program/reader, then the retained scope guard
rejects; successful use of a disposed compiler is not claimed. The unregistered
read control and six untouched function ASTs remain. Strict typing, Ruff, native
metrics and worker/parent hooks pass; mean 14.85, maximum 96 and health 41.27
remain unchanged. Only the allocated test and its single fingerprint row change.
The full profiling cohort is not replayed. Raw profile/working-data consumers
are complete; normal cleanup expires their outputs. The profiling checkout is
clean and its seven independent fixtures remain exact at 45,360 bytes.

The combined delivery through `d14bc50` passed exact hosted run `38602758682`:
22 changed inputs, 15 affected Python files, 11 ownership reviews and 366 retained
records. The quality step took 21 seconds, ran no pytest and uploaded zero
artifacts. Every job step passed. This qualifies the delivered selector/import
components and test repairs within their stated limits; six findings and complete
37-rule enforcement remain unresolved.

## Application selection after broad checker removal

At `f3b02b3`, one requested application-only timing run passed 951 tests with 29
existing dependency warnings: 127.95 seconds reported by pytest and 128.73 seconds
wall time (2m09s). The fresh-proof-bundle integration consumer remains explicitly
excluded, as in the earlier measurement; scientific qualification is not run.
This measurement is not an automatic pre-commit test repeat.

The timing exposes residual compiler/source/guard-erasure exercises mixed into
unit/integration modules, including fan-in reader and input-storage port probes.
The marker component is integrated at `7fba34d`. Its 13 reviewed files exclude
109 checker cases while preserving all 88 original test/helper function bodies
and 101 assertions, including actual runtime, native tensor/alias/order and
scientific behavior cases. Exact declaration/binding fingerprints remain unchanged.
Those excluded cases account for 117.223 of 124.852 summed testcase seconds in
the saved measurement; the remaining 842 cases account for 7.629 seconds. These
are historical testcase sums, not a measured new wall time. The classification
consumer is complete. No manual test rerun was added.

The latest user correction requires one automatic affected-test invocation in
the commit hook and the same selection in CI. Push/manual gate stages do not
invoke pytest; parent fast-forward integration reuses the worker-tested commit.
This replaces the earlier CI-only interpretation. Routine selection excludes
reviewed checker exercises and the integration consumer requiring a fresh full
native proof bundle; neither full scientific qualification nor complete 37-rule
architecture acceptance is established.


## Automatic test boundaries and final metric-reuse slice

The automatic runner is delivered at `45146bc`. Its normal commit hook passes
static checks, one selected pytest command and cleanup. No manual pytest runs.
The recorded selection is 911 node identifiers: 842 application cases and 69
focused quality cases in 77 files. Successful child output was hidden by the hook,
so exact pass/skip totals and wall time are unavailable; no replay was added.
Mean complexity 14.85 and maximum 96 remain; health improves 41.27 to 41.31.
Parent adoption is a fast-forward; push executes static checks without pytest.
Native/process/resource consumers are not inferred from Python import edges;
changed behavior at those boundaries needs explicit focused test sources.

The final metric component adds the exact authored 0.1.1-to-0.1.2 patch and
qualified archive while preserving original source/patch lineage. Parent archive
inspection independently verifies all provenance hashes and the exact five
changed package paths: package metadata, numeric-fact storage, Git map injection
and two exports/type declarations. Nine discovery/calculation/comparison sources
remain byte exact; production/numerical source is untouched. Three focused cache
cases cover cold/warm/changed-blob reuse, identity invalidation/protocol and exact
rename/delete/merge-parent comparisons. They run through the mandatory hook,
with no separate manual pytest. The local fact cache does not establish arbitrary
external dependency integrity or full architecture coverage.

The initial staged metric check found a complexity regression in the expanded
archive-preservation proof and health 41.27 to 41.25. It was not waived. A
same-file helper attempt also failed the normal hook before pytest: complexity
14 to 18 and health 41.31 to 41.27. The bounded repair reuses existing archive
fixture construction and standard-library exact byte comparison (`shallow=False`)
for the composed final reconstruction and installed-source observation; both
archive stages keep independent source-name and hash checks. Hash, lineage,
source-name, patch-result, mismatch and error predicates remain required. Five
explicit guard-disabling exercises in the immediate consumer files are marked
out of routine selection without changing their bodies. Final hook/delivery
results are recorded in the wrap-up checkpoint after execution.

The numeric-fact component is committed at `c22e943` after its normal hook and
cleanup pass. Automatic tests succeed; 217 recorded node IDs and no remaining
failures are observed after cleanup. The preceding automatic invocation passed
210 cases and failed seven diagnostic fixtures, with 14 checker cases deselected
in 94.62 seconds. Those failures were canonical-tool inputs incorrectly resolved
from the temporary target repository. Provenance/package/lock now resolve from
the wrapper's own project; target Git inputs and numeric cache stay target-local.
The focused invalidation case changes the actual C# analysis manifest. Existing
diagnostic assertions are unchanged. No manual pytest or parent replay occurred.

Hosted run `38615309920` for `45146bc` passed static checks but exposed 17 setup
errors in the audit-transition fixture: its legacy reference commit existed only
in the local object store. It passed 894 cases, deselected 110 and took 43.81
pytest seconds. The repair changes only the fixture reference to published main
ancestor `8e90dc665b0c89616eacb4d62415970de955828d`. The reference source has the
same Git blob `416d049624204b34a3d674d371e5ad523da3654c` and SHA256
`56a9009c163cc31436775b0a357622f0035a846b3e84bbe92d641ef49e8c9a1e`.
All test bodies, assertions and production arithmetic remain unchanged. Its
automatic affected-test result is recorded after the corrective commit.

The published audit-fixture correction is delivered at `3bd3ffe`; its normal
affected-test hook and cleanup pass. Parent push runs static checks without a
pytest repeat. The final user amendment makes numerical score regressions
advisory at the project adapter boundary. It supersedes the suggested 0.01-point
tolerance and the prior complexity/health ratchet. Native qualified package bytes
and raw measurements/findings remain unchanged; malformed/unknown/empty failures
and tool/analysis errors remain blocking. Test, typing, architecture and scientific
predicates are unaffected. Per-function complexity review remains a proposal,
not implemented measurement or a required numerical threshold.

The advisory-policy component is delivered at `2140a61` after its normal hook,
automatic selected tests and cleanup pass. Its nine paths contain two actual
ownership-row changes. Two earlier hook attempts stopped on typing/formatting
before pytest; neither caused a test replay. The successful automatic invocation
selected 11 test targets; exact case count/time were hidden and were not recovered
by rerunning. Native measurements remain regression/passed-false with three CQ002
findings: mean 14.84 to 14.86, report-test file complexity 9 to 10 and diagnostic
file complexity 13 to 31. Maximum 96 remains; health/maintainability improve
41.31 to 41.34. The project annotation correctly marks these advisory/nonblocking.
Native 0.1.2 package, calculators, comparisons and provenance remain unchanged.
Parent adoption is a fast-forward; push performs no pytest.

The published audit correction passed exact hosted run `38621098579`: every job
step succeeds and the affected-check/test step takes 14 seconds. At the wrap-up
checkpoint, independent source inspection also verifies all five current frozen
hashes and byte identity of the seven fixtures against `79f62ad`, totaling
45,360 bytes. This is preservation evidence, not complete scientific acceptance.

Exact hosted run `38622709325` for `2140a61` passes every job step. The
affected-check/test step takes 116 seconds; this is a targeted quality-tool
change, not a new full application-suite benchmark. The full
37-rule analyzer still reports COV002 and six findings remain. No scientific
hold is released; no new simulator feature or numerical remedy is delivered.
