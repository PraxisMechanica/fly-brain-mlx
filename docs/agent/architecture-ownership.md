# Reviewed Python ownership registry

This registry records current source responsibilities. It does not certify
application architecture or change scientific behavior. The user's 2026-10-14
amendment and [project architecture policy](architecture-policy.md) supersede the
strict-profile requirements discussed below. Historical recorded findings and
incomplete alias/effect proofs are not present refactor acceptance blockers.
The source inventory and protected-hash checks remain active.

The intended outcome is a typed, deterministic input to the structural analyzer:
every retained first-party Python or stub file has an exact reviewed entry,
every named declaration has an owner and role, new bindings cannot inherit
permission without review, and unresolved classifications stay visible. Historical
qualification included source-only rejection, repair, nearby compliant and weakening
fixtures, strict typing, Ruff and the commit gate. Current changes use the developer
workflow verification scope. The experimental full 37-rule result remains
incomplete; completing it is outside the current project scope.

## Registry mechanics and historical strict scope

[ownership.json](../../tools/architecture/ownership.json) has one explicit row
per file across `src`, `tests`, `tools`, `typings`, and `main.py`.
The five roots drive discovery; they grant no owner, role, export or effect
permission. No folder-based classification, wildcard, exclusion, suppression,
generated-code exception or automatic classification runs in the build.

[policy.py](../../tools/architecture/policy.py) owns metadata loading and
fingerprints. [policy_review.py](../../tools/architecture/policy_review.py) owns
source reconciliation:

- `load_policy(path) -> Policy`: reject duplicate JSON keys, invalid or unknown
  fields/types/roles/owners, empty scopes, non-exact paths, incompatible neutral
  export or composition records, resource-parent cycles, false database absence,
  and unowned identifier resources as `COV002` analysis failures.
- `review_policy(root, policy, source_scope=...) -> Review`: discover and parse source without
  importing the application, check the reviewed sets, resolve exact metadata
  references, and return inventory-compatible `Ownership` records and exact
  `(path, name) -> Classification` mappings. Unmapped, absent or changed source
  classifications produce `COV001` findings. An optional exact source scope
  validates changed sources while accounting for the complete file inventory;
  unchanged source classifications retain their reviewed baseline.
- `declaration_fingerprint(declarations)` and `binding_fingerprint(tree)`: obtain
  review inputs after inspecting source. They are not an automatic policy repair.

The [developer workflow](development.md) owns integration check selection.
The historical unconditional full reconciliation instruction is retired; scoped
reconciliation does not waive incomplete semantic analysis.

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

The two current test oracles, adapted Brian2/Torch references and extracted pure
reference-parameter factory additionally require exact reviewed source hashes.
Ordinary active files are not content-frozen: changed arithmetic with identical binding/declaration sets still needs the scientific
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

Exact declaration overrides record real mixed responsibilities. Bootstrap
assembles commands, and comparison scoring belongs to `comparison.metrics`.
Ports, modules, commands and service operations have exact reviewed entries.
Qualification contains independent rules, storage, orchestration,
device/framework adapters, local contracts and
neutral observations; it is not a whitelisted adapter tree. A role record does
not excuse incompatible co-location or implementation calls within a function.

Host NumPy arrays are numerical data. Calling a pure array operation or receiving
an array is not automatically a collaborator dependency. Frozen dataclasses do
not make all contained arrays, dictionaries or sets immutable. `ReductionRow`
uses detached native-byte storage; alias ownership of other records remains
unproved.

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
`storage_only` relationships reflect these current operations. Concrete access,
lifetime, representation and scientific adoption remain separate debt; this
decision grants no boundary exemption.

FlyWire neuron identity, neuron-row identity, original edge-row identity and
trial identity have distinct meanings. Connectome FlyWire IDs and neuron rows,
grouped original edge rows, and bucket neuron/padded-edge rows now use the existing
simulation-owned array brands. Their lawful producer and constructor boundaries
retain the same objects, array bytes and numerical operations. Experiment FlyWire
scalars, stimulus neuron rows, requested observation-session labels and
`ParityCase.trial`, the four `NetworkCase` selectors and Torch qualification
setup/observation targets use the existing owned scalar brands. Catalog, validated
option and persisted-stimulus ingress retain their existing values and guards;
ordinary steps/counts and local reference array positions remain coordinates.
Rasters and complete lawful-conversion origins remain unproved. The four
simulation `VALUE001` records remain historical strict-profile observations;
current policy does not require generic conversion-origin proof.
The reference producer digest uses qualification-owned
`ReferenceProducerDigest`. Native typing rejects primitive and foreign-brand
consumers; explicit rebranding and complete conversion-origin enforcement remain
unproved.
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

## Current provenance and limits

Five current sources have frozen hashes: the adapted Brian2/PyTorch references,
`qualification/reference_parameters.py`, and
`tests/support/legacy_mlx_observer.py` / `tests/support/legacy_mlx_ledger.py`.
The parameter factory is extracted exactly; the residual Torch source retains
its numerical declarations and original lineage. Both current pieces have
separate hash guards and are included in actual source-identity consumers. The
two legacy MLX sources remain independent observation-session test oracles. They are checked first-party source, with
their exact provenance in the registry.

The adapted Brian2/PyTorch reference records freeze the local source and name the
upstream commit, source path and original blob hash obtained from local Git.
They are first-party qualification references, not blanket vendor exemptions.
The [numerical boundary review](numerical-boundaries.md) records the conflict
between permanent byte identity and complete model/provider separation. It also
records the correction: authorized structural repairs may reclassify the reviewed
source revision after preservation and identity checks. No rule deviation or
numerical change is granted.
The Brian2/PyArrow stubs are handwritten, checked source contracts and have no
generator provenance. The separately pinned JavaScript metric tool's provenance
is outside this Python/stub registry; its existing native gate remains required.

The strict registry retains six historical observations: the concrete `Advance`
callback, framework/model definitions in `TorchModel`, and four primitive-identity
records. Their project dispositions are in the architecture policy. The first two
are accepted project structures; the latter four do not demonstrate incorrect
mapping or arithmetic. Do not implement wrappers or reorder scientific code just
to remove these records. Actual invalid mappings, unintended aliases and failure
loss still require a focused repair when observed.

`ownership.json` is a canonical indexed check input. Source-only controls
reject missing-index and ignored policy inputs, accept explicit staging, permit
nearby measurement JSON, and stop rejecting the same metadata defect when only
the policy input is omitted. They exercise the input guard; policy content and
full structural rules have their separate analyzers and limits.
