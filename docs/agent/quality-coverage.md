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
| Ruff formatting and lint | Changed Python sources; changed metric-bridge code receives Node syntax checking. These do not prove architecture. |
| Strict Pyright | Changed sources and affected dependents, with configured supporting context and recorded third-party typing limits. |
| Ten project import contracts | Production/reference and comparison/execution separation, a narrow scientific-calculation/workflow boundary, and existing observation/input consumers. Services and data contracts have no blanket implementation-type ban. |
| Protected scientific source identity | Exact five protected paths and reviewed hashes. Ordinary declaration/binding changes and historical strict findings do not block refactors. Indexed-source checks still account for required inputs. |
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
sources, and native import contracts evaluate affected source modules. Python
removals widen static scope conservatively; ordinary changes retain incremental
selection. The type checker loads supporting context without claiming complete
runtime or effect resolution. Component owners author focused tests and record
source/dependency identity. The commit hook automatically runs affected tests
and blocks failures before delivery; CI uses the same selection. Push/manual
stages and agents do not add separate test runs. Missing required tools, invalid source/configuration and omitted intended scope
still fail. Retiring unused modules no longer requires an experimental proof.

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

The [scientific source guard](architecture-ownership.md) uses the existing
compact manifest to protect five reviewed source identities. It rejects missing or changed
protected sources and an invalid protected inventory. Ordinary file declarations,
bindings and role labels are not automatic rejection conditions. The historical
registry/reconciliation APIs and their general predicates are removed.

## Removed analysis platform

The experimental semantic schema, role/resource predicates, language-server
transport, native compiler/type/call/partial/context projections, prototype graph
and purity witnesses are removed with their exclusive tests. The neutral numerical
provider experiment is also removed; the actual kernel-expression guard remains.
Small JSON test helpers and the useful comparison import contract are retained in
appropriate test/quality modules. There is no custom analyzer left to complete.

The remaining authored JavaScript is the metric bridge. Its changed source receives
`node --check`; its existing metric behavior tests remain. The self-referential
TypeScript/native-impact platform is removed. Standard Pyright checks Python.
Python module deletions/renames conservatively widen static type/import scope;
pytest still selects actual changed/affected behavior. Ordinary edits remain
incremental. This does not claim complete historical or dynamic dependency proof.

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
preserving the record and arrays. Reduction selectors carry global `NeuronRow`
identities while local bucket positions remain integers. The bounded behavior tests
and normal type checks remain; no SDK projection or complete ancestry proof is
required. These boundaries grant no new scientific acceptance.

## Maintenance scope

Maintain the reviewed inventory and meaningful source/import boundaries when
actual code changes. Preserve failure propagation and accurate affected-test
selection. Review practical responsibilities and scientific invariants under the
project architecture policy; repair demonstrated problems with focused checks.
The former task to bind every strict predicate into a universal analyzer is
retired. Its completion is not a prerequisite for handoff or scientific development.
