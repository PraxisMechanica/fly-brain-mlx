# Quality enforcement coverage

Audience: agents and maintainers. This records executable coverage, not an
application-wide architecture approval. [milestone.md](../../milestone.md)
owns the active work order and verification status.

## Current architecture result

**ANALYSIS FAILED — COV002: complete structural enforcement is not implemented.**
The strict catalog contains 37 rules. Native checks and five import contracts
cannot prove them all. Six recorded architecture/identifier findings remain.
No incomplete rule is treated as clean or inapplicable.

| Rules | Working mechanism and limit |
| --- | --- |
| OWN001–OWN006 | The reviewed registry/loader reconcile exact Python files, named declarations, binding sets and frozen provenance. Complete binding/type/effect classification and deterministic role placement remain missing. |
| DEP001 | Import Linter checks five configured domain/framework/role boundaries, including neutral observation ports and active session consumers. Fixtures cover aliases, type-only imports, re-exports and transitive paths. Other role boundaries and same-module interactions are not covered. |
| DEP002–DEP004 | Some forbidden paths fail existing contracts. Complete logical owner cycles, public-contract exports and resolved foreign symbol/type checks are missing. |
| DI001–DI004 | Strict typing checks declared signatures. Collaborator identity, hidden construction, ambient dependencies and lifecycle analysis are missing. |
| ROLE001–ROLE007 | Complete resolved call/control-flow, role, persistence and neutral-contract checks are missing. |
| STATE001–STATE003 | Bounded native call witnesses check seeded acquisition boundaries. Complete effect summaries and ownership/alias analysis are missing. |
| ISP001, OCP001, LSP001, VALUE001, COMP001, ERR001 | Type checking covers native structural compatibility. Complete consumer-capability, dispatch, unsupported implementation, identifier conversion, inheritance and failure-flow predicates are missing. |
| TYPE001 | Strict Pyright runs across configured application, tests and tools, using the recorded third-party typing limits. This does not resolve all architectural call/effect identities. |
| CODE001, STYLE001 | Ruff detects configured unused bindings/syntax failures and checks formatting. Named-declaration/binding reconciliation and frozen provenance guards are implemented. Complete contract/stub and semantic catalog coverage remain missing. |
| COV001 | Hook mode rejects unindexed Python/check inputs, including canonical policy and metric prerequisites. The loader rejects missing/changed file/declaration/binding inputs and frozen provenance. Source fixtures prove repair and weakening; complete semantic bindings, source languages, roles/resources and build variants still require coverage. |
| COV002 | Missing capabilities raise analysis failures in the bounded analyzer components. Complete required executable coverage/error analysis remains to be implemented and integrated. |
| COV003 | Both installed hooks call `just check` with full scans, no filename list and unconditional execution. Real fixtures exercise commit/push rejection. Hosted checks use the same command; required merge protection is not configured. |
| COV004 | Native import and metric fixtures exercise rejection and repair; hook probes exercise child-error propagation and staged-source handling. Transitive/always-run weakening is covered. Other predicates need their own negative, repaired, close, error and weakening cases. |

## Working mechanisms

The [shared commands](../../justfile) run Ruff formatting/lint, strict Pyright,
five Import Linter contracts, source-only quality tests, and staged/commit metric
regression checks. [Developer workflow](development.md) owns installation,
diagnostic output, and retention. This quality gate does not execute the complete
application or scientific suite.

The [ownership registry and loader](architecture-ownership.md) reject invalid
metadata, changed declarations/bindings, missing mappings, broken resource/export/
composition links, and changed frozen provenance. Discovery fails on separately
empty roots, parse failures, workspace escapes, and untraversed directory links.
Empty reconciliation findings do not establish structural compliance.

The native resolver uses the locked Pyright language server. It resolves named
definitions through aliases, re-exports, type-only references, captures, exact
Unicode coordinates, and limited unconditional callable aliases. Source/call
graphs keep resolved locations and hashes for transitive paths and owner-cycle
inputs. Broken tools/messages, unsupported or unresolved targets, and changed
source fail COV002. These witnesses do not prove complete generics, Any/Unknown,
overloads, implicit calls, runtime dispatch, alias ownership, control flow, or
effects. Structured native type export remains unintegrated.

The [semantic input schema](../../tools/architecture/semantic_policy_schema.py)
defines version 2 with required sections and the exact 37-rule/context
inventory. Validation compares native source/UTF-16 anchors, configuration,
artifact hashes/versions, and cross-record references against independent
observations and actual bytes. Unsupported languages/kinds and absent
observations fail COV002. `require_semantic_compliance()` always raises COV002:
validated records cannot manufacture missing analysis or executed predicates.
Actual global inventory and required gate integration remain incomplete.

The pinned metric package counts whole-file native Python decisions with a file
baseline. Its qualified aggregation preserves native decision weights and the
CQ001–CQ003 predicates. Provenance, source/qualified archives, and the authored
patch are canonical indexed inputs. Fixtures cover masked regressions, repair,
protocol/numeric errors, cache identities, and individual predicate/input
weakening. Health and maintainability share one heuristic; they are not
independent architecture evidence.

Current implementation boundaries include explicit clock injection, pure
comparison scoring, command composition, consumer-owned seeded acquisition,
immutable causal-audit transitions, typed reference digests, and injected
observation sessions. Their bounded checks preserve behavior within their tested
scope. Complete type/alias/effect/control-flow analysis and the remaining
architecture findings still require work; these boundaries grant no new
scientific acceptance.

## Remaining work

Maintain the reviewed inventory as source changes, complete remaining binding,
resource, effect, and composition coverage, and bind all 37 rules to it. Unknown
targets and absent mechanisms must fail separately from violations. Integrate
the complete analyzer into `just check`, prove each predicate, report existing
findings, and resolve authorized repairs before claiming full compliance or
returning to feature/numerical development.
