# M5 handoff

Use `main` containing this directory. Scientific sources match baseline
`6429e722c27e10ee1b7c546ba5da9b40baa5f44d`; keep the delivery checkout.

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

M5 qualification remains pending. Get human approval before work expected over
two hours. Preserve this bundle while its M5 qualification/reuse consumers remain.
The M1 goal stays paused; normal generated runs remain under ignored `executions/`.
