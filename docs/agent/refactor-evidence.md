# Refactor evidence

The practical architecture refactor is complete through `9f89ef6`. Detailed
commit-by-commit records remain in Git. This summary supplies historical scope;
current implementation evidence and holds belong in `milestone.md`.

- `feebbea` adopted project-specific checks; `d24754d` simplified comparison
  composition; `b439fdf` retired the experimental analyzer and neutral-provider
  prototype. Exact hosted runs `38629545114`, `38630196350` and `38634165371`
  passed their required checks.
- Scientific-source identities and seven independent fixtures were preserved.
  Structural, typing and observation comparisons established their stated
  preservation properties; they did not qualify the 52-case scientific matrix.
- Earlier analyzer findings and incomplete 37-rule proofs belong to the retired
  objective. Current policy is in `architecture-policy.md` and implemented
  enforcement in `quality-coverage.md`.

Consumed raw outputs were deleted after verification. Historical counts and
summaries do not imply those raw proofs survive or establish current numerical
acceptance. Do not rerun old preservation workloads for unrelated changes.
