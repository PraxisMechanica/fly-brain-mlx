# Quality enforcement coverage

Audience: agents and maintainers. This records executable coverage, not an
application-wide architecture approval. [milestone.md](../../milestone.md)
owns the active work order and verification status.

## Current project coverage

The user's 2026-10-14 amendment replaces the generic strict profile with the
[project architecture policy](architecture-policy.md), which assesses all 37
rules separately. The required project gate provides the checks below; it does
not certify every semantic property of the application.

| Required mechanism | Practical scope and limit |
| --- | --- |
| Ruff formatting and lint | Changed Python sources; native syntax checks receive changed bridge files. These do not prove architecture. |
| Strict Pyright | Changed sources and affected dependents, with configured supporting context and recorded third-party typing limits. |
| Ten configured import contracts | Existing simulation/qualification/comparison and selected observation/input boundaries. They do not ban concrete MLX types inside the backend. |
| Reviewed ownership and source identity | Changed file/declaration/binding records, complete file inventory accounting and protected source hashes. Historical strict findings are reviewed under the current project policy. |
| Automatic affected tests | One invocation per commit and CI gate. Push/manual stages do not run tests. Native/process consumers still need explicit selection evidence where Python imports cannot prove consumption. |
| Native numerical metrics | Reuse per-blob calculations; report CQ001–CQ003 regressions as advisory. Invalid inputs/results or tool failures still block. |

A missing required tool, parse failure, invalid input, or unsupported affected
scope remains a blocking analysis error (`COV002`). An unfinished experimental
whole-program analyzer is no longer a required project mechanism. Its missing
capabilities therefore do not block refactor completion. Existing diagnostic
identifiers retain their actual meanings; no failure is converted to a false PASS.

Practical responsibility, reproducibility, state ownership, failure handling and
identity mapping also require focused source review and meaningful behavior tests.
Those review expectations are not advertised as complete automated proofs.
The former global **ANALYSIS FAILED — COV002** assessment described the retired
strict-analyzer objective, not a failed application test or the present acceptance
standard.

## Working mechanisms

The [shared commands](../../justfile) select changed inputs and affected
dependents. Ruff checks changed files, strict Pyright checks affected Python
sources, and native import contracts evaluate affected source modules. Native
bridge checks derive reverse static type consumers from pinned TypeScript
dependencies; changed ambient/global declarations invalidate their native cohort.
The compiler loads supporting context, while computed provider acquisition and
runtime/effect resolution remain unproved. Component owners author focused tests and record
source/dependency identity. The commit hook automatically runs affected tests
and blocks failures before delivery; CI uses the same selection. Push/manual
stages and agents do not add separate test runs. Unsupported Python deletion/rename
impact fails COV002, as do native removals without a proved affected scope.

Configured first-party forbidden targets must exist exactly in the native graph,
including when their source scope is inactive. The runner derives first-party
roots from its canonical packages and the declared session roots. It retains
source-presence checks, exact-root/descendant matching and optional absent
external packages. Missing configured first-party targets fail COV002; the
upstream framework's separate missing-target limitation remains recorded.

Commit metrics check the index. Push/hosted metrics check every submitted commit
and merge parent. Native numeric facts are reused per source blob across
commands, with implementation/runtime/configuration identity invalidation; full
inventories and aggregate comparisons still execute. This is calculation reuse,
not a persistent test or metric verdict cache. Cold or incompatible facts require
fresh calculation; malformed facts fail analysis.
The latest user amendment makes CQ001/CQ002/CQ003 numerical regressions advisory
in the project gate. Native findings/status/measurements remain visible; the
project policy annotation records that these findings do not block. Analysis,
protocol, source-input and coverage errors remain blocking. The native standalone
engine retains its qualified comparator; project aliases use the project policy.
This numeric policy is separate from the project architecture assessment;
scientific predicates and failures of adopted checks remain binding. The duplicate custom
health/maintainability score and whole-file complexity are not proof of quality.
Reliable per-function complexity review remains a proposed diagnostic improvement,
not an implemented gate or a numerical acceptance requirement. The native import-fact cache
is separate from a verdict and uses the verified source-tree identity; manual
or unindexed inputs use a fresh graph. [Developer workflow](development.md) owns
installation, diagnostics and exact output retention. The required gate does
not execute the complete application or scientific suite.

The [ownership registry and loader](architecture-ownership.md) reject invalid
metadata, changed declarations/bindings, missing mappings, broken resource/export/
composition links, and changed frozen provenance. Discovery fails on separately
empty roots, parse failures, workspace escapes, and untraversed directory links.
Empty reconciliation findings do not establish structural compliance.

## Experimental analysis inventory

The following native APIs and the semantic schema were developed for the former
strict objective. These are retained capability records, not a remaining task list.
Do not extend or integrate them merely to obtain a 37-rule certificate. Their
existing failures and limitations remain honest when they are explicitly invoked.
Required incremental checks above may reuse their bounded working components.

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
declaration, type, call, effect, control-flow or runtime-target verdict. The shared
live session supplies source-bound native reads, guards original/refreshed loaded
origins and rejects unregistered or post-disposal reads. Selected unreferenced
stubs receive native interim enrollment and forced binding; the actual Module,
scope, symbol table and original-file identity are checked. Tracking remains
unchanged and repeated reads retain cached file/tree identity. Loaded parsed
import descriptors share the checked native reachability guard. Non-forcing
readiness checks keep unrequested pending inputs lazy and preserve their origin/
hash accounting; complete `active_imports` capability remains missing. The
[native bound-declaration observer](../../tools/architecture/native_python_declarations.mjs)
retains actual parser-node and Symbol IDs, report-local scope/declaration indexes,
and native reachability. Raw declaration URI/range remain separate from lexical
UTF-16 spans. Intrinsic and unmatched native nodes are explicit. Dormant parsed
names can lack native bindings; complete authored bindings, parsed-name roles,
declaration payloads, alias resolution, types, calls, effects, control flow and
runtime targets remain missing. Enrollment and observation do not fill those
absent semantic capabilities.

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
proved runtime-environment equivalence. Complete authored declaration
reconciliation and reviewed live version 2 inputs would be dependencies of that
experimental analyzer, not of the current project refactor.

The [semantic input schema](../../tools/architecture/semantic_policy_schema.py)
defines version 2 with required sections and the exact 37-rule/context
inventory. Validation compares native source/UTF-16 anchors, configuration,
artifact hashes/versions, and cross-record references against independent
observations and actual bytes. Unsupported languages/kinds and absent
observations fail COV002. `require_semantic_compliance()` always raises COV002:
validated records cannot manufacture missing analysis or executed predicates.
The experimental full analyzer and its gate integration remain unimplemented;
neither is required by the current project policy.

## Current metric and application boundaries

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
actual NumPy dependency root. Reduction selectors now carry global `NeuronRow` identities through capture,
audit and provider ports; local bucket positions remain integers. Conversion-origin
and complete ancestry precision remain unproved; nominal wrappers do not establish
those predicates.
Their bounded checks preserve behavior within their tested scope. Complete
type/alias/effect/control-flow analysis remains unimplemented and outside the
required project scope. These boundaries grant no new scientific acceptance.

## Maintenance scope

Maintain the reviewed inventory and meaningful source/import boundaries when
actual code changes. Preserve failure propagation and accurate affected-test
selection. Review practical responsibilities and scientific invariants under the
project architecture policy; repair demonstrated problems with focused checks.
The former task to bind every strict predicate into a universal analyzer is
retired. Its completion is not a prerequisite for handoff or scientific development.
