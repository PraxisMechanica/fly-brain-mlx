# MLX fly-brain milestones

Audience: agents. Updated 2026-10-14 (America/Los_Angeles).
This is the current work order. Project policy is in [AGENTS.md](AGENTS.md),
scientific requirements in the [numerical contract](docs/agent/numerical-contract.md),
and commands in the [developer workflow](docs/agent/development.md).

## Current task

Complete the rearchitecture/refactor and prepare a verified handoff to the prior
implementation agent. The user resumes this scope on 2026-10-13 after the
historical-record cleanup was delivered at
`79f62adee10b092fcaaaed0ea4043da3f5b9c415`. Decision confidence: 99%.

Completion requires the remaining architecture and dependency repairs, complete
applicable 37-rule enforcement without weakened predicates, current human/agent
documentation, meaningful preservation checks, small checked commits delivered
to `origin/main`, a clean tree and a concise ordered implementation handoff.
New simulator features, numerical remedies, the full scientific matrix and
performance work remain outside this agent's scope. Scientific runs are required
only when needed to verify a refactor. Full coverage and findings cannot receive
PASS while incomplete; configured component checks are separate evidence.

The latest user amendment on 2026-10-13 prioritizes eliminating duplicate test
runs. Static architecture analysis must run only for changed source and affected
dependencies; reuse unchanged verification rather than repeating a full scan or
the complete checker regression suite at each worker, commit, push and hosted
boundary. This supersedes the previous unconditional full-snapshot workflow.
The checked workflow now uses that model. Preserve exact predicates, complete
source discovery, changed-input invalidation and honest coverage; incremental
results do not establish missing 37-rule mechanisms. Component owners retain
source/dependency evidence and run meaningful regressions once; repeat only
changed or failed controls. Automatic regression scheduling and a persistent
metric verdict cache are outside the minimum solution.

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

The parent owns shared policy, canonical commands/configuration, retention,
documentation and serial integration. Recovery is complete. The same worker
owners use isolated execution checkouts and commit verified components before
handoff: `architecture_symbols` owns native type/call/source facts;
`architecture_ownership` owns the neutral import boundary and allocated placement
predicate; `composition_refactor` owns coordinated simulation identifiers.
Shared registry changes are merged by exact row deltas; only the parent pushes.

Output policy belongs to [AGENTS.md](AGENTS.md); diagnostic commands belong to
[developer workflow](docs/agent/development.md). The
[retention manifest](tools/code_quality/retention.json) owns exact consumers and
release conditions. Keep it current before a verification output crosses a
commit boundary.

Historical execution records, generated outputs, archived verification scripts,
review logs and handoff histories have been removed. Seven independently
recorded regression fixtures remain as current test data under
`tests/data/reference`, totaling 45,360 bytes. Their manifest names the exact
current consumer and release condition. All seven bytes/hash identities were
preserved during relocation; production/reference arithmetic is unchanged.
Five current reference/oracle sources have reviewed hash guards. The pure
parameter factory is extracted exactly from the original Torch reference; its
remaining numerical declarations retain their original syntax. The Brian2 and
two legacy MLX oracles remain byte exact. Pinned FlyWire inputs and licences
remain intact. The native import-fact cache has an active operational exception
in the retention manifest; no scientific run output is retained.

Success requires:

- Complete applicable 37-rule analysis and rejection fixtures, required gate
  integration, and resolution of the authorized architecture findings. Missing
  capabilities remain an analysis failure.
- Preserve pinned inputs, reviewed reference/oracle lineage, the seven independent
  regression fixtures, scientific predicates, numerical behavior and output contracts.
- Keep human usage in `README.md` and current agent contracts in the indexed
  agent documents, with one owner per fact and valid destinations.
- Integrate committed worker components serially, then pass meaningful behavior
  and native preservation checks plus commit, push and exact-revision hosted
  checks. Deliver small coherent commits to `origin/main`.
- Finish all refactor assignments, leave a clean tree with no expired output
  exception, and hand off a concise ordered implementation plan with verified
  limits. Full scientific implementation remains with the prior agent.

## Current refactor evidence

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
unchanged. Selected, unreferenced stubs remain natively unbound; this is not
complete declaration enrollment. The historical declaration candidate remains
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

## Remaining order and unresolved decisions

Current bounded assignments (confidence 95%): B qualifies selected-source
enrollment through the pinned native interim-registration/binder APIs and checked
canonical live session. The historical 14-path declaration tree remains
unaccepted; dormant occurrences and lexical-versus-resolved identities must stay
explicit. A assesses the remaining absolute-count mapping seam and late
acquisition/pure-rule separation. Grouping injection is delivered and cannot
alone establish a complete module guard.
C assesses `NetworkCase` neuron-row selector tuples and their actual producers;
canonical batch labels are delivered. Local array positions, collectors, digest
streams and original numeric behavior remain unchanged. Positional artifact
provenance and joint stimulus-identity enforcement remain missing. Owners use separate main execution checkouts,
qualify affected controls once and commit before serial parent integration.

1. Keep checked components and current documentation delivered incrementally.
   Verify exact hosted revisions and leave no expired output exception.
2. Complete native declaration-only observation and reviewed live version 2
   contexts. A source-only prototype observes 314 worker sources, but raw native
   binding tables omit dormant declarations and mix import target URIs with
   lexical ranges. Reconcile every authored occurrence; do not invent identities.
   Canonical configuration, native command-line host/file-system behavior,
   complete source enumeration and loaded-source origins are observed at
   `39c4556`. Replace manual downstream contexts with those verified facts;
   runtime-environment equivalence and complete live analysis remain unproved.
3. Continue wider provider-role separation after the checked pure parameter and
   private `torch_setup` mapping repairs. The selected parity path's experiment
   lookup, neuron mapping, stimulus storage and connectome silencing now use
   consumer-owned services; preserve both catalog-read positions, seed 20261004,
   generation/persistence/silencing order and errors.
4. Complete callable/slot origins, implicit calls, runtime targets, source/export
   predicates, injection/lifetime checks, control flow/failure disposition and
   alias/effect closure. Bind every applicable rule into the required gate with
   independent rejection, repair, nearby-compliant and weakening controls.
5. Verify source-preserving structural repairs before the dependent inner repairs,
   complete all authorized refactor verification, and prepare the ordered handoff
   to `[Fly Brain] implementation`. That chat is idle; no message has been sent.

A fresh scientific review found complete model/provider separation incompatible
with the exact four-source freeze. The [reviewed boundaries](docs/agent/numerical-boundaries.md)
identify affected symbols, the minimum repair and preservation requirements.
The prior requirement for a separate human freeze amendment was an overbroad
interpretation. The authorized refactor can reclassify a reviewed source revision
only after preserving scientific behavior, independent lineage and every actual
source-identity consumer. Current hashes remain enforced until that specific
repair is checked; no numerical remedy, new execution mode or rule deviation is
approved. The pure reference-default extraction is checked and pushed at
`4c87409`, following the completed delegated scientific review. All 21 preserved
cases collect after genuine test-responsibility factoring, and strict typing
passes. Native metrics passed both worker parents at mean 15.22, maximum 96 and
health 39.91; parent commit/push checks also passed. Nine provenance controls
and two independent weakenings preserve the joined assertion's rejection.
Completed numerical cohorts were not replayed. Exact hosted run `38545182620`
passed with 23 changed inputs, 33 affected Python files, 21 reviewed sources and
91 import module/contract checks. Its quality step took 14 seconds, with no
pytest and zero artifacts. The [coverage report](docs/agent/quality-coverage.md)
owns remaining mechanism limits.

## Current scientific scope

Run the pinned FlyWire v783 leaky integrate-and-fire model on Apple silicon,
using MLX and uv. Brian2 and PyTorch are independent qualification references.
Preserve model equations, input identity, experiment definitions, native state,
events, queues and spike formats. Keep compilation and alternative arithmetic
modes subject to their explicit qualification requirements.

Numerical development remains on hold until the complete 37-rule architecture
enforcement is implemented, verified and accepted. This cleanup does not release
that hold.

The complete 52-case matrix and prescribed sugar/P9 four-trial comparisons are
not complete. Removed historical records do not establish current source or
execution-mode acceptance. Any new qualification must produce complete fresh
working data and satisfy every unchanged scientific gate before cleanup.
Future reference reuse needs verified input/source/build identity and complete
native equivalence; retain no archive simply in anticipation of possible reuse.

## Current architecture scope

Complete 37-rule structural enforcement remains **ANALYSIS FAILED (COV002)**.
Six recorded architecture/identifier findings remain. Strict typing, eight
import contracts, source ownership reconciliation and qualified native metric
checks are useful components, not a full structural or scientific approval.
Current coverage is in [quality-coverage.md](docs/agent/quality-coverage.md) and
classifications in [architecture-ownership.md](docs/agent/architecture-ownership.md).
