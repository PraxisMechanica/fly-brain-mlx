# MLX application architecture remediation

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
- Initial verification: strict Pyright and import contracts pass; 61 scientific tests pass with zero skips. Scalar/replay checks, clean runtime installation, and final review remain open.
- Feature development: held until architecture checks pass.

All changes belong on `main`. Commit verified steps incrementally. Push remains pending until a user-owned remote exists.

## Retired source

The checkpoint `22c813e` retains the original application in Git. For an exact historical source citation, run `git show 22c813e:code/run_brian2_cuda.py` or substitute the recorded repository path. The earlier audit and numerical reports cite those historical versions. Their line numbers describe the original files, not the moved package.

Removed active workflows: `environment.yml`, `environment-brian2genn.yml`, split requirements files, the CUDA/GeNN/NEST runners and installers, the multi-framework benchmark dispatcher, unused vendored Python/notebooks, and the old standalone entrypoint scripts. Their source remains in Git; all existing data, result bundles, licenses, and scientific evidence remain on disk.

Moved numerical code: MLX core and accumulation arithmetic now belong to `simulation/backend`; independent Brian2/PyTorch references and diagnostic execution belong to `qualification/adapters`; shared test helpers belong to `tests/support`. Comparison rules no longer depend on Pandas or the benchmark dispatcher. No compatibility wrappers or duplicate installation methods were added.

The [source preservation record](evidence/architecture-remediation/source-preservation.json) checks 28 arithmetic/reference bodies against `22c813e`. Precision configuration and the factored propagation binding are explicit. Their behavior is covered by fresh scientific qualification, not inferred from source identity alone.
