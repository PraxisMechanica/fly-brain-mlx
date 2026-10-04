import importlib.metadata
import json
import platform
from dataclasses import dataclass, field
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend.core import COEFFICIENTS

TraceArrays = dict[
    str, NDArray[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]
]


@dataclass
class ArtifactRecorder:
    output: Path | None
    prefix: str = ''
    measurements: dict[str, dict[str, object]] = field(
        default_factory=lambda: dict[str, dict[str, object]]()
    )

    def record(
        self, name: str, arrays: TraceArrays, measurements: dict[str, object]
    ) -> None:
        name = self.prefix + name
        self.measurements[name] = measurements
        if self.output is not None:
            with (self.output / f'{name}.npz').open('xb') as destination:
                np.savez_compressed(destination, **arrays)

    def annotate(self, name: str, key: str, value: object) -> None:
        self.measurements[self.prefix + name][key] = value

    def finish(self, filename: str, execution: str) -> None:
        if self.output is None:
            return
        report = {
            'execution': execution,
            'mlx': importlib.metadata.version('mlx'),
            'mlx_metal': importlib.metadata.version('mlx-metal'),
            'brian2': importlib.metadata.version('brian2'),
            'numpy': np.__version__,
            'python': platform.python_version(),
            'platform': platform.platform(),
            'device': mx.device_info(),
            'MLX_ENABLE_TF32': '0',
            'coefficients_float32': dict(zip('abc', COEFFICIENTS, strict=True)),
            'measurements': self.measurements,
        }
        with (self.output / filename).open('x') as destination:
            json.dump(report, destination, indent=2)
            destination.write('\n')
