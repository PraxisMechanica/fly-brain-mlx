import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

import numpy as np

from fly_brain.qualification.models import InputAuditArtifact, MappedArray


class InputAuditRepository:
    def create_output(self, output: Path, /) -> None:
        output.mkdir(parents=True, exist_ok=False)

    def write_arrays(self, output: Path, arrays: Mapping[str, MappedArray], /) -> Path:
        artifact = output / 'mapped-inputs.npz'
        with artifact.open('xb') as destination:
            np.savez_compressed(destination, **arrays)
        return artifact

    def read_artifact_identity(self, artifact: Path, /) -> InputAuditArtifact:
        return InputAuditArtifact(
            str(artifact), hashlib.sha256(artifact.read_bytes()).hexdigest()
        )

    def write_report(self, output: Path, report: dict[str, object], /) -> None:
        with (output / 'mapping.json').open('x') as destination:
            json.dump(report, destination, indent=2)
            destination.write('\n')
