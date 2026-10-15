# Project architecture policy

Audience: agents and maintainers. This document owns the project-specific
interpretation of architecture rules and change acceptance.

## Authority and purpose

Keep simulation, qualification and comparison understandable. Add structure only
for a current responsibility or consumer problem. Preserve reproducible inputs,
failures, scientific contracts and protected reference lineage.

MLX arrays, states, traces, streams and existing compilation operations belong
directly in the backend. Qualification may use recognizable Torch/Brian models
and legitimate framework inheritance. No portable tensor layer or compulsory
framework rewrite is required.

## Rule-by-rule decisions

**Keep** retains a useful requirement; **adapt** applies only the practical scope
below; **not applicable** identifies a responsibility absent from this application.
These decisions are project policy, not a claim of complete automatic proof.
Review expectations use source review and affected behavior tests. Existing native
checks reject actual failures in their implemented scope.

| Rule | Decision | Requirement for this project |
| --- | --- | --- |
| OWN001 | Adapt | Keep simulation, qualification and comparison code with the responsibility it serves. Retain the current layout; no move merely to meet a generic domain tree. |
| OWN002 | Adapt | Give inputs, runs, reference artifacts and comparison results clear owners. Do not create one domain per file, array or runtime object. |
| OWN003 | Adapt | Split unrelated responsibilities when they cause real maintenance difficulty. Related types, numerical helpers and orchestration may share a coherent module. |
| OWN004 | Keep | Generic helpers must not secretly introduce model-specific decisions or a second source of experiment policy. |
| OWN005 | Adapt | MLX implementation belongs in the simulation backend; Torch/Brian implementations belong in qualification. No external integration tree or neutral tensor layer is required. |
| OWN006 | Adapt | Keep scientific policy legible and avoid accidental duplication. Framework-specific numerical model definitions are valid; do not split each arithmetic operation from its provider. |
| DEP001 | Adapt | Retain useful configured import boundaries, especially production versus qualification. Concrete same-backend imports are permitted. |
| DEP002 | Adapt | Avoid import/dependency cycles that obscure responsibility or break initialization. Use existing import checks and source review, not a new semantic owner-graph engine. An intentional annotation edge alone does not justify a new layer. |
| DEP003 | Adapt | Use clear interfaces between workflows and keep qualification-only dependencies out of production. Private backend components may collaborate directly. |
| DEP004 | Adapt | A private MLX backend callback may expose MLX state, traces and arrays. Add a neutral contract only when an actual consumer requires it. |
| DI001 | Adapt | Type meaningful dependencies; concrete types and checked callables are acceptable. Add a protocol only where substitution or a current consumer benefits. |
| DI002 | Adapt | Make expensive setup and resource creation visible. Local constructors, owned values and array allocation require no injected factory ceremony. |
| DI003 | Keep | Avoid hidden mutable globals and service locators. Pass scientific seeds, configuration and other reproducibility-sensitive inputs explicitly. |
| DI004 | Adapt | Own actual file/process/device lifetimes and release resources reliably. No universal infrastructure layer is required. |
| ROLE001 | Adapt | Keep command parsing, dispatch and failures clear. Do not require an exact count of one use-case call on every command path. |
| ROLE002 | Adapt | Keep orchestration readable and separate complicated numerical calculations when that helps understanding. MLX knowledge appropriate to the backend is allowed. |
| ROLE003 | Adapt | Keep file serialization and format validation coherent; storage operations must not unexpectedly launch unrelated scientific workflows. |
| ROLE004 | Not applicable | The application has no database or object-relational mapper. Existing file storage does not require a database repository pattern. |
| ROLE005 | Not applicable | There are no foreign database tables or joins. Shared pinned model inputs are legitimate. |
| ROLE006 | Adapt | Preserve meaningful errors and artifact context. Native arrays and useful native exceptions need no universal neutral wrapper. |
| ROLE007 | Adapt | Avoid surprising heavy work during imports or dependency construction. Normal command startup may execute the requested workflow. |
| STATE001 | Adapt | Keep scoring and model calculations reproducible; make time, randomness and I/O explicit where behavior depends on them. MLX allocation/evaluation is allowed in numerical code. |
| STATE002 | Keep | Prevent unintended caller-input mutation and mutable alias surprises. Document and test ownership of buffers and simulation state; no universal alias-proof engine. |
| STATE003 | Adapt | Simulation sessions deliberately own state. Prevent leakage between independent runs; do not force a stateful simulator into stateless service patterns. |
| ISP001 | Adapt | Keep added consumer interfaces small and useful. Do not build universal registries or speculative methods. |
| OCP001 | Adapt | Use ordinary explicit dispatch for the fixed supported execution/reference modes. No strategy framework just to eliminate a short switch. |
| LSP001 | Keep | Implement the operations a consumer actually expects. Preserve native type checks and meaningful failure behavior. |
| VALUE001 | Adapt | Retain useful FlyWire/neuron/trial brands where they prevent mixups. Array positions, dimensions and serialization fields may remain numeric; check mapping, bounds, dtype, shape and provenance at meaningful boundaries. |
| COMP001 | Adapt | Prefer simple composition where it improves code. Legitimate `nn.Module`/autograd/reference inheritance is allowed; no compulsory framework-model rewrite. |
| ERR001 | Keep | Propagate or deliberately handle failures. A log or empty catch must not hide a failed requested operation. |
| TYPE001 | Keep | Retain adopted strict typing and documented third-party limits. No unchecked type escapes to conceal actual mismatches. |
| CODE001 | Keep | Remove proven unused code when safe; preserve public/registered consumers and independent scientific references. |
| STYLE001 | Keep | Use the existing formatter and syntax rules. No second formatting tool or metric-based structural quota. |
| COV001 | Adapt | Account for required source/check inputs and affected consumers. File inventory is useful; a complete classification of every runtime effect is not a refactor prerequisite. |
| COV002 | Adapt | Missing required tools, invalid inputs, parse errors and unsupported required check scope remain failures. Missing experimental whole-program capabilities are outside the required gate. |
| COV003 | Adapt | Keep automatic affected checks/tests at commit and CI, plus static push checks. Reuse unchanged results; no full-codebase or manual test replay and no new merge-protection requirement. |
| COV004 | Adapt | Test changed behavior with focused tests. Do not require broad checker self-tests, hook simulations or disabling every guard as routine work. |

## Executable checks and behavior tests

The executable policy uses the existing runner and tools. Required checks are:

| Check | Reject | Permit |
| --- | --- | --- |
| Ruff and Pyright | Adopted syntax/format/type failures | Concrete MLX types, typed callables and legitimate framework reference models |
| Production imports | Simulation depending on Torch/Brian or qualification code | Direct MLX backend collaboration and private numerical helpers |
| Comparison imports | Scoring/calculation code depending on execution frameworks or workflow/storage mechanics | Numerical library operations and the useful owned identity types |
| Scientific source identity | Missing/invalid protection records or an unreviewed protected-source hash change | Ordinary function, argument, declaration and module changes outside protected scientific sources |
| Indexed inputs and affected selection | Missing committed check/source inputs or an unsupported required scope | Changed sources and affected consumers without a full-source replay |
| Automatic behavior tests | A failure in selected changed/affected behavior | One invocation at commit and CI; no manual or push test replay |

The scientific guard uses the three-source manifest owned by
[source ownership](architecture-ownership.md), with reviewed hashes and provenance.
Existing independent input, mapping, state, repeatability and numerical checks
retain their actual acceptance contracts. Numerical quality scores are advisory.

Tests for changed enforcement exercise useful outcomes: a concrete backend
contract passes, a protected source change fails, and production reference
contamination fails. Application tests retain validation, ordering, outputs and
error behavior. Source review covers properties outside the automatic checks.

## Concrete implementation boundaries

Private `Advance`/`Execution` backend contracts and qualification `TorchModel`
framework types are accepted. Useful identifier brands remain; residual numeric
coordinates do not justify universal wrappers or conversion-origin analysis.
Preserve actual bounds, ordering, dtype, shape, occupancy and independent checks.

## Bounded change acceptance

A source repair must name the concrete problem, affected callers, smallest useful
change and meaningful verification. Preserve the current practical architecture
and add structure only for an actual consumer need.

[Quality coverage](quality-coverage.md) owns implemented checks and their limits;
[milestone.md](../../milestone.md) owns remaining work and handoff. The
[numerical contract](numerical-contract.md) retains all scientific acceptance gates.
Keep independent evidence and report failed, skipped and incomplete verification
honestly.
