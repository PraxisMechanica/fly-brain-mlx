# Protected scientific sources

Audience: agents and maintainers. The [project architecture policy](architecture-policy.md)
owns design requirements; [quality coverage](quality-coverage.md) owns check scope.

The [scientific manifest](../../tools/code_quality/scientific_sources.json) is the
single owner of five reviewed source hashes and their independent provenance:

- `src/fly_brain/qualification/adapters/brian_reference.py`
- `src/fly_brain/qualification/adapters/torch_reference.py`
- `src/fly_brain/qualification/reference_parameters.py`
- `tests/support/legacy_mlx_observer.py`
- `tests/support/legacy_mlx_ledger.py`

The [source guard](../../tools/code_quality/ownership.py) validates the manifest,
requires this exact protected set, and compares actual file hashes. Missing files,
invalid protection records and unreviewed changes fail. The original hash, kind,
lineage commit and origin text are preserved for every source.

An authorized structural repair may update a reviewed revision only after verifying
scientific preservation, independent lineage and every actual source-identity
consumer. Do not rebaseline a hash merely to silence a check. The
[numerical contract](numerical-contract.md) owns acceptance.

The general ownership registry, role/resource classifiers, declaration/binding
fingerprints and experimental analyzer are removed. Ordinary functions, parameters
and modules need no metadata approval. Ruff, Pyright, project import checks and
automatic affected tests enforce their actual requirements. Required input discovery
still rejects unindexed source/check inputs. A source-hash pass is not full scientific
qualification or a semantic architecture proof.

The former six strict-profile observations are resolved by the project policy:
concrete backend `Advance` types and framework-based `TorchModel` definitions are
accepted; primitive numerical coordinates and serialized fields do not by themselves
establish an identity defect. Keep useful brands and actual mapping, bounds, shape,
order, trial and state checks. No general alias/conversion-origin proof is required.

Preserve the seven active independent regression fixtures and pinned FlyWire inputs.
Use the [developer workflow](development.md) for checks and output handling. The
application remains database-free; file storage needs no database repository layers.
