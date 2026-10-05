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

The retained [staged report](../evidence/code-quality/ci-1376e40/staged.json)
and [commit report](../evidence/code-quality/ci-1376e40/commits.json) pass all
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
| DEP001 | Import Linter checks three configured domain/framework boundaries, including aliases, type-only imports, re-exports and transitive paths. Other role boundaries and same-module interactions are not covered. |
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

## Definite application finding

`DI001 src/fly_brain/simulation/service.py:36`: `simulate` obtains its clock
from the concrete imported `time.perf_counter`; the clock is absent from its
injected collaborators. The strict contract requires a typed clock port.
The service's imported clock and six direct reads are visible even though
Ruff, Pyright and the three current import contracts pass.

Repair: inject a required `Callable[[], float]` into the service and supply
`perf_counter` in composition. Inspect the writer's timing dependency at the
same boundary; preserve timer units, result fields and all numerical operations.
Verify with a deterministic injected clock and existing application checks.
This report proposes the repair; it does not claim it is implemented.

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
