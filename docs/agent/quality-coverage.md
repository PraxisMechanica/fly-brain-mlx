# Quality enforcement coverage

Audience: agents and maintainers. This records executable coverage, not an
application-wide architecture approval. [milestone.md](../../milestone.md)
owns the active work order and verification status.

## Current architecture result

**ANALYSIS FAILED — COV002: complete structural enforcement is not implemented.**
The strict catalog contains 37 rules. Native checks and ten import contracts
cannot prove them all. Recorded debt is described in
[source ownership](architecture-ownership.md).
No incomplete rule is treated as clean or inapplicable.

| Rules | Working mechanism and limit |
| --- | --- |
| OWN001 | The placement predicate checks domain bindings against exact owner roots and its explicitly reviewed outside role over independently validated version 2 inputs. Missing native identities, sources, hashes or relevant scope fail COV002. Whole live contexts and required gate integration remain missing. |
| OWN002–OWN006 | The reviewed registry/loader reconcile exact Python files, named declarations, binding sets and frozen provenance. Complete resource, binding/type/effect classification and role predicates remain missing. |
| DEP001 | Import Linter checks ten configured domain/framework/role boundaries, including neutral observation ports and active session consumers. Fixtures cover aliases, type-only imports, re-exports and transitive paths. Other role boundaries and same-module interactions are not covered. |
| DEP002–DEP004 | Some forbidden paths fail existing contracts. Complete logical owner cycles, public-contract exports and resolved foreign symbol/type checks are missing. |
| DI001–DI004 | Strict typing and bounded native facts expose declared/instantiated signatures and selected explicit calls. Complete collaborator/slot origins, hidden construction, ambient dependencies and lifecycle analysis are missing. |
| ROLE001–ROLE007 | Complete resolved call/control-flow, role, persistence and neutral-contract checks are missing. |
| STATE001–STATE003 | Bounded native call witnesses check seeded acquisition boundaries. Complete effect summaries and ownership/alias analysis are missing. |
| ISP001, OCP001, LSP001, VALUE001, COMP001, ERR001 | Type checking covers native structural compatibility. Complete consumer-capability, dispatch, unsupported implementation, identifier conversion, inheritance and failure-flow predicates are missing. |
| TYPE001 | Strict Pyright checks changed sources and affected dependents while loading their configured type context, using the recorded third-party typing limits. This does not resolve all architectural call/effect identities. |
| CODE001, STYLE001 | Ruff detects configured unused bindings/syntax failures and checks formatting. Named-declaration/binding reconciliation and frozen provenance guards are implemented. Complete contract/stub and semantic catalog coverage remain missing. |
| COV001 | Hook mode rejects unindexed Python/check inputs, including canonical policy and metric prerequisites. The loader rejects missing/changed file/declaration/binding inputs and frozen provenance. Source fixtures prove repair and weakening; complete semantic bindings, source languages, roles/resources and build variants still require coverage. |
| COV002 | Missing capabilities raise analysis failures in the bounded analyzer components. Complete required executable coverage/error analysis remains to be implemented and integrated. |
| COV003 | Commit, push and hosted checks use explicit stage modes. Changed sources and affected dependents receive static checks; component owners execute meaningful regressions once before commit. Global inventory and metric aggregates remain accounted for. Required merge protection is not configured. |
| COV004 | Native import and metric fixtures exercise rejection and repair; hook probes exercise child-error propagation and staged-source handling. Transitive paths, source selection and canonical-input weakening are covered. Other predicates need their own negative, repaired, close, error and weakening cases. |

## Working mechanisms

The [shared commands](../../justfile) select changed inputs and affected
dependents. Ruff checks changed files, strict Pyright checks affected Python
sources, and native import contracts evaluate affected source modules. Native
bridge checks load imported type context; complete reverse-consumer coverage
for those JavaScript sources remains unproved. Component owners run meaningful
regressions once before commit and record source/dependency identity. Hooks and
hosted checks do not replay those tests. Unsupported Python deletion/rename
impact fails COV002, as do native removals without a proved affected scope.

Configured first-party forbidden targets must exist exactly in the native graph,
including when their source scope is inactive. The runner derives first-party
roots from its canonical packages and the declared session roots. It retains
source-presence checks, exact-root/descendant matching and optional absent
external packages. Missing configured first-party targets fail COV002; the
upstream framework's separate missing-target limitation remains recorded.

Commit metrics check the index. Push/hosted metrics check every submitted commit
and merge parent, with native blob calculations reused within the command.
No persistent test or metric verdict cache is used. The native import-fact cache
is separate from a verdict and uses the verified source-tree identity; manual
or unindexed inputs use a fresh graph. [Developer workflow](development.md) owns
installation, diagnostics and exact output retention. The required gate does
not execute the complete application or scientific suite.

The [ownership registry and loader](architecture-ownership.md) reject invalid
metadata, changed declarations/bindings, missing mappings, broken resource/export/
composition links, and changed frozen provenance. Discovery fails on separately
empty roots, parse failures, workspace escapes, and untraversed directory links.
Empty reconciliation findings do not establish structural compliance.

The lexical resolver uses the locked Pyright language server. It resolves named
definitions through aliases, re-exports, type-only references, captures, exact
Unicode coordinates, and limited unconditional callable aliases. Its source/call
graphs retain located, hashed evidence. Lexical declarations do not establish
possible runtime dispatch targets.

The integrated [native type API](../../tools/architecture/native_types.py) uses
Pyright 1.1.414's evaluator to export immutable structured graphs for classes,
protocols, generics, unions, signatures and supported type variables, with exact
declaration and input identities. `require_precise` rejects Any/Unknown surfaces.
Unsupported projection forms, including ParamSpec/TypeVarTuple and recursive
shapes, fail COV002 rather than receiving a fabricated type. Actual bound import
records use native reachability: active unresolved/partial imports and invalid
native records fail with source-located COV002 after queries. Namespace-package
origins and unreachable version branches remain valid; loaded-file and actual
read hashes remain guarded. This does not prove computed imports, full ancestry
precision or equivalence of the manually supplied type context.

The [native call API](../../tools/architecture/native_calls.py) exports selected
signatures/overloads, receiver types, argument/result graph references and exact
UTF-16 ranges for explicit calls. Fixtures cover aliases, re-exports, captures,
inferred factory returns, methods, protocols, constructors, builtins and unpacked
argument expressions. Erased or ambiguous static signatures, missing artifacts
and changed inputs fail COV002. Unpacked expressions are not argument-to-parameter
expansion proof; protocol calls are not concrete dispatch proof.

The [checked JavaScript source API](../../tools/architecture/native_sources.py)
uses TypeScript 5.9.3 to reconcile bridge declarations, bindings, imports,
exports and actual input hashes. This bounded inventory does not supply complete
live JavaScript or authored C++ contexts to semantic-policy validation.

The [native Python context API](../../tools/architecture/native_python_context.py)
observes the actual pinned compiler configuration, complete source enumeration,
ordered import roots and loaded-source origins. It uses the native command-line
host and file system, reconciles discovery independently and hashes configuration,
request, compiler, bridge and read inputs. Shared editable dependency paths are
observed; runtime-environment equivalence is not established. It supplies no
binding, type, call, effect, control-flow or runtime-target verdict. The shared
live session provides source-bound reads, checks original and refreshed loaded
origins, and rejects unregistered or post-disposal reads. Selected but unreferenced
stubs may still lack native binding/parse results; complete enrollment is missing.

The [native partial API](../../tools/architecture/native_partials.py) exports
source-bound constructor and wrapped-expression identities, ordered captures,
native residual signatures and raw Any/ellipsis/gradual/error flags. Unsupported
unpack/residual forms and incomplete or changed provenance fail COV002. Native
conditional types may collapse targets; closure rebinding and keyword mutation
remain unproved. These are static facts, not origins or runtime/effect proof.

The [placement predicate](../../tools/architecture/ownership_placement.py) executes
OWN001 over independently validated domain bindings. It preserves coverage
failures separately from located placement findings; this does not make the
canonical live analyzer complete.

These components do not add absent capabilities to `SemanticModel`. Complete
callable/slot origins, partial dispatch, implicit calls, runtime target sets,
alias ownership, control flow and effect summaries remain missing. The existing
native type/call/partial setup still manually supplies strict rules and paths;
the new canonical context observations have not yet replaced those contexts or
proved runtime-environment equivalence. Declaration-only observation and reviewed
live version 2 inputs remain the next dependency.

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

Current implementation boundaries include explicit clock injection, injected
comparison scoring/coordinates/clock conversion/diagnostics, command composition,
consumer-owned seeded acquisition, immutable causal-audit transitions, typed
reference digests, branded Connectome/grouping arrays, Experiment/Stimulus
scalars, requested session/case and canonical batch trial labels, injected observation sessions, pure
reference parameters, consumer-owned connectome silencing and host mapping
readers used by the input audit and required grouping/count readers for fan-in
audits. Fan-in preparation precedes count acquisition; pure completion consumes
the returned array before grouping. Configured imports guard both analysis and
probe modules against mapping providers. The host audit separates pure rules and
orchestration from four repository operations behind required `InputAuditFiles`;
configured imports reject service/rule dependencies on its storage implementation.
Row-space coordinate validation and FlyWire-space
comparison/pooling now use separate constrained raster specializations while
preserving the record and arrays. Native type arguments are qualified with the
actual NumPy dependency root. Conversion-origin and complete ancestry precision
remain unproved; nominal wrappers do not establish those predicates.
Their bounded checks preserve behavior within their tested scope. Complete type/alias/effect/control-flow analysis and the remaining
architecture findings still require work; these boundaries grant no new
scientific acceptance.

## Remaining work

Maintain the reviewed inventory as source changes, complete remaining binding,
resource, effect, and composition coverage, and bind all 37 rules to it. Unknown
targets and absent mechanisms must fail separately from violations. Integrate
the complete analyzer into `just check`, prove each predicate, report existing
findings, and resolve authorized repairs before claiming full compliance or
returning to feature/numerical development.
