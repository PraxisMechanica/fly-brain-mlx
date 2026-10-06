# Quality enforcement coverage

Audience: agents and maintainers. This records executable coverage, not an
application-wide clean-architecture approval. [milestone.md](../../milestone.md)
owns the active work order.

At `1376e40`, confidence **99%** that the published native/metric integration
works: [GitHub run 37328288754](https://github.com/PraxisMechanica/fly-brain-mlx/actions/runs/37328288754)
passes on Apple silicon, including bootstrap, both hook installation, the shared
command, and evidence upload. The earlier run passed its checks but failed
upload because hidden report paths were excluded. The corrected uploader
includes only `.quality-reports/*.json`.

The retained [staged report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/edfbb9dcfb477bf788740ca9096165518d21231a/docs/evidence/code-quality/ci-1376e40/staged.json)
and [commit report](https://github.com/PraxisMechanica/fly-brain-mlx/blob/edfbb9dcfb477bf788740ca9096165518d21231a/docs/evidence/code-quality/ci-1376e40/commits.json) pass all
three metric rules across nine comparisons. They cover 232 supported files /
25,207 nonblank lines, average/max complexity 5.37 / 28, and health /
maintainability 69.05 / 69.05. Health and maintainability use the same heuristic;
they are not independent architecture evidence.

## Current architecture result

**ANALYSIS FAILED — COV002: complete structural enforcement is not implemented.**
The strict catalog contains 37 rules. Native checks and four import contracts
cannot prove them all. No incomplete rule is treated as clean or inapplicable.

| Rules | Working mechanism and limit |
| --- | --- |
| OWN001–OWN006 | The reviewed registry/loader reconcile exact Python files, named declarations, binding sets and frozen provenance. Complete binding/type/effect classification and deterministic role placement remain missing. |
| DEP001 | Import Linter checks four configured domain/framework/role boundaries, including the qualification-owned observation port, aliases, type-only imports, re-exports and transitive paths. Other role boundaries and same-module interactions are not covered. |
| DEP002–DEP004 | Some forbidden paths fail existing contracts. Complete logical owner cycles, public-contract exports and resolved foreign symbol/type checks are missing. |
| DI001–DI004 | Strict typing checks declared signatures. Collaborator identity, hidden construction, ambient dependencies and lifecycle analysis are missing. |
| ROLE001–ROLE007 | Complete resolved call/control-flow, role, persistence and neutral-contract checks are missing. |
| STATE001–STATE003 | Effect summaries and ownership/alias analysis are missing. |
| ISP001, OCP001, LSP001, VALUE001, COMP001, ERR001 | Type checking covers native structural compatibility. Complete consumer-capability, dispatch, unsupported implementation, identifier, inheritance and failure-flow predicates are missing. |
| TYPE001 | Strict Pyright runs across configured application, tests and tools, using the recorded third-party typing limits. This does not resolve all architectural call/effect identities. |
| CODE001, STYLE001 | Ruff detects configured unused bindings/syntax failures and checks formatting. Named-declaration/binding reconciliation and frozen provenance guards are implemented. Complete historical-resolution, contract/stub and semantic catalog coverage remain missing. |
| COV001 | Hook mode rejects unindexed Python/check inputs, including the canonical policy. The loader rejects missing/changed file/declaration/binding inputs and frozen provenance. Source fixtures prove repair and weakening; complete semantic bindings, source languages, roles/resources and build variants still require coverage. |
| COV002 | This report names missing coverage. A complete required executable coverage/error analyzer remains to be implemented. |
| COV003 | Both installed hooks call `just check` with full scans, no filename list and unconditional execution. Real fixtures prove commit/push rejection. Hosted checks use the same command; required merge protection is not configured. |
| COV004 | Native import and metric fixtures prove rejection and repair; hook probes prove child-error propagation and staged-source handling. Transitive/always-run weakening is demonstrated. Other predicates need their own negative, repaired, close, error and weakening cases. |

## Repaired clock finding — 2026-10-06

The original `DI001 src/fly_brain/simulation/service.py:36` finding identified
six direct `time.perf_counter` reads in `simulate`. The service now requires a
`Callable[[], float]` clock. Its result writer requires the same typed clock;
bootstrap supplies `perf_counter` to both through explicit composition. Timer
units, timing/report fields, spike schemas, and numerical operations are unchanged.

At base `876cb157b403c6e65d96aa3d411ae8686988cf06`, eleven focused tests pass
with no failures or skips, and strict Pyright reports no errors or warnings.
The service test checks deterministic stage durations. The real-file writer
test checks its export duration and total elapsed time, alongside the existing
empty/populated spike-format checks. An in-memory ambient-clock control fails
the deterministic service assertion. Test outputs are retained in a fresh
`/private/tmp/fly-brain-clock-tests-20261006-01` directory.

This repairs the recorded clock dependency. It does not implement the missing
full structural analyzer or establish new scientific case acceptance.

## Actual reduction-row boundary — 2026-10-06

The causal writer now receives a qualification-owned `ReductionReader` rather
than discovering a private `Layout` in `partial.args`. The provider returns
actual device leaf identities/counts/occupied padding and the bound reduction
order through neutral values with detached immutable byte storage. This alone
does not prove complete metadata/alias immutability. The independent weight pairing
stays in qualification. Alias-only host-array contracts no longer import the
concrete backend. Concrete execution/state dependencies elsewhere remain open.

Eighteen native/value cases, seven real paired/repeat/batch/singleton cases, and
five real source-only commit-hook cases pass. The latter prove direct, aliased,
type-only, transitive, and re-export implementation rejection, repair to neutral
values, and loss of detection when the port scope is removed. Four original/new
reader comparisons preserve all 96 native arrays' dtype, shape, and bytes. This
is bounded forwarding/evidence preservation; the observer and ledger logic are
unchanged. No complete application architectural approval is claimed.

## Analyzer foundations — 2026-10-06

The executable Python inventory reconciles exact named declarations and file
hashes with supplied ownership records. It rejects missing/unmapped source,
blank ownership, absent mappings, changed frozen-source provenance, separately
empty roots, parse failures, workspace escapes, and untraversed directory links.
The resolver uses the locked native Pyright language server; real protocol
fixtures resolve aliases, re-exports, and type-only references to their defining
method. Broken tools/messages, unresolved symbols, and source changes fail COV002.

Forty-one source-only fixtures pass, including six real reconciliation mutations
and two native-resolution/framing guard mutations that lose detection when
weakened. Strict typing, formatting, and lint pass. Live discovery parses 249
Python/stub files and 3,332 named declarations, including sixty retained evidence
sources. The compact proof is in
`docs/evidence/code-quality/architecture-foundations-20261006/verification.json`.

These components do not yet classify every production symbol/export/resource or
provide a complete typed call, alias, effect, and control-flow model. The full
architecture result remains **ANALYSIS FAILED (COV002)**. Passing their fixtures
is not a whole-application architecture pass.

## Comparison rules and orchestration — 2026-10-06

`comparison.metrics` owns pure scoring and result construction.
`comparison.service` coordinates its typed reader and pure transformations;
acceptance/pooling import the rule module directly. Original scoring ASTs and
reader/preparation order are preserved. Seventy-nine focused behavior/file/CLI
cases and 81 exact original/new serialized fixture comparisons pass. A buffer
reuse test fails when a control reads both inputs before preparing the first.

The fourth native import contract protects acceptance, diagnostics, metrics and
pooling from service/schema/storage dependencies. Six real source-only hook
cases reject aliased/type-only/indirect/re-export paths, accept neutral values,
and lose detection when scope or transitivity is weakened. The proof is in
`docs/evidence/code-quality/comparison-rules-20261006/verification.json`.
This repairs the inspected role split and source graph; complete role/call/effect
and alias enforcement remains COV002.

## Metric predicate weakening — 2026-10-06

Three source-only cases measure the same actual staged regression, then reverse
each native metric rule in a fresh isolated copy. Each rule loses its diagnostic
while other rules retain theirs; equal snapshots and repaired/nearby source
pass. CQ002 retains the actual file path. The installed package is unchanged.
`docs/evidence/code-quality/metric-weakening-20261006/verification.json` records
the executed proof. Coupled health/maintainability formulas remain one heuristic.

## Composition boundaries — 2026-10-06

Bootstrap factories return typed owned command adapters without loading pinned
inputs or executing workflows. Domain services sequence input/probe/report
ports. Parent integration preserves configuration, pin/load/clock order and CLI
output/exit behavior; 150 focused behavior/file/CLI/boundary cases pass.

The first import contract also covers simulation input orchestration and the
new simulation/comparison ports and reporting service. Pure comparison rules
cannot reach reporting, commands or module assembly. Four native-hook controls
reject implementation dependencies, accept neutral repair, and lose rejection
when their exact source scope is removed. The initial duplicate-entry assertion
is repaired by selecting only the intended contract. Compact parent proof:
`docs/evidence/code-quality/composition-refactor-20261006/parent-integration.json`.
These source boundaries do not prove all role/call/effect rules; COV002 remains.

## Native semantic identities and graph witnesses — 2026-10-06

The reviewed native resolver links declarations through imports, re-exports,
type-only references, captures, exact Unicode coordinates and its explicitly
limited unconditional callable aliases. Source/call graphs retain resolved
locations and source hashes for transitive paths and owner-cycle inputs. Eight
source hashes and all 84 parent fixtures are verified; raw fixture output stays
outside Git. Compact proof:
`docs/evidence/code-quality/architecture-symbols-20261006/parent-integration.json`.

Nominal locations and explicit lexical calls do not prove complete generics,
Any/Unknown, overloads, implicit calls, runtime dispatch, alias ownership, control
flow or effects. Every required missing capability raises COV002. Structured
native evaluator export is a separate assigned follow-up; hover text is not a
substitute. Whole-application structural enforcement remains incomplete.

## Reviewed source ownership and policy inputs — 2026-10-06

The reviewed loader rejects duplicate/invalid metadata, changed declaration or
binding sets, missing mappings, broken resource/export/composition links and
changed frozen provenance. Source-only fixtures prove rejection, neutral repair,
close cases and detection loss when each guard is weakened. The canonical policy
requires indexing; untracked/ignored policy fails, staging repairs it, nearby
measurement JSON stays allowed and exact input weakening loses detection.
Seventy-six parent policy/index cases pass at the ownership checkpoint. Proof:
`docs/evidence/code-quality/architecture-ownership-20261006/parent-integration.json`.

The runtime-parent contract has two dedicated source cases; all sixty-seven
parent policy cases pass at the subsequent resource checkpoint. Proof:
`docs/evidence/code-quality/resource-ownership-review-20261006/parent-integration.json`.
[Source ownership](architecture-ownership.md) owns current classifications,
counts, exports, resource decisions, provenance and remaining debt. These guards
do not prove complete type/call/alias/effect/control-flow or historical analysis.

## Inactive observation-session consumers — 2026-10-06

The canonical import contract protects independent expectations, observation
orchestration, block values, simulation observation ports and neutral observations.
Five actual configured scopes reject implementation dependencies and accept
repair; alias/type-only/transitive/factory/re-export and weakening controls remain.
The first expanded fixture overwrote its own violating observations module;
that setup is repaired without changing the gate. Parent checks pass 106 real
Metal cases and 64 value/package/hook cases, retaining 27 upstream warnings.
Compact proof:
`docs/evidence/code-quality/qualification-session-boundary-20261006/parent-integration.json`.

The verified storage correction replaces type-shadowing interception with nine
frozen records, explicit private snapshot fields and 36 typed view properties.
Parent checks pass 106 Metal and 66 value/alias/package/canonical-port cases;
constructor signatures, 55 public values, 31 dtype outcomes and all 30 existing
fixture assertion ASTs are preserved. Compact proof:
`docs/evidence/code-quality/session-storage-transparency-20261006/parent-integration.json`.
The old collector remains active. Pinned transparency and four-trial memory,
all consumer migrations and complete alias/type/effect/control-flow enforcement
remain pending; this component is not an architecture or adoption certificate.

## Seeded acquisition and pure input transformations — 2026-10-06

Fresh uniform/permutation acquisition now occurs outside domain rules through
required consumer-owned typed ports. Services supply completed trial/mask/order
values to pure stimulus and fan-in transformations. Exact original seed lists,
draw sizes/order, immediate preparation, probabilities and mathematical bodies
are preserved. Parent verification passes 144 focused cases and 26 native
effect/canonical provider-boundary cases; 54 original/new records match all
fields. The integrated full pinned four-trial, 1,000-step stimulus preserves
complete event bytes and metadata. No device/scientific acceptance follows.

Resolved native definition/call witnesses reject effect aliases, re-exports,
wrappers, hidden defaults and constructors; unresolved callbacks/targets and
changed/empty/unmapped inputs fail COV002. Individual weakening controls lose
their own diagnostics. Four additional canonical consumer scopes reject the
concrete seeded provider, repair to neutral values and lose detection when
removed. Only three source-reviewed STATE001 findings are cleared. Full
type/alias/implicit-dispatch/control-flow coverage remains incomplete. Proof:
`docs/evidence/code-quality/seeded-input-boundary-20261006/parent-integration.json`.

## Remaining work

Maintain the reviewed inventory as source changes, complete all remaining
binding/resource/effect/composition coverage, and bind all 37 rules to it. Use the
resolved import graph and a type/call/alias layer for the missing predicates;
unknown targets and absent mechanisms must fail separately from violations.
Integrate the complete analyzer into `just check`, prove each new predicate,
report existing findings, and resolve authorized repairs before claiming full
compliance or returning to feature/numerical development.

The previous seven-check architecture release remains historical evidence for
its stated scope. It does not satisfy this newer complete checker contract.
