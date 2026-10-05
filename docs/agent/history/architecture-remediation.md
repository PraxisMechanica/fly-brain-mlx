# MLX application architecture remediation

Historical record. Holds, process states, model-switch instructions, package counts, and remote availability below describe the recorded checkpoint. For current work, read [milestone.md](../../../milestone.md) and [AGENTS.md](../../../AGENTS.md). Original review ownership and scientific evidence are preserved.

The user authorized this work on 2026-10-04. The application must use MLX only. Remove Conda, NVIDIA execution backends, and unused packages. Keep Brian2 and PyTorch only for the scientific qualification required by the accepted contract. No database infrastructure is needed.

## Decision before implementation

**Force:** executable entrypoints, file storage, and qualification frameworks vary. Neural equations, operation order, edge/event identity, precision, output schemas, and acceptance budgets must remain fixed.

**Choice:** one uv-managed `src/fly_brain` package. Use domain modules for simulation, qualification, and spike comparison. Keep MLX execution in the simulation adapter. Keep independent Brian2/PyTorch reference code in qualification adapters. Use immutable records internally and Pydantic for external requests. Inject execution and output dependencies. Keep the command-line adapter thin.

**Rejected alternative:** retaining the inherited multi-backend benchmark dispatcher would preserve cycles, globals, and unnecessary CUDA dependencies. A new database, generic repository, transaction framework, dependency-injection container, or web framework has no purpose here.

**Verification:** normal package imports, enforced import contracts, full-scope Ruff/Pyright, unit tests without device/framework setup, preserved file-contract checks, fresh scientific requalification with no skips, and a recorded final review. The current small MLX core is the numerical envelope. Full-connectome loading and simulation remain later milestones.

## Work steps

1. Preserve incoming work and record the authorization. Replace obsolete runtime and Conda installation files.
2. Establish `pyproject.toml`, `uv.lock`, package imports, dependency groups, and complete quality configuration. Keep the qualified scientific versions.
3. Separate requests, services, MLX execution, file adapters, and qualification. Give existing accumulation algorithms backend ownership. Replace test-module patching with an explicit propagation dependency.
4. Configure strict public typing, third-party adapter typing, test groups, and import-linter contracts. Verify the thin entrypoints and file boundaries.
5. Requalify the existing reference, serial-core, and factored cases with unchanged criteria and fresh evidence. Record source/evidence checks, scope limits, and the architecture release decision.

## Progress

- Incoming scientific work: archived with original hashes; 47 files preserved.
- Application refactor: implemented as one MLX-only package; obsolete runtime, Conda, and requirements workflows removed.
- Verification complete: 31 application tests and 61 scientific tests pass with zero skips. Ruff, strict Pyright, and all three import contracts pass. A normal clean runtime installation executes the delayed-input core on Metal.
- Numerical preservation: 157 factored scalar cases meet both fixed budgets; four reference replays are byte-identical. All 1,076 arrays in 39 retained artifacts match. The bounded Astra review passes.
- Architecture hold: released after the checks and final review below. Full-connectome loading, integration, parity, and performance remain open milestones.

All changes belong on `main`. Commit verified steps incrementally. Push remains pending until a user-owned remote exists.

## Retired source

The checkpoint `22c813e` retains the original application in Git. For an exact historical source citation, run `git show 22c813e:code/run_brian2_cuda.py` or substitute the recorded repository path. The earlier audit and numerical reports cite those historical versions. Their line numbers describe the original files, not the moved package.

Removed active workflows: `environment.yml`, `environment-brian2genn.yml`, split requirements files, the CUDA/GeNN/NEST runners and installers, the multi-framework benchmark dispatcher, unused vendored Python/notebooks, and the old standalone entrypoint scripts. Their source remains in Git; all existing data, result bundles, licenses, and scientific evidence remain on disk.

Moved numerical code: MLX core and accumulation arithmetic now belong to `simulation/backend`; independent Brian2/PyTorch references and diagnostic execution belong to `qualification/adapters`; shared test helpers belong to `tests/support`. Comparison rules no longer depend on Pandas or the benchmark dispatcher. No compatibility wrappers or duplicate installation methods were added.

The [source preservation record](../../evidence/architecture-remediation/source-preservation.json) checks 28 arithmetic/reference bodies against `22c813e`. Precision configuration and the factored propagation binding are explicit. Their behavior is covered by fresh scientific qualification, not inferred from source identity alone.

## Final technology scope

| Purpose | Installed choice |
| --- | --- |
| Runtime | Python 3.10.14; MLX and MLX Metal 0.32.3; NumPy 1.26.4; PyArrow 25.0.1; Pydantic 2.13.5 |
| Package and environment | uv; `pyproject.toml`; `uv.lock`; one supported macOS ARM64 environment |
| Application boundaries | Domain-owned immutable records, pure comparison rules, explicit execution/file collaborators, Pydantic request validation, and a thin standard-library command-line adapter |
| Development checks | Ruff 0.16.10; strict Pyright 1.1.414; pytest 9.1.1; import-linter |
| Optional scientific qualification | Brian2 2.8.0, Cython 3.3.0, and CPU PyTorch 2.11.0, managed by the same uv project |

The normal runtime has ten installed packages including the application and transitive dependencies. The development/qualification environment has 38. Both pass uv's package compatibility check. The clean runtime contains no Brian2, PyTorch, Pandas, SciPy, Matplotlib, or Joblib. No CUDA runner, NVIDIA dependency, Conda manifest, split requirements workflow, or database framework remains in the application.

`pytest-asyncio` is excluded because this application has no asynchronous behavior. The later user instruction to remove unused packages takes precedence over the original generic test-tool inventory. SQLModel, Alembic, web frameworks, generic repositories, transaction units of work, and dependency-injection containers have no required role here. These are scope decisions, not deferred infrastructure.

## Final architecture review

The force, choice, and rejected alternatives above still apply. The review checked the installed package, its callers, request schemas, services, framework/file adapters, test support, and quality configuration against `python-design` and `software-design`.

| Audit finding | Implemented correction and evidence |
| --- | --- |
| No installable package | One `src/fly_brain` package and installed command; imports and comparison execute from outside the checkout. The [clean installation](../../evidence/architecture-remediation/clean-runtime.json) is normal, not editable. |
| Orchestration/persistence cycle | The inherited dispatcher and runners are removed. Domain services accept small callable contracts; bootstrap owns concrete composition. Three enforced import contracts pass. |
| Hidden operational globals | Paths and requests are immutable values. Precision is configured before framework loading and injected into construction. Each execution captures its own network and propagation arrays. Output writers receive explicit fresh destinations. |
| Algorithms/test support lack ownership | Accumulation belongs to the MLX backend. Independent references belong to qualification adapters. Shared harness/artifact support uses fixtures and an injected execution factory; no peer-test patching or global measurement registry remains. |
| Narrow completion checks | Ruff covers the owned project; Pyright checks all 48 application/test files in strict mode. [Specific third-party limits](../typing.md) document local stubs and four narrow suppressions. Tests are marked unit, integration, reference, and Metal. |

No unresolved audit finding or blanket legacy exemption remains. Unit checks prove acceptance rejects skipped/empty/failed suites, collaborators receive the correct run, independent configurations do not share output state, and existing evidence is preserved. Integration checks use real Parquet files and a fresh process to verify imports, installed commands, null/finite validation, supported time columns, and the existing report filenames. There is no database test or destructive fixture cleanup.

## Completion evidence and limits

- [Final check record](../../evidence/architecture-remediation/checks.json): Ruff lint/import sorting and formatting pass; strict Pyright has zero errors or warnings; three import contracts pass; the uv lock is current; both installed environments are compatible.
- [Application test report](../../evidence/architecture-remediation/boundary-tests-final.xml): 31 passed, zero failures, errors, or skips.
- [Scientific test report](../../evidence/architecture-remediation/qualification/tests.xml) and [result](../../evidence/architecture-remediation/qualification/result.json): 61 passed, zero failures, errors, or skips, on the Apple M1 Max Metal device. Complete state/event artifacts are retained beside the report.
- [Factored scalar result](../../evidence/architecture-remediation/factored-scalars/factored.json): 157/157 pass both unchanged budgets; repeated and minimally padded standalone results match bit for bit. Maximum one-step budget fraction is 0.0236594731.
- [Retained casting diagnostic](../../evidence/architecture-remediation/accumulation-scalars/accumulation.json): all 125 diagnostic assertions pass, but only 109/125 original-weight one-step cases and 119/125 trajectory cases meet parity. Its strategy remains unapproved. Passing limitation assertions does not erase these failures.
- [Reference replay](../../evidence/architecture-remediation/reference-replay/numerical-contract.json): two NumPy and two C++ traces are byte-identical, with 43 spikes and the frozen stimulus hash. The [schedule diagnostic](../../evidence/architecture-remediation/reference-schedule/reference-schedule.json) matches the original Brian2/PyTorch trace.
- [Source preservation](../../evidence/architecture-remediation/source-preservation.json), [artifact/archive verification](../../evidence/architecture-remediation/artifact-preservation.json), and the [bounded Astra preservation review](../../evidence/architecture-remediation/astra-preservation-review.md) establish the retained small-network numerical contract. The parent verified the evidence before integration.

Architecture compliance is complete for the current application scope. This does not qualify a complete connectome, compiled factored propagation, custom kernels, production spike export, full-network parity, or performance. Threshold rounding and serial/weight-casting limits remain recorded. The manual specification/evidence updates were preserved and left unstaged at architecture release. Sol then verified and integrated the completed manual handoff in a separate checkpoint recorded in `milestone.md`; the original scientific decision and owner are retained.

Incremental checkpoints: `22c813e` records authorization and incoming-work preservation; `d98f5bf` installs the architecture; `bf97672` verifies file boundaries and the clean runtime; `c61e246` records numerical preservation and the completed Astra review. The release record is committed separately. No user-owned remote is configured; pushing to the reference upstream is outside the authorized scope.
