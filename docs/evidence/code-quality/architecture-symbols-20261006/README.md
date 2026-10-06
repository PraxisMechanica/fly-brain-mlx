# Native semantic resolver and graph component

Decision confidence: 95% at base `0a313d02b56d886542d130134346506106a5f926`.
This bounded component implements source-only declaration, nominal-location,
explicit-call and graph foundations. Application code, scientific inputs,
reference semantics and existing evidence are outside its write scope.

Success criteria are exact native declaration identity through claimed aliases,
imports, annotations, captures and factory-result receivers; explicit immutable
source/type/call records; evidenced transitive paths and cycles; reconciled
source hashes; source-only rejection, repair, close, error and weakening cases;
and the installed canonical local checks before a coherent commit.

## API and evidence model

`tools.architecture.resolution.Resolver(root, sources, compiler)` accepts the
existing discovery records and an active `Compiler` context. `analyze()` returns
`SemanticModel`. The module-level `analyze(root, sources, compiler)` is equivalent.
The resolver imports no application module and uses the installed, locked
Pyright 1.1.414 language server. Compiler initialization now advertises standard
Go to Declaration support, so native definitions prefer source declarations;
type-definition responses remain native and can be ambiguous.

`symbols.py` defines `Location`, `Provenance`, `Symbol`, `Reference`, `Call`,
`NominalType`, `Capabilities` and `SemanticModel`. Locations use canonical
absolute paths, one-based lines, zero-based UTF-16 columns and exclusive ends.
Provenance includes the exact file SHA-256 and a repository path only for an
inventoried first-party file. Symbol equality includes its location and source
hash. Library and builtin identities use their exact native-selected source or
stub and bytes, without suffix-based effect classification.

The index retains identifier ranges and native-compatible parameter declaration
ranges, including defaults and variadic prefixes. AST UTF-8 byte offsets become
UTF-16 positions. Ordinary names and f-string expression names use exact AST
ranges. Attribute spans are validated against their source spelling, including
Python's identifier normalization. This positioning step does not infer type
identity. Native definition locations establish the referent.

`Reference` distinguishes reads, annotations, bases, imports and decorators.
Its capture flag records a native-resolved binding in an enclosing function;
it does not prove ownership, mutability or callback purity. `Call` records an
explicit lexical call to a native declaration. Constructor targets are class
declarations. Signature defaults belong to their enclosing definition scope.
Implicit constructor methods, descriptor calls and actual runtime dispatch are
not proved by this model.

Assigned callable aliases are supported only through one unconditional,
compiler-linked assignment per binding, with a simple name or attribute RHS.
Each link retains the native RHS referent and source location. Conditional,
reassigned, computed and factory-returned callable bindings fail COV002.
Files with global/nonlocal directives cannot use this narrow alias mechanism.
Alias cycles and chains deeper than 128 fail COV002. This is not full alias or
interprocedural data-flow analysis.

`Resolver.nominal_type(location)` returns one exact native class declaration.
It rejects missing, non-class and ambiguous type-definition results. It does
not return generic arguments, Any/Unknown classification, callable signatures,
selected overloads or a complete structured type. Pretty hover text is never
parsed to manufacture those facts.

`graph.source_graph(model)` adds explicit declaration-containment edges to the
native source references and callable-alias links. `graph.call_graph(model)`
uses explicit lexical calls. `Graph` provides shortest paths, forbidden-path
witnesses, iterative strongly connected components, one cycle witness per
cyclic component and complete group collapse. Edge evidence retains original
references/calls. Empty intended selections, absent nodes, dangling edges and
incomplete group mappings fail COV002. Owner, role and effect policy is a
separate integration input; no policy API or application file list is hardcoded.

## Verified scope and remaining coverage

The fixtures cover imported aliases, re-exports, TYPE_CHECKING imports,
same-module references, multi-link callable assignment aliases, protocol and
concrete captures, constructor targets, typed factory-result receivers, defaults,
fields, variadic parameters, Unicode/f-string positions and exact library
provenance. Graph fixtures include violating transitive concrete calls, repair
to a protocol, a close pure-value case, type-only paths and native call cycles.
Guard weakening accepts the same conditional alias, ambiguous method or stale
source response. Dropping transitive edges or a cycle edge loses the same graph
witness. Existing meaningful compiler/inventory fixtures are preserved.

Source discovery and required checks have separate reports. The existing
`just check` command verifies its configured native, import, quality-fixture and
metric gates; passing it does not certify the full 37-rule architecture catalog.
The complete semantic/application result remains **ANALYSIS FAILED (COV002)**.
See `scope.json` for the actual attempted whole-source scan and first failure.
No unsupported scope is silently marked clean or inapplicable.

`native-capability.json` records the actual server handshake, exact compiler
artifact hash, native location/hover samples and the -32601 response to the
proposed `pyright/typeInfo` request. This proves that request is unsupported by
the installed server and that the current adapter lacks a structured type
export. It does not deny the existence of Pyright's private evaluator internals.

A version-pinned, source-only native evaluator adapter must expose structured
type categories, Any/Unknown, unions, generic arguments, overload selections,
callable signatures, class hierarchies and declaration links. Separate alias
ownership, control-flow, implicit/dynamic calls and imports, and checked effect
summaries remain required. `model.capabilities.require(...)` raises COV002 for
these missing capabilities. Consumers must request every capability their rule
needs; nominal locations or declaration graphs cannot substitute for it.

## Integration and preservation

The parent owns policy joins, required whole-gate coverage, shared configuration,
application repairs and project status. This component changes only its resolver,
IR, graph, two fixture files and this evidence folder. Both native Git hooks are
installed. Shared `.venv` and `node_modules` remain read-only runtime symlinks.
Each focused/gate run uses a fresh retained pytest temporary directory. No
application startup, simulation, database lifecycle or scientific run is needed.
No branch, fetch, rebase or push belongs to this component's local handoff.
