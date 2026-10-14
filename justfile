set shell := ["sh", "-eu", "-c"]

check stage="commit":
    uv run --locked --no-sync python -m tools.code_quality.check {{stage}}

format-check:
    uv run --locked --no-sync python -m tools.code_quality.check manual --only format

lint:
    uv run --locked --no-sync python -m tools.code_quality.check manual --only lint

type-check:
    uv run --locked --no-sync python -m tools.code_quality.check manual --only types

boundaries:
    uv run --locked --no-sync python -m tools.code_quality.check manual --only boundaries

metrics:
    uv run --locked --no-sync python -m tools.code_quality.check manual --only metrics

bootstrap:
    uv sync --locked --group qualification
    pnpm install --frozen-lockfile
    uv run --locked --no-sync pre-commit validate-config
    uv run --locked --no-sync pre-commit install --hook-type pre-commit --hook-type pre-push
