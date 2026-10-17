# Development and qualification

Read `milestone.md` for current holds and `numerical-contract.md` for acceptance.
`README.md` owns installation, simulation and comparison instructions.

## Development loop

1. Choose a bounded behavioral outcome. Complete its related implementation,
   affected callers, collectors and tests as one diagnosable batch, then validate
   before dependent work. Use source review and retained evidence. Remove
   superseded paths; avoid optional cleanup, abstractions and checker/report work.
2. Preserve failure attribution: keep subchanges separable in the diff and know
   which focused observation distinguishes their failures. Combine low-risk
   fixes when attribution remains clear. Separate independent numerical changes
   if their failures cannot be distinguished by a small deterministic replay.
3. Let hooks and CI run affected routine tests once per completed batch. Do not
   test after each edit or pre-run their selected tests manually. Use a focused
   diagnostic when it resolves a concrete uncertainty or failure before dependent
   changes compound it. Choose the smallest discriminating replay; repair related
   causes together before checking again.
4. Reuse retained native evidence for diagnosis and rescoring. Validate a small
   replay against native bytes before trying a scientific correction. For a
   repaired full-network failure, screen its spike metrics with the production
   MLX runner against compatible retained references before another paired run.
   Validate the screen against retained baseline events/inputs; record each
   candidate's source and mode. A screen rejects candidates; acceptance requires
   state, queue, causal, fresh-repeat and full campaign checks. Verify affected
   scientific behavior before dependent work; complete required local checks and
   the campaign once the candidate stabilizes. Retain compatible checkpoints.
5. Before an expensive run, identify its unanswered question or required gate,
   relevant changes, expected duration and stopping condition in the existing
   execution record or milestone. Run only if retained evidence cannot answer it.
   Profile briefly only for a measured bottleneck; pursue an optimization when
   expected savings justify implementation and requalification. Throughput goals
   are estimates, not additional scientific acceptance gates.
6. Freeze scientific sources in the qualification checkout. While a gate runs,
   implement a ready independent batch in a separate worktree and environment;
   integrate after its prerequisite passes. Avoid device contention and changes that would
   invalidate the running qualification. Overlap independent CPU references
   with MLX, retaining fresh initial states, settings, repeats and provenance.
   Score the first replay and stop decisive failures. Complete the claimed tiered
   scope in `milestone.md`; matrix/batch claims require their corresponding gates. Regenerate
   only evidence invalidated by relevant source, input, environment or mode changes,
   as determined by the existing compatibility verifier. A documentation commit
   alone does not require rerunning simulations.
7. Update the milestone after each completed batch or material result. Commit and
   push the coherent batch, then verify its CI; avoid micro-commits and chains of
   unpushed commits that repeatedly select accumulated changes. Keep history in Git.

Routine test commands have a five-minute maximum; diagnose overruns before retrying.
Long scientific executions require the concrete reason above. Preserve all contract
horizons and gates. Minimize total validation time and target less than 10% idle
waiting; useful concurrent work must not change sources consumed by an active run.
Do not manufacture work to hide waiting. Use existing command receipts to report
routine validation, scientific execution and remaining uncertainty separately.

## Tools and delivery

Use Apple silicon/macOS and uv; `justfile` owns shared commands. Push performs
static delivery checks without pytest. Missing tools, malformed results and failed
adopted checks block delivery; numerical code-quality scores remain advisory.

`AGENTS.md` owns the documentation budget and retention policy.

## Local scientific checks

Reuse compatible scientific records for unchanged producers and inputs. Run
affected checks in bounded groups with the CLI's existing pytest selection. For
example, one module can be selected with:

```sh
PYTEST_ADDOPTS='-k test_mlx_core' uv run --locked --group qualification fly-brain qualify --output executions/local-core-01
```

Record the full current collected inventory, each selection and completed JUnit
node identities. Require exact coverage by disjoint fresh passes and verified
compatible records, with zero failures/errors/skips. A selected subset does not
certify the whole inventory. Routine hooks do not replace scientific checks.

The runner stops at the first failure, enforces five minutes including setup,
kills its owned process group on expiry and returns unaccepted exit 124.
Retain timed-out runs; untrusted partial counts grant no acceptance. Diagnose
scope and cost before another invocation; avoid repeating unaffected suites.

## Full scientific qualification

```sh
uv run --locked --group qualification python -m tools.qualify_matrix --output executions/matrix-01
uv run --locked --group qualification python -m tools.qualify_matrix --resume-from executions/matrix-01 --reviews executions/matrix-01/reviews --verify-only --output executions/matrix-preflight-01
```

The matrix verifies canonical inputs, source/execution identities and native
scoring, stops on an unaccepted case and rejects incomplete coverage.
Batch input requires accepted compatible singletons 0–3; exact native
phase/final equality suffices for the state budgets. Differences require diagnosis.
No source edits, commits or push-hook stashing while a run consumes those sources.

`--resume-from` validates retained cases against current sources, canonical inputs,
native repeats, scoring and bound artifact hashes. `--verify-only` launches no
engines and grants no matrix acceptance. After it succeeds for the available
cases, omit that flag to continue missing cases in a fresh output directory.
`--reviews` supplies case-named directories of completed bound causal reviews.
Matrix checkpoints record original case paths; the batch tool reads that index
and validates its four corresponding singletons again before execution.

Case records include persisted channel metadata, `launch.json`, `environment.json`,
bound reference build provenance, native replay evidence and `case.json`.
`matrix.json` includes per-case/pooled metrics and 100 ms localization. A first
spike difference needs the prescribed causal decision, bound to the original
artifacts. Preserve the unaccepted raw report and record any reviewed acceptance
separately. Good summary metrics or small threshold margins alone do not establish
acceptance. The implementation agent makes evidence-backed causal decisions;
the escalation conditions in `AGENTS.md` govern optional Astra assistance.

## Diagnostics and outputs

Each diagnostic uses `fly-brain <command> --output executions/<fresh-directory>`:
`probe-accumulation`, `probe-factored`, `probe-bucketed`, `probe-replay`,
`inspect-reference`, `audit-inputs`, `qualify-fan-in`, `qualify-layout-fan-in`,
`qualify-device-layout`, `qualify-connectome-pulse`. Their contract-defined local
scope does not replace full-network qualification.

Use `logs/` only for disposable diagnostics. Keep scientific artifacts, reusable
verification results and failure reports in fresh directories under `executions/`.
Commit/push cleanup never removes execution evidence. Follow `AGENTS.md`
and the retention manifest for unfinished consumers. Report failed, skipped and
incomplete verification honestly.
