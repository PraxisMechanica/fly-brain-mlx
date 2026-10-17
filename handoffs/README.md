# M5 handoff

The archive captures baseline `6429e722c27e10ee1b7c546ba5da9b40baa5f44d`.
Current M5 results and the replacement tiered scope are in `milestone.md`.

The bundle includes full instructions,
57 manifest-verified files, scientific baselines, prospective statistics and the
Eon packaging draft. Extract into a fresh ignored directory:

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

Read `executions/m5-transfer-01/m5-handoff/HANDOFF.txt`, then follow its manifest
verification, environment setup and bounded pilot instructions. Its captured
Downloads/manual-transfer directions are superseded by the commands above;
`6429e72` identifies scientific provenance, not the delivery checkout to select.
No separate file transfer is needed.

The user subsequently authorized the necessary M5 campaign without approval
pauses; it is complete. Preserve this baseline bundle and new ignored
`executions/` evidence. The M1 goal stays paused. Eon integration remains a draft.
