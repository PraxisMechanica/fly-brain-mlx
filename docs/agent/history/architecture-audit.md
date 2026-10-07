# Architecture compliance audit

Historical record. Holds, process states, model-switch instructions, package counts, and remote availability below describe the recorded checkpoint. For current work, read [milestone.md](../../../milestone.md) and [AGENTS.md](../../../AGENTS.md). Original review ownership and scientific evidence are preserved.

Recorded 2026-10-04 (Europe/Paris). Audited checkpoint: `ab8637c885ee9e23e81c3d1596744a63695650f8` on `main`, plus the explicitly identified uncommitted review work. Historical audit status: **investigation complete; remediation was proposed and development was halted**. The subsequent authorized implementation and current checks are in the [remediation record](architecture-remediation.md).

## Conclusion and scope

I failed to implement the required application architecture and establish the approved Python stack as its foundation. I read both design skills before implementation. I then proceeded without the required package structure, typed application boundaries, domain services, explicit execution dependencies, and complete quality checks. Calling this an enforcement gap understated the implementation omission.

I made numerical qualification the completion gate. I did not make application compliance a prerequisite. The missing architecture and tool configuration remain my responsibility.

This audit covers the root entrypoint, project-owned backend and comparison modules, authored probes, qualification tests, tooling configuration, milestone/handoff history, and relevant public session records. Static-check counts below cover nine committed authored files, not every inherited or vendored file. The unfinished factored-network test is reviewed structurally and is excluded from those counts. No simulations, benchmarks, dependency installations, application refactors, or data deletion were performed during this audit.

Standards applied: [python-design](/Users/ocasta/.codex/skills/python-design/SKILL.md), [software-design](/Users/ocasta/.codex/skills/software-design/SKILL.md), their supporting architecture references, and [project rules](../../../AGENTS.md). These skills require the smallest architecture that fits the actual variation and failure modes; they do not require every enterprise pattern. The current application has file persistence and execution backends, but no database or HTTP service requiring a database repository, transaction unit of work, or web framework.

Preserve the existing scientific evidence during repair. The small MLX core contains typed functions, a frozen dataclass, named tuples, and explicit Metal execution. Those local choices do not implement the required application architecture. Use of uv, Ruff, Pyright, and pytest also does not satisfy the complete specification.

## Audited technologies and approved target

The technology inventory records installed versions, configuration files, and source imports. Installation and application integration are separate facts.

| Area | Current state | Required target for this application |
| --- | --- | --- |
| Package management | uv 0.5.31 was used with pinned requirements files. Inherited Conda manifests also specify pip installation. No `pyproject.toml` or `uv.lock` exists. | One uv-managed application package with `pyproject.toml` and `uv.lock`. No Conda workflow is required for the MLX goal. |
| Environment isolation | A local `.venv` exists. Inherited Conda manifests describe other backend environments. | One supported application environment created with `uv venv`. Keep qualification dependencies in the same uv project. |
| Formatting and lint | Ruff 0.16.10 is installed. No project Ruff configuration exists; checks were limited in scope. | Configure Ruff for formatting, lint, and import sorting across all application-owned code. |
| Type checking | Pyright 1.1.414 is installed. Its strict configuration selects two files. ty is absent. | Keep Pyright and apply a documented policy to all application-owned code. Make public boundaries strict. No second checker is needed. |
| Tests | pytest 9.1.1 is installed. pytest-asyncio and declared unit/integration/device groups are absent. | Use pytest and pytest-asyncio as the approved test dependencies. Declare unit, integration, and Metal qualification groups. Use asynchronous tests only for asynchronous behavior. |
| Boundary validation | Pydantic and SQLModel are absent. Application requests/configuration mainly use dictionaries and primitive values. | Use Pydantic for validated external run/configuration boundaries. Use plain immutable records inside the domain. Validate arrays in bulk in the owning input/backend adapter. |
| Import rules | import-linter and declared dependency contracts are absent. | Use import-linter to enforce domain and adapter boundaries. |
| Application structure | Flat `code/` modules, path injection, mixed workflow and storage functions. | An installed `fly_brain` package organized by simulation, benchmarking, and comparison domains. Each domain owns its rules and adapters. |
| Dependency injection | Global paths, environment reads, framework preferences, and concrete runner back-references. | Inject configuration, engine callables/ports, clocks, and output writers through function parameters or constructors. Wire them at the entrypoint. |
| Command-line handling | Standard-library `argparse` with workflow and backend-selection logic. | Keep `argparse` as a thin adapter over an application service. A new command-line framework has no demonstrated need. |
| File persistence | pandas, PyArrow, Parquet, comma-separated values (CSV), and JSON; storage logic mixed with execution. | Keep existing file contracts. Put file reads/writes in domain-owned adapters that return typed values. |
| Database models and migrations | No database, SQLModel, Alembic, or database boilerplate was found in the application. | Excluded from this application. No database models, migrations, repositories, or transaction units of work are proposed. |

The installed scientific stack is Python 3.10.14, Brian2 2.8.0, NumPy 1.26.4, MLX/MLX-Metal 0.32.3, and PyTorch 2.11.0. Data and analysis dependencies include pandas 2.3.3, PyArrow 25.0.1, SciPy 1.15.3, joblib 1.6.0, matplotlib 3.10.9, and Cython 3.3.0. Preserve qualified versions during architecture repair. These libraries serve the simulation; they do not replace the approved application tools.

The source also contains Brian2CUDA, NEST GPU, GeNN, and Brian2GeNN adapters. Their presence does not prove installation or qualification in the current Apple-silicon environment. No web service, frontend, or database stack is needed for the present command-line simulation.

### Dependency scope after user clarification

On 2026-10-04, the user specified one package workflow and no competing application frameworks. The proposal is one uv project, one lockfile, and one supported environment. MLX is the application execution backend. Brian2 and PyTorch remain qualification dependencies because the reviewed contract requires their reference and comparison results. They already coexist with MLX in the current environment.

Conda is not required for these dependencies. Install the same Python packages through uv; no equivalent library replacement is needed. Brian2 publishes a normal Python package, and uv supports the Python package index and PyTorch installation. See [Brian2 installation](https://brian2.readthedocs.io/en/2.8.0/introduction/install.html), [uv package indexes](https://docs.astral.sh/uv/concepts/indexes/), and [uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/). Brian2's reference code generation still needs a system C++ compiler.

Brian2CUDA, NEST GPU, GeNN, and Brian2GeNN are outside the proposed MLX application installation. Their native build requirements and the older Brian2GeNN version conflict do not justify a second supported package workflow. Jupyter is optional analysis tooling. Preserve the inherited source and existing evidence during the hold; do not port these optional backends or change command contracts in this investigation.

There is no database infrastructure to remove. SQLModel and Alembic were listed as conditional approved tools in the initial audit. That was unnecessary for this application. They are now explicitly excluded from the proposed stack.

The [dependency-scope check](../../evidence/dependency-scope-20261004.json) records the read-only environment check and database-import search. All 41 installed packages passed uv's compatibility check. This does not replace a clean installation test. No package installation, backend removal, or application change was performed.

## Verified findings

| Finding | Evidence and consequence | Required correction |
| --- | --- | --- |
| No installable application package | No `pyproject.toml` or package definition. [main.py](architecture-remediation.md#retired-source), probes, and tests inject paths into `sys.path`. Dynamic imports are unresolved by the wider type check. | Install one named package; import it normally from entrypoints and tests. |
| Orchestration and persistence are interdependent | [benchmark.py](architecture-remediation.md#retired-source) owns experiment configuration, scheduling, concrete runner dispatch, logging, CSV/manifest persistence, and presentation. Runners import its configuration and output helpers back, for example [run_brian2_cuda.py](architecture-remediation.md#retired-source). Deferred imports avoid immediate loading cycles but retain the dependency cycle. | Separate domain rules, application orchestration, and file/framework adapters; wire concrete backends at the entrypoint. |
| Operational state is hidden in globals | [benchmark.py](architecture-remediation.md#retired-source) reads process configuration and owns global paths. [run_reference_baseline.py](architecture-remediation.md#retired-source) mutates those paths and Brian2 preferences. Imports in `main.py` and `benchmark.py` change environment/warning settings. [mlx_core.py](architecture-remediation.md#retired-source) discovers launch policy inside network construction. | Pass immutable run configuration and paths explicitly. Validate launch/precision/device requirements at bootstrap or the backend factory, preserving the existing safety requirements. |
| Reusable algorithms and test support lack clear ownership | [probe_mlx_factored_accumulation.py](architecture-remediation.md#retired-source) imports another executable probe and owns reusable arithmetic. The uncommitted [factored test](architecture-remediation.md#retired-source) patches another test module and the core to substitute behavior. [test_mlx_core.py](architecture-remediation.md#retired-source) also owns mutable measurements and artifact output. | Put backend arithmetic in its backend module, independent reference helpers in test support, and artifact recording at the qualification boundary. Inject the actual propagation variation through one small seam. |
| Completion checks understate their scope | [pyrightconfig.json](architecture-remediation.md#retired-source) includes only the core and qualification runner. No project-owned Ruff/pytest configuration, unit/reference/device classification, or enforced application dependency graph exists. | Make check coverage explicit across all application-owned modules, scripts, and tests; enforce package boundaries and document narrowly scoped third-party typing limitations. |

MLX arrays and explicit device streams belong in the MLX backend; replacing them with an elaborate framework-neutral numerical layer would add complexity. The architectural failure is ownership and hidden dependencies, not the presence of backend-specific array types.

### Reproduced static checks

The historical check record contained commands, exit codes, source hashes,
inventory, and diagnostic counts. Routine JSON, compressed Pyright stdout,
settings dumps, and console output were removed from Git under the user's
2026-10-07 retention amendment. The diagnostic counts below retain their
original checkpoint scope.

| Check | Scope | Result |
| --- | --- | --- |
| Existing configured strict Pyright | Two files | Exit 0; zero diagnostics |
| Same strict checker with explicit authored paths | Nine committed files | Exit 1; 881 diagnostics |
| Ruff with explicit authored paths | Same nine files | Exit 1; five `I001` import-order diagnostics |

The 881 diagnostics include six missing-stub and eight missing-import reports, plus cascading unknown-type reports and missing annotations. They are **not 881 demonstrated runtime defects**. They demonstrate that the green configured check does not establish typing compliance for the application. Inherited runners were inspected structurally; these counts must not be presented as their complete lint/type baseline. No numerical tests were rerun under the hold.

## How the oversight occurred

Relevant public session/tool records and Git history are summarized in process history. Times here are Europe/Paris.

1. Both design skills were read at 14:14:49 and again at 15:22:36, before MLX implementation. At 14:16:59 this chat publicly said it was using them to keep the port within the existing backend interface. The failure was in applying and enforcing their requirements, not discovering the skills.
2. The imported source was preserved at `4466b37`. Subsequent reference helpers (`295994b`, `5489ae0`) repeated path injection and global operational overrides. These choices should have triggered a recorded architecture exception or correction before being extended.
3. The consolidated plan prioritized source preservation and numerical evidence. Its instruction to preserve upstream structure conflicted with broader application standards. The implementing agent treated preservation too broadly, did not surface the conflict, and established no architecture acceptance gate.
4. Milestone 1 added a locally well-structured core, but `52f8427` introduced a strict type check covering only two files. Numerical test success and narrow static checks were recorded as milestone completion without an application-wide architecture qualification.
5. Scientific handoffs bounded numerical review carefully but did not carry an explicit application architecture prerequisite. Later scripts and test adapters therefore accumulated more coupling while the scientific review advanced.

The supported causal inference is that I prioritized numerical acceptance and treated the preservation instruction as a structural exemption. I did not implement the required application foundation. Reading the skills did not excuse that omission. The record shows an implementation and review-process failure by this agent, not a skill-discovery or platform malfunction.

The latest user instruction resolves the conflict: repair necessary application boundaries while preserving numerical semantics, source provenance, evidence, and existing external contracts. Earlier instructions against an upstream architecture rewrite do not exempt defects identified here from remediation. Unrelated code and genuinely vendored source remain untouched.

## Proposed resolution

### Design decision

**Force:** execution engines, input readers, and output storage vary; the neural model, experiment meaning, ordering, deterministic stimuli, and output contracts must remain fixed. Current concrete back-references and process globals obscure that distinction.

**Choice:** one installable `src/fly_brain` package organized around simulation, benchmarking, and comparison. Each domain owns its values, rules, service functions, and file/framework adapters. Use Pydantic at external run/configuration boundaries. Keep immutable Python records inside domains. Define only the small consumer-owned callable or protocol needed to select existing engines and propagation implementations. `main.py` remains the thin primary entrypoint and explicit composition root.

**Rejected simpler alternative:** adding more path patches and helper extractions inside the existing dispatcher would leave dependency cycles, global configuration, and unowned backend variations intact. A generic clean-architecture framework, dependency-injection container, ORM, event bus, or new service layer hierarchy has no demonstrated need here and is also rejected.

**Verification:** normal installed imports, enforced dependency direction, orchestration tests using lightweight engine/output fakes, real entrypoint and file-contract checks, application-wide static gates, and unchanged scientific acceptance criteria.

### Ordered remediation work

1. **Record package and domain boundaries.** Map every application-owned runner, comparison tool, probe, and test helper to its owner. Distinguish pinned vendored source from application code explicitly. Declare allowed imports before moving code. Simulation services cannot import concrete runners, command parsers, or benchmark presentation/persistence; benchmarking and comparison call simulation services through their declared contracts.
2. **Package without dependency upgrades.** Introduce `pyproject.toml`, uv-managed installation, reproducible resolution, and explicit Ruff/pytest/type-check configuration. Preserve the qualified Python 3.10.14, Brian2 2.8.0, NumPy 1.26.4, and MLX 0.32.3 versions. Use one supported MLX environment, with Brian2/PyTorch qualification dependencies in the same project. Exclude the optional NVIDIA backends from the application installation. Remove application/test path injection as callers move to installed imports.
3. **Make execution dependencies explicit.** Separate experiment values and scheduling from concrete backend wiring, logging, clocks, and output persistence. Inject run configuration, paths, engine selection, and output collaborators. Isolate unavoidable framework-global preferences inside the owning adapter's execution lifecycle. Preserve command options, spike/manifest fields, and numerical expressions, ordering, dtypes, queue semantics, and precision guards.
4. **Give qualification code stable ownership.** Move existing reusable MLX arithmetic without optimization or algebraic changes. Share reference fixtures through test support while keeping independent oracle equations independent. Replace test-module monkeypatching with the minimal real propagation seam. Classify pure unit, reference integration, and Metal qualification tests; keep artifact recording explicit and use fresh destinations that preserve existing evidence.
5. **Verify and review before resuming milestones.** Run the gates below, record exceptions and unsupported environments honestly, and conduct a final review against both skills. Packaging or refactoring success cannot replace numerical requalification. The unfinished manual scientific review remains preserved and must not be treated as finalized by this audit.

No database, persisted-file, or public command/output schema modification is proposed. If remediation reveals a required schema change, present the current contract and exact change and obtain the approval required by `AGENTS.md` before dependent implementation. No compatibility shim or new feature is part of this proposal.

## Acceptance checks for lifting the hold

At the audit checkpoint all checks were **open**. Their implementation, verification, and release decision are now recorded in [milestone.md](../../../milestone.md) and the [remediation record](architecture-remediation.md).

1. The ownership/import map covers every application-owned module and every finding above is resolved, or an explicit user-approved exception is recorded. Vendored exclusions are named and justified; no blanket legacy exemption applies to owned runners.
2. A clean supported environment installs the package using uv and the recorded dependency resolution. Entrypoints and tests import normally without application path injection. Importing application domain/service modules performs no file writes, process configuration changes, or execution setup.
3. Automated import-boundary checks pass. Services have explicit configuration and collaborators; no runner imports the orchestrator's concrete persistence/configuration implementation back. Existing engine variation is substitutable through the consumer's small contract.
4. Ruff formatting/lint/import checks and the documented typing policy cover the full application-owned scope. Typed public boundaries are strict; third-party stub limitations are confined to their adapters. Broad exclusions, blanket `Any`, or disabled diagnostics cannot substitute for remediation.
5. Tests verify orchestration intent, independent configurations, and input/output boundaries. Unit tests run without framework/device setup. Reference and Metal requirements are separately identified, and the existing command/output contracts are checked against real adapters on supported hardware.
6. Existing reference/core/factored acceptance suites and deterministic replays are requalified after relevant moves using fresh preserved outputs. Tolerances, discrete invariants, independent oracles, operation ordering, and acceptance envelopes remain unchanged. No skipped required test can be reported as a passing gate; unsupported optional platforms remain explicit limitations.
7. A final Python/software architecture review records the force, choice, rejected alternatives, verified scope, and remaining limits. `milestone.md` records completion evidence and a clear hold decision before selecting further milestone work.

## Audit checkpoint

This audit changes documentation and records static evidence only. The backend goal remains paused. The separate chat **“Review accumulation design”** is idle and its final response explicitly acknowledges the architecture hold; its uncommitted test/evidence/specification updates are preserved and excluded from the audit commit. The attempted stop message was rejected by automatic approval review because separate-chat messaging required explicit authorization; no such message was sent, and read-only inspection subsequently confirmed the chat had stopped.

Remediation is unstarted. Feature and numerical development remain halted. The only configured remote is the reference `upstream`; no user-owned push destination is configured.
