set shell := ["sh", "-eu", "-c"]

check: format-check lint type-check boundaries quality-tests metrics

format-check:
    uv run --locked --no-sync python -m tools.code_quality.run format ruff format --check src tests tools main.py

lint:
    uv run --locked --no-sync python -m tools.code_quality.run lint ruff check src tests tools main.py

type-check:
    uv run --locked --no-sync python -m tools.code_quality.run types pyright

boundaries:
    uv run --locked --no-sync python -m tools.code_quality.run boundaries lint-imports --no-cache

quality-tests:
    uv run --locked --no-sync python -m tools.code_quality.run tests python -m pytest -q tests/quality

metrics:
    uv run --locked --no-sync python -m tools.code_quality.run metrics python -m tools.code_quality.gate

bootstrap:
    uv sync --locked --group qualification
    pnpm install --frozen-lockfile
    uv run --locked --no-sync pre-commit validate-config
    uv run --locked --no-sync pre-commit install --hook-type pre-commit --hook-type pre-push
