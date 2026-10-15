# Development and qualification

Read `milestone.md` for current holds and `numerical-contract.md` for acceptance.
`README.md` owns installation, simulation and comparison instructions.

## Development loop

1. Read the current milestone and affected source. Choose one bounded outcome.
   Reuse verified task state; inspect immediate dependencies only as needed to
   resolve a concrete uncertainty.
2. Implement the smallest change. Remove superseded paths and duplicate checks;
   keep one implementation and direct assertions of its required behavior.
3. Let commit hooks and CI select routine affected tests. Do not run those tests
   manually as well. Fix a failure with a targeted check before retrying delivery.
4. Run scientific checks only when the changed behavior needs their evidence.
   Diagnose from retained native evidence and the smallest sufficient probe.
   Verify collection, causal-review consumption, acceptance and resumption on
   existing artifacts before launching another long execution.
5. Once that path works and the scientific implementation is stable, run the
   required matrix, fresh repeats and sugar/P9 batches. These are necessary qualification
   executions. Reuse completed cases only after canonical-input, source,
   environment, native-replay and scoring checks establish compatibility with the
   delivered implementation. Resume missing work. New code, inputs, execution
   mode or unresolved failures determine which evidence must be regenerated.
6. Update the milestone with results, missing acceptance and revised estimates;
   commit, push and verify CI. Keep detailed history in Git.

Routine test commands have a five-minute maximum. Assess any overrun before
retrying. Long scientific executions run only for a concrete unresolved diagnosis
or contract-required acceptance. Never shorten an experiment or weaken its gates
to fit the routine test budget. Target
less than 10% idle waiting; continue useful independent work without changing
sources consumed by an active run. Stop unnecessary runs instead of inventing
work to occupy their duration. Concentrate on implementation and acceptance;
further checker/report performance tuning is outside the current scope.

## Tools and delivery

Use Apple silicon/macOS, Python 3.10.14 and uv. Metric tooling uses the versions
in `package.json`; shared commands are in `justfile`.

```sh
just bootstrap
```

Bootstrap installs locked tools and hooks. Commit and CI automatically select
changed/affected Ruff, Pyright, import, scientific-source and behavior checks.
Push performs static delivery checks without another pytest run. Do not add
manual routine test replays. Missing tools, malformed results and failed adopted
checks block delivery; numerical code-quality scores remain advisory.

The input check enforces a combined 10,000-word documentation limit, counting
tracked `.md`, `.rst`, `.adoc`, `.txt` and `.tex` files by whitespace. License texts,
code and generated execution data are separate. Keep decisions and current
bounded evidence; use Git for detailed history.

## Local scientific checks

```sh
uv run --locked --group qualification fly-brain qualify --output executions/local-01
```

This runs local independent-reference and MLX scientific tests, including bounded
observation transparency, all-slot faults, repeats, chunks and batch regressions.

The runner enforces five minutes including setup, kills its owned process group
on expiry and returns unaccepted exit 124. Partial counts are untrusted. Diagnose
failures directly; do not repeat unaffected expensive suites. Hooks own routine
checks; required scientific qualification remains separate.

## Full scientific qualification

```sh
uv run --locked --group qualification fly-brain qualify-parity --experiment p9 --duration-s 0.1 --trial 0 --output executions/parity-01
uv run --locked --group qualification python -m tools.qualify_matrix --output executions/matrix-01
uv run --locked --group qualification python -m tools.qualify_batch --experiment sugar --singletons executions/matrix-01/cases --output executions/sugar-batch-01
```

Check the milestone's current scope before launching. The matrix preserves all 52
prescribed cases, fresh repeats and sugar/P9 one-second four-trial comparisons.
It independently verifies canonical inputs, source/execution identities and
native scoring, stops on an unaccepted case and reports incomplete coverage as
unaccepted. Batch input requires accepted compatible singletons 0–3; exact native
phase/final equality suffices for the state budgets. Differences require diagnosis.
No source edits, commits or push-hook stashing while a run consumes those sources.

Case records include persisted channel metadata, `launch.json`, `environment.json`,
bound reference build provenance, native replay evidence and `case.json`.
`matrix.json` includes per-case/pooled metrics and 100 ms localization. A first
spike difference needs the prescribed causal decision, bound to the original
artifacts. Preserve the unaccepted raw report and record any reviewed acceptance
separately. Good summary metrics or small threshold margins alone do not establish
acceptance.

## Diagnostics and outputs

Each diagnostic uses `fly-brain <command> --output executions/<fresh-directory>`:
`probe-accumulation`, `probe-factored`, `probe-bucketed`, `probe-replay`,
`inspect-reference`, `audit-inputs`, `qualify-fan-in`, `qualify-layout-fan-in`,
`qualify-device-layout`, `qualify-connectome-pulse`. Their contract-defined local
scope does not replace full-network qualification.

Use fresh output directories. Store diagnostics under ignored `logs/` and working
runs under ignored `executions/`. Before a commit, register unfinished consumers
with exact paths, reasons and release conditions in `tools/code_quality/retention.json`.
Successful hooks remove unregistered outputs; failed hooks retain diagnostics.
Remove exceptions when consumers finish. Preserve the seven independent fixtures.
Report skipped, failed and incomplete verification honestly.
