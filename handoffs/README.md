# M5 handoff

Archive baseline: `6429e722c27e10ee1b7c546ba5da9b40baa5f44d`.
Current M5 results, tiered scope and implemented Eon integration: `milestone.md`.

The 57 manifest-verified files include instructions, baselines, prospective
statistics and the original Eon draft. Extract into a fresh ignored directory:

```sh
shasum -a 256 handoffs/m5-handoff-20261016.tar.gz
mkdir -p executions
mkdir executions/m5-transfer-01
tar -xzf handoffs/m5-handoff-20261016.tar.gz -C executions/m5-transfer-01
```

Expected SHA-256:

```text
9d44f047fdccb26212cde286cb77f6a24a28c623fc02f6e0e965e726c550605d
```

Read `executions/m5-transfer-01/m5-handoff/HANDOFF.txt` for manifest verification,
environment setup and pilot instructions. Commands above supersede captured
Downloads/manual-transfer directions; `6429e72` identifies provenance.

The authorized M5 campaign is complete. Preserve this bundle and ignored
`executions/` evidence. M1 stays paused.
