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
The strict catalog contains 37 rules. Native checks and three import contracts
cannot prove them all. No incomplete rule is treated as clean or inapplicable.

| Rules | Working mechanism and limit |
| --- | --- |
| OWN001–OWN006 | Domain roots are documented. Complete file/symbol/resource role classification and deterministic placement checks are missing. |
| DEP001 | Import Linter checks three configured domain/framework boundaries, including the qualification-owned observation port, aliases, type-only imports, re-exports and transitive paths. Other role boundaries and same-module interactions are not covered. |
| DEP002–DEP004 | Some forbidden paths fail existing contracts. Complete logical owner cycles, public-contract exports and resolved foreign symbol/type checks are missing. |
| DI001–DI004 | Strict typing checks declared signatures. Collaborator identity, hidden construction, ambient dependencies and lifecycle analysis are missing. |
| ROLE001–ROLE007 | Complete resolved call/control-flow, role, persistence and neutral-contract checks are missing. |
| STATE001–STATE003 | Effect summaries and ownership/alias analysis are missing. |
| ISP001, OCP001, LSP001, VALUE001, COMP001, ERR001 | Type checking covers native structural compatibility. Complete consumer-capability, dispatch, unsupported implementation, identifier, inheritance and failure-flow predicates are missing. |
| TYPE001 | Strict Pyright runs across configured application, tests and tools, using the recorded third-party typing limits. This does not resolve all architectural call/effect identities. |
| CODE001, STYLE001 | Ruff detects configured unused bindings/syntax failures and checks formatting. Full ownership reconciliation, archived-source provenance and contract/stub scope still need catalog analysis. |
| COV001 | Hook mode rejects unindexed configured Python/check inputs. Eight source-only Git fixtures cover untracked/ignored source and stubs, staging repairs, nearby evidence, and guard weakening with a controlled downstream metric. Complete symbol, role, resource and build-variant reconciliation is missing. |
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
order through neutral immutable values. The independent reference-weight pairing
stays in qualification. Alias-only host-array contracts no longer import the
concrete backend. Concrete execution/state dependencies elsewhere remain open.

Eighteen native/value cases, seven real paired/repeat/batch/singleton cases, and
five real source-only commit-hook cases pass. The latter prove direct, aliased,
type-only, transitive, and re-export implementation rejection, repair to neutral
values, and loss of detection when the port scope is removed. Four original/new
reader comparisons preserve all 96 native arrays' dtype, shape, and bytes. This
is bounded forwarding/evidence preservation; the observer and ledger logic are
unchanged. No complete application architectural approval is claimed.

## Remaining work

Inventory every first-party file, declaration, owned resource, public export,
effect and composition site. Bind all 37 rules to that inventory. Use the
resolved import graph and a type/call/alias layer for the missing predicates;
unknown targets and absent mechanisms must fail separately from violations.
Integrate the complete analyzer into `just check`, prove each new predicate,
report existing findings, and resolve authorized repairs before claiming full
compliance or returning to feature/numerical development.

The previous seven-check architecture release remains historical evidence for
its stated scope. It does not satisfy this newer complete checker contract.
