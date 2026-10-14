# Project architecture policy

Audience: agents and maintainers. This document owns the project-specific
interpretation of architecture rules and refactor acceptance.

## Authority and purpose

On 2026-10-14 the user explicitly accepted concrete backend dependencies because
production will remain MLX-only, rejected architecture more complex than the
application, and required each rule to be assessed for its actual benefit.
This amendment supersedes conflicting generic strict-profile requirements and
the former 37-rule completion prerequisite. Decision confidence: 99%; source
review checkpoint: `5249fc5`. Three bounded read-only reviews covered ownership
and dependencies, injection/roles/state, and design/coverage rules. The parent
checked their findings against the registry, backend contracts and current
service, observation and comparison sources.

The goal is understandable scientific code with useful responsibility boundaries,
explicit reproducible inputs, reliable failures and meaningful verification.
Keep simulation, qualification and comparison recognizable. A small function or
module is often sufficient; do not manufacture domain layers, interfaces, factories
or services around every call. A new abstraction needs an actual consumer problem,
not a hypothetical alternative backend or a better numerical code-health score.

Production MLX operations may directly use `mx.array`, `core.State`,
`core.StepTrace`, streams and compilation inside the simulation backend.
Qualification may directly use Torch/Brian types, model equations and required
framework inheritance. Independent references should remain recognizable and
independent. Preserve the numerical contract and current lineage/hash guards.

## Rule-by-rule decisions

**Keep** retains a useful requirement; **adapt** applies only the practical scope
below; **not applicable** identifies a responsibility absent from this application.
These decisions are project policy, not a claim of complete automatic proof.
Review expectations use source review and affected behavior tests. Existing native
checks continue to reject actual failures in their implemented scope; no general
alias/effect/control-flow analyzer is required.

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

## Former six strict-profile observations

The unchanged [ownership registry](../../tools/architecture/ownership.json) records
source identities and historical strict-profile observations. The required loader
checks changed source/inventory records; it does not reject those six recorded
observations as application defects. Their current project dispositions are:

- `DEP004`, `simulation/backend/engines.py:Advance`: accepted private MLX contract.
  `Execution`, `Compiler` and `Factory` may carry the concrete backend types they
  actually use. No neutral numerical carrier or primitive-operation port is needed.
- `OWN005`, `qualification/adapters/torch_reference.py:TorchModel`: accepted
  framework-specific scientific reference. Preserve its independent equations,
  lineage and qualification tests. The same principle applies to the Brian
  reference and existing legacy MLX observation consumers.
- `VALUE001`, FlyWire neuron, neuron-row, edge-row and trial records: the strict
  loader creates these records from the reviewed `primitive` classification, not
  from demonstrated invalid cross-index use. Many public fields are already
  branded. Residual report dictionaries and numerical coordinates do not justify
  new array wrappers or generic lawful-origin analysis. Preserve actual identity,
  ordering, range, trial, occupancy and independent-reference checks.

These are explicit project decisions authorized by the latest user amendment, not
repairs or a PASS under the former generic strict profile. No additional application
defect was established by this bounded review; it is not an exhaustive correctness
proof. Update a classification only after reviewing its actual source and consumers.

## Bounded refactor acceptance

The refactor protects actual invariants and simplifies actual maintenance. A new
source repair must name the concrete problem, affected callers, smallest useful
change and meaningful verification. Do not resume the general analyzer, introduce
provider-neutral numerical wrappers, or reorganize reference models solely to
satisfy the old catalog.

[Quality coverage](quality-coverage.md) owns implemented checks and their limits;
[milestone.md](../../milestone.md) owns remaining work and handoff. The
[numerical contract](numerical-contract.md) retains all scientific acceptance gates.
Refactor completion does not mean scientific implementation or full qualification
is complete. Keep independent evidence and report skipped verification honestly.
