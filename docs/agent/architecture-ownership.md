# Reviewed Python ownership registry

Scope: combined parent source at
`90cc61b1aecd0a49844a901f3080b3989c421edd` plus the inactive observation-session
component and its canonical consumer controls. Parent reconciliation confidence: 95%. The original
worker record retains its `0a313d0` base and 90% classification confidence. This
registry records responsibilities; it does not certify application architecture
or change scientific behavior.

The intended outcome is a typed, deterministic input to the structural analyzer:
every retained first-party Python or stub file has an exact reviewed entry,
every named declaration has an owner and role, new bindings cannot inherit
permission without review, and unresolved classifications stay visible. Success
also requires source-only rejection, repair, nearby compliant and weakening
fixtures, strict typing, Ruff and the existing commit gate. The full 37-rule
result remains **ANALYSIS FAILED (COV002)**.

## Contract and coverage

[ownership.json](../../tools/architecture/ownership.json) has one explicit row
per file across `src`, `tests`, `tools`, `typings`, `main.py`, and `docs/evidence`.
The six roots drive discovery; they grant no owner, role, export or effect
permission. No folder-based classification, wildcard, exclusion, suppression,
generated-code exception or automatic classification runs in the build.

[policy.py](../../tools/architecture/policy.py) exposes:

- `load_policy(path) -> Policy`: reject duplicate JSON keys, invalid or unknown
  fields/types/roles/owners, empty scopes, non-exact paths, incompatible neutral
  export or composition records, resource-parent cycles, false database absence,
  and unowned identifier resources as `COV002` analysis failures.
- `review_policy(root, policy) -> Review`: discover and parse source without
  importing the application, check the reviewed sets, resolve exact metadata
  references, and return inventory-compatible `Ownership` records and exact
  `(path, name) -> Classification` mappings. Unmapped, absent or changed source
  classifications produce `COV001` findings.
- `declaration_fingerprint(declarations)` and `binding_fingerprint(tree)`: obtain
  review inputs after inspecting source. They are not an automatic policy repair.

`Review.findings` are executable reconciliation findings. `recorded_findings`
retain source-reviewed architecture debt, unresolved resource attribution and
primitive identifier contracts, with their current source locations. These two
streams and `limitations` must all be reported by the complete analyzer. Empty
reconciliation findings never mean a full architecture pass.

The named-declaration fingerprint preserves name, declaration kind and duplicate
occurrences. It includes named nested functions, class members, and module/class
assignments supplied by the existing inventory. It omits line numbers so that
moving unchanged declarations does not force reclassification. The separate
abstract syntax tree (AST) binding fingerprint tracks import targets and aliases,
parameters, stored/deleted names and attributes, global/nonlocal declarations,
exception names and pattern-binding names. New bindings fail review even if the
named production declarations have not changed. This is a conservative binding
set check. It does not resolve lambda/comprehension scopes, captured values,
call targets, alias ownership, control flow, error propagation or effects.

Historical source and the two adapted scientific references additionally require
exact source hashes. Ordinary active files are not content-frozen: changed
arithmetic with identical binding/declaration sets still needs the scientific
and semantic analyzers. The source-only fixtures demonstrate this limit
explicitly. Source changes during reconciliation fail `COV002`.

## Semantic decisions and open classifications

The three existing domain concepts are simulation, qualification and comparison.
They own their request/result values, rules, orchestration and storage adapters.
Application entrypoints, process composition, architecture tooling, quality gate
tooling, genuine cross-domain tests and handwritten third-party typing contracts
have distinct explicit owners. Domain tests keep the domain owner when their
subject is one domain; a foreign neutral value as input does not make a test a
new shared domain. Scientific comparisons between complete engines and shared
artifact fixtures have a declared system-test owner. Placement and all permitted
interactions still require the complete analyzer.

Exact declaration overrides record real mixed responsibilities. The completed
bootstrap repair now assembles commands rather than executing workflows, and
comparison scoring is owned by `comparison.metrics`. Only those two proven
mixed-role findings are removed. Their new ports, modules, commands and service
operations have exact reviewed entries. Qualification still contains independent
rules, storage, orchestration, device/framework adapters, local contracts and
neutral observations; it is not a whitelisted adapter tree. A role record does
not excuse incompatible co-location or implementation calls within a function.

Host NumPy arrays are numerical data. Calling a pure array operation or receiving
an array is not automatically a collaborator dependency. Frozen dataclasses do
not make all contained arrays, dictionaries or sets immutable. The detached
native-byte evidence for `ReductionRow` is stronger than the unproved alias
ownership of other records. That difference remains explicit.

MLX arrays in `Network`, `State`, `Layout` and `Execution` carry vendor device
representation; execution callbacks carry behavior. They are not neutral public
exports. Numerical transformations that also use streams or allocation need
resolved effect/ownership summaries and their scientific qualification before
adoption. No new arithmetic, representation, runtime mode or numerical remedy is
authorized by this registry. Local callable contracts using vendor types are
classified as ports so their leaks can be checked; their visibility does not
make them neutral contracts.

Public contracts enumerate exact value/port declarations and their named
members. They do not expose rule functions, repositories, services, device
implementations, constructors or the package's entire Python-visible namespace.
The complete resolver must follow aliases and re-exports back to those identities
and check neutral member types. Direct foreign pure-rule calls and writable
public aliases remain issues for that layer.

The authored simulation run, comparison report and qualification case are
independently operated workflows. Pinned input records, experiment/stimulus
artifacts and the simulation spike file are declared storage-only parts of the
simulation run: their source has no independent mutation service or endpoint.
Comparison imports a spike snapshot; it does not own the producing simulation
run. The actual reference builder has no independent public lifecycle or reuse
service: its compiled producer and fresh processes are qualification-case
runtime children. Native execution/state implement the simulation run. Their
`storage_only` relationships reflect these current operations, with reviewed
confidence 96% / 98%. Concrete access, lifetime, representation and scientific
adoption remain separate debt; this decision grants no boundary exemption.

FlyWire neuron identity, neuron-row identity, original edge-row identity and
trial identity have distinct meanings but currently cross neutral contracts as
unbranded integer/array values. The reference producer digest is an unbranded
string. They stay in the identifier registry with recorded `VALUE001` findings.
`ExperimentName` is an owned closed literal; `ParityCase` is a distinct compound
value. A time step, numerical dimension, ordinary count or numeric voltage is a
coordinate/fact, not an invented independent resource identifier.

The source inventory establishes no application database driver, object
relational mapper, database schema, SQL/table migration or HTTP route. Persistence
is CSV, Parquet, NumPy, JSON, tapes and scientific process/build files. The
command adapter is argparse; the Brian2 stdout stream is an observation protocol.
Exact supporting files are recorded in the responsibility absence records. The
external pre-commit SQLite cache is a tool-lifecycle responsibility, covered by
the standing non-production authorization. Missing query/call mechanisms remain
`COV002`; these absence decisions do not waive future unclassified source.

## Provenance and integration

All sixty retained evidence Python files are read and parsed as source, with
exact local hashes at the reviewed base. Their executed/interrupted verifiers,
independent scoring calculations, copied ledger and prospective prototypes keep
their real declaration ownership where the script contains domain algorithms.
They are handwritten historical source, not generated code. Resolving their old
imports/callers needs their historical revision/environment; current-tree
resolution failures cannot become a pass or an automatic exclusion.

The adapted Brian2/PyTorch reference records freeze the local source and name the
upstream commit, source path and original blob hash obtained from local Git.
They are first-party qualification references, not blanket vendor exemptions.
The Brian2/PyArrow stubs are handwritten, checked source contracts and have no
generator provenance. The separately pinned JavaScript metric tool's provenance
is outside this Python/stub registry; its existing native gate remains required.

The current parent integration reviews sixteen exact inactive-session
source/test changes. The subsequent typed-storage correction reviews eight
exact source/test rows and reconciles the combined inventory: 289 source/stub
files at that checkpoint. The subsequent RNG slice reconciles 299 source/stub
files, 4,078 declaration occurrences and 278 neutral exports. All 62 frozen
historical/reference records retain provenance. Reconciliation has zero gaps;
Eight architecture/identifier findings remain after the three proved RNG
acquisition repairs. Candidate neutral observation
values/ports and local assembly sites have exact entries; private helper
functions are not silently promoted to public contracts. The typed-storage
correction removes dynamic attribute/type shadowing and preserves array-facing
constructors and values. Private snapshots remain private; removed interception
members are no longer public exports. Historical/type/alias/effect coverage stays
incomplete until the complete analyzer is verified.

`ownership.json` is now a canonical indexed check input. Source-only controls
reject missing-index and ignored policy inputs, accept explicit staging, permit
nearby measurement JSON, and stop rejecting the same metadata defect when only
the policy input is omitted. They exercise the input guard; policy content and
full structural rules have their separate analyzers and limits.

The original worker fixtures and reports stay under
`docs/evidence/code-quality/architecture-ownership-20261006/`. The compact parent
record there is `parent-integration.json`; raw reconciliation and fixture reports
are retained outside Git. Parent owns subsequent reconciliation, complete rule
integration, project status/index updates and sequential remote delivery.

The committed resource review records actual exports/callers, scoped process
completion, source direction, immutable-observation limits and exclusive repair
footprints. Its proof is
`docs/evidence/code-quality/resource-ownership-review-20261006/parent-integration.json`.
The parent verified all 95 reviewed source hashes, corrected the prose's initial
declaration count from its raw manifest, updated the live registry assertion,
and passed 67 policy cases. The earlier ownership component evidence retains
its thirteen-finding checkpoint; neither snapshot certifies full architecture.
