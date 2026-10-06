# Refactor documentation audit — 2026-10-06

Reviewer: `architecture_ownership`, inherited GPT-6.1 Sol at `xhigh`.
Requested parent checkpoint: `c5296da3fd66ff3d48348a919bd1a44e5b01b496`.
Actual reviewed checkpoint: `f2de8f01a2e5311a94ac4e520572925d23ce6f78`,
which incorporates the runtime-resource review. Local record starts at
`3613b96dac3c6c9bcc411301de3f828d25846839`. Confidence: 97% in the four
bounded corrections below. Only this audit record is written by the reviewer;
the parent owns all live document/configuration changes.

The delivered organization remains appropriate. Root `AGENTS.md` contains
project-specific scope, scientific preservation, non-production authorization,
model/review settings and remotes. Root `README.md` serves human installation,
pinned inputs, simulation and comparison, with status/developer links. Their
instructions agree with current source/configuration; neither needs a rewrite.
The scientific contract, historical notices and existing evidence stay intact.

## Material findings and smallest corrections

1. **The active milestone again contains a chronological checkpoint log.**
   `milestone.md:78–261` accumulates old test counts, PR/stack delivery, hosted
   run history, refactor source statistics and failed/repaired hook attempts.
   It repeats evidence already owned by history and quality coverage, and embeds
   completed imperatives such as integrating the already delivered foundations.
   The initial parallel component summary at `263–284` repeats the assignment
   owner while describing completed initial implementation scopes.

   Move the complete `78–261` blocks, preserving text/numbers/evidence and
   rebasing only relative links, into the existing
   `docs/agent/history/milestones.md` under a unique dated refactor/enforcement
   checkpoint heading bound to `f2de8f0`. Preserve its existing archive and
   historical notices. Replace those blocks in the active milestone with a
   short latest-delivery/coverage snapshot linked to quality coverage, source
   ownership and the checkpoint history. Keep active direct-main delivery,
   parent serial integration, standing authorization, full COV002 and the
   feature/numerical hold explicit. Keep `56–75` scientific acceptance/failure
   and suspended-process state, current goal/completion criteria, later science
   constraints, milestone table and all scientific numeric expressions intact.
   Replace `263–284` with a short pointer to the exclusive assignment owner.
   In `288–292`, remove the completed metric/index weakening work from the
   current to-do and the incorrect “clock repair below” reference; name remaining
   structural/type/alias/effect/control-flow integration and hosted verification.
   Continue requiring all existing checks; completed fixtures are not retired.

2. **The assignment record lacks an explicit current handoff snapshot.**
   `docs/agent/handoffs/parallel-refactor-20261006.md:44–47` correctly describes
   parent `471ab69`, but still says `ffbc2fe` is being integrated and `d6e8d43`
   awaits the next join. Its live follow-up table at `55` still assigns the now
   integrated runtime ownership decision. Reading only the file that owns
   current scopes can suggest repeating completed work.

   Keep the dated paragraph as historical; label it as an initial handoff
   checkpoint and add the current integration snapshot: native identities at
   `a9453aa`, ownership at `c5296da`, runtime decision at `f2de8f0`. Mark the
   runtime review complete and this documentation review as a separate read-only
   handoff. Retain the native-types and session worker assignments, exact
   exclusive files and the reference/probe prerequisites at `67–73`. State that
   their unmerged implementation/adoption results remain provisional. Do not
   copy the detailed scopes back into the active milestone or reassign them.

3. **Developer ownership still gives result presentation to the CLI.**
   `docs/agent/development.md:102` says `cli.py` owns “result presentation”.
   Current `cli.py:95,108,112,133` returns the composed owned command's result;
   `comparison/commands.py:11–13`, `simulation/commands.py:8–20` and
   `qualification/commands.py:9–39` print results and map command exit status.
   Bootstrap constructs these adapters; it does not execute their workflows.
   Also, `development.md:50` omits source-only quality tests from the default
   pytest description, while `pyproject.toml:63` includes `tests/quality`.

   Change the CLI table entry to “Argument parsing, validated request/command
   selection, one composed owned command call, and exit propagation”. Add owned
   command adapters/result presentation to the three domain entries, retaining
   bootstrap's composition/configuration role. Use “network/stimulus values”
   rather than implying every array-bearing frozen record is deeply immutable.
   Add source-only quality tests to the default pytest scope sentence. Point
   detailed source classifications to `architecture-ownership.md`; retain this
   table as the small developer map. Do not change CLI examples, output fields,
   command behavior or the scientific-suite distinction.

4. **Quality coverage repeats ownership semantics and understates delivered inputs.**
   `quality-coverage.md:29,37–38` frames documented roots as the ownership
   mechanism and ownership/provenance reconciliation as missing. Its later
   `159–188` and `architecture-ownership.md:108–121,137–180` both narrate source
   counts, exports, frozen provenance, resource decisions and debt. The old
   3,770/thirteen-finding and later 3,771/eleven-finding counts are legitimate
   different checkpoints, not a scientific contradiction, but only the latter
   is the current registry snapshot.

   Keep current classifications, exact counts/exports/resources/provenance and
   classification debt in `architecture-ownership.md` and the canonical registry.
   In quality coverage, keep the loader/index rejection mechanisms, executed
   fixtures, weakening evidence and their exact dated proof references; replace
   copied ownership semantics/counts with a link to their owner. Update the
   OWN/CODE/COV table cells to distinguish implemented exact file/named-declaration
   and syntactic-binding/provenance reconciliation from still-missing complete
   binding, placement, type/call/alias/effect/historical-resolution enforcement.
   Replace “Inventory every first-party file…” at `192–193` with using and
   maintaining the reviewed inventory while completing the missing analyses.
   Preserve the complete 37-rule COV002 result and every outstanding finding.
   In the agent index's ownership table, describe quality coverage as executable
   mechanisms and analysis limits, rather than centering the repaired clock
   finding. No new documentation layer is needed.

## Final document ownership map

| Existing document | Sole active responsibility |
| --- | --- |
| `AGENTS.md` | Project scope, scientific/data preservation, project authorization, model/review policy and remotes |
| `README.md` | Human installation, inputs, run/compare usage, licenses and concise status links |
| `milestone.md` | Active bounded goal, holds, acceptance status, latest delivery/evidence pointers and ordered next work |
| `docs/agent/README.md` | Navigation and document ownership; no second active plan or verification ledger |
| `numerical-contract.md` | Scientific semantics, equations, precision, stimuli, repeatability and fixed acceptance gates |
| `development.md` | Actual environment/check commands, scientific command scope and concise command/code ownership |
| `typing.md` | Exact third-party stubs/suppressions and their proof limits |
| `quality-coverage.md` | Rule/gate mechanisms, rejection/weakening evidence, missing analysis and COV002 |
| `architecture-ownership.md` plus `tools/architecture/ownership.json` | Reviewed source/role/export/resource/identifier meanings, provenance and classification debt |
| `handoffs/parallel-refactor-20261006.md` | Current exclusive assignments, committed handoff state and integration prerequisites |
| `history/milestones.md` and other existing history/review briefs | Dated chronology and original decisions, including superseded holds/branch/PR/manual-switch guidance |
| Existing `docs/evidence` records | Original source-bound results and verification; no new permission or transferred acceptance |

All shorthand document names above are under `docs/agent/`. Proposed live edit
footprint is exactly `milestone.md`, `docs/agent/history/milestones.md`,
`docs/agent/handoffs/parallel-refactor-20261006.md`, `docs/agent/development.md`,
`docs/agent/quality-coverage.md` and the agent index. Root policy/README,
scientific contract, typing rationale, implementation/configuration, original
references, data and retained evidence need no edit for these findings.

## Verification and limits

Source inspection covered the current documents, command adapters/dispatch,
configured default tests, shared check, hooks and hosted workflow. The historical
notices already make old branch/PR/model/remote/permission guidance historical;
do not rewrite preserved prompts or rename original refs to modern conventions.
The active direct-main delivery and current project-specific authorization/model
guidance are compatible. Session/native-type source behavior remains provisional
until its assigned committed evidence and adoption prerequisites are verified.

A static scan of all 22 authored Markdown documents found 743 inline local
destinations/heading anchors, all resolving; no reference-style definitions were
found. Relevant correction destinations were opened and read. No link fix is
proposed. Binary evidence was checked for destination existence, not reinterpreted;
external URLs and installation/scientific execution were not tested. After the
proposed relocation, rebase local links and rerun destination/anchor checks;
preserve original scientific text, tables, numeric expressions and all evidence.

Fresh external review evidence is retained in
`/private/tmp/fly-brain-refactor-documentation-links-20261006-01.json` and
`/private/tmp/fly-brain-refactor-documentation-source-review-20261006-01.json`.
The document hashes were stable through review. The required native commit hook
runs the unchanged local source gate; its raw output is retained at
`/private/tmp/fly-brain-refactor-documentation-native-commit-20261006-01.log` and
its completion result accompanies the committed handoff. This is a documentation
audit, not implemented corrections, whole-application architecture approval or
new scientific acceptance.
