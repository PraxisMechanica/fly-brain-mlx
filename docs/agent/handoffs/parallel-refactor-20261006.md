# Parallel refactor assignments — 2026-10-06

The user explicitly requested bounded parallel work and committed handoffs.
Decision confidence: 97% at 0a313d02b56d886542d130134346506106a5f926.
All three implementation agents inherit GPT-6.1 Sol at xhigh.

Each worker uses an independent local-main clone pinned to that commit. The
clones share installed dependencies read-only, have separate Git metadata and
pre-commit caches, and retain their source/evidence. No feature branch or
competing origin/main push is created. The parent integrates and pushes serially.

## Initial assignments at 0a313d0

| Agent | Component | Exclusive file scope |
| --- | --- | --- |
| architecture_ownership | Reviewed owners/roles, binding fingerprints, resources/public exports and typed metadata loader | New tools/architecture/policy.py, compact ownership metadata, its dedicated test, ownership evidence and optional architecture-ownership.md |
| architecture_symbols | Native symbol/type-definition/call relationships, alias handling and graph primitives | New symbols/graph modules and dedicated tests; compiler.py/compiler tests only if needed; symbol evidence |
| composition_refactor | Separate bootstrap assembly from owned runtime use cases; preserve lazy imports, configuration, load/clock boundaries and CLI behavior | bootstrap.py, cli.py; owned module/ports/commands/input-service wiring; qualification/service.py if needed; neutral qualification ports; composition/package tests and the narrow test_parity_options.py seam update; composition evidence |

The parent exclusively owns shared pyproject/justfile/hook/workflow configuration,
AGENTS.md, milestone.md, quality-coverage.md, the agent index, integration and the
current comparison rule repair. No worker edits another worker's files. Workers
request a parent allocation before expanding file scope.

Ownership metadata and native semantic IR have no unpublished API dependency:
metadata uses the existing inventory records; native IR emits explicit locations
and generic graph relationships. The parent joins them and implements the full
rule/gate integration. Composition changes application declarations; reconcile
its final committed symbols and public contracts into the ownership registry
at integration. Do not guess future declarations or register broad exemptions.

Each worker must install required hooks, run focused checks plus the existing
shared gate, and commit coherent verified changes before handoff. It returns
SHAs, exact files, actual commands/results, coverage limits, and integration
requirements. No hook bypass, dependency installation, push, rebase, branch
creation, scientific mode change or full-matrix execution is assigned.

The parent reviews each committed diff and evidence, imports the commit without
bypassing mandatory commit checks, reconciles shared metadata/configuration,
checks the combined snapshot, and pushes to origin/main in sequence. Native
resolution limits and missing applicable mechanisms remain COV002; green
component checks do not establish all 37 rules or new scientific acceptance.

## Initial handoff checkpoint at 471ab69

At parent `471ab69`, composition worker commit `05dd220` is integrated and pushed
with both hooks and 150 parent behavior/boundary cases passing. Native resolver
worker commit `ffbc2fe` passes 84 parent source fixtures and is being integrated.
Ownership worker commit `d6e8d43` remains preserved for the next serial join.

## Current integration and assignments

At `f2de8f01a2e5311a94ac4e520572925d23ce6f78`, all original worker components
are integrated: composition at `471ab69`, native identities/graphs at `a9453aa`,
reviewed ownership at `c5296da`, runtime-parent decisions at `f2de8f0`. Each passed
native commit/push hooks and its configured hosted job. Resource review `3613b96`
is complete. Documentation audit `e48aa9e` is a committed read-only handoff;
the parent implements its six-document corrections.

Implementation settings remain inherited GPT-6.1 Sol at xhigh. The accepted
scientific review stays with its existing fresh-context GPT-6 Astra reviewer.
Unmerged native-type and session results remain provisional; no collector
adoption or case acceptance follows from worker progress messages.

| Owner | Current bounded component | Exclusive scope and finishing condition |
| --- | --- | --- |
| architecture_symbols | Native structured types | New native_types.py, native_types.mjs, native_types_node.d.ts, dedicated fixtures and compact evidence. Preserve committed resolver files; check native categories/signatures/identities with installed TypeScript and fail closed on unsupported data. Commit before handoff. |
| composition_refactor | Opaque sessions and independent expectations | Neutral simulation observations/session provider, qualification ports/observer/ledger/paired/case/batch callers, dedicated tests/evidence. Preserve engine math, reference/build/weight-reader sources and bootstrap/CLI. Commit the inactive provider first; complete accepted transparency/integrity and shortest pinned-run/memory proof before collector adoption. |
| parent | Shared reconciliation and delivery | Apply documentation corrections, verify committed evidence, own shared configuration/policy/status/index, reconcile exact source mappings and push serially. Allocate reference/probe seams after the committed session contract is known. |

The inactive session handoff `6e111545` and storage correction `a58be25e` are
verified against the combined parent source. Checks pass 106 Metal and 66
value/alias/package/canonical-port cases. Nine public constructors and all
existing fault assertions are preserved. The same session owner will complete
pinned-run/four-trial memory qualification before caller migration. RNG and
shared assembly writes remain with the ownership worker; no collector is active.

The ownership agent's committed purity review `a6fade0` bounds the three
seeded-random acquisition seams and immutable audit-state transition. It is a
read-only plan; all four findings remain until concrete repairs are checked.
Shared ports/bootstrap/capture/case writes must be serialized with the session
owner. The ownership worker now implements the complete RNG acquisition/pure-transform
slice in an independent clone at `54aea507`; only its proved three RNG findings
may be cleared. Native bridge splitting remains exclusive to the symbols owner;
every new native_types_*.mjs module needs source/index/type coverage on
integration. An independent read-only metric review checks the documented
aggregation discrepancy before any tool correction; no threshold or guard is
weakened.

The exact session assignment is retained in the worker conversation. Additional
caller allocation comes from the parent before an edit. No worker changes
shared configuration, policy metadata, status/index documents, dependencies,
other workers' code, branches or remote refs. The parent reconciles final
committed declarations after application and analyzer integration. The native
structured-type component and opaque observation boundary do not touch each
other's files; their checks and parent policy joins are serialized.

Parent allocation after the committed runtime-resource review: the existing
session worker also owns minimal native-session/evidence-type wiring in
qualification/adapters/parity_case.py, paired_observer.py and paired_causes.py.
Reference producer/build/weight-reader bytes remain protected. Reference seams
and the remaining layout/pulse/scalar/reducer probes are allocated only after
the session's committed contract is known; their exclusive scopes do not move
silently to the session worker.
