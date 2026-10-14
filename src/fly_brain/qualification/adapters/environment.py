import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import mlx.core as mx
import torch


def write(output: Path, precision: str) -> None:
    if precision != '0' or os.environ.get('MLX_ENABLE_TF32') != '0':
        raise RuntimeError('Qualification provenance requires MLX_ENABLE_TF32=0')
    project = Path(__file__).resolve().parents[4]
    package = project / 'src/fly_brain'
    sources = {
        '.'.join(
            path.relative_to(package.parent).with_suffix('').parts
        ): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(package.rglob('*.py'))
    }
    for name, module in sys.modules.copy().items():
        if (
            name == 'fly_brain' or name.startswith('fly_brain.')
        ) and module.__file__ is not None:
            path = Path(module.__file__)
            key = name + '.__init__' if path.name == '__init__.py' else name
            if hashlib.sha256(path.read_bytes()).hexdigest() != sources.get(key):
                raise ValueError(f'Loaded qualification source differs: {name}')
    commit = subprocess.check_output(
        ['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True
    ).strip()
    entrypoint = Path(sys.argv[0]).resolve()
    with (output / 'launch.json').open('x') as artifact:
        json.dump(
            {
                'commit': commit,
                'source_root': str(project),
                'entrypoint': str(entrypoint),
                'entrypoint_sha256': hashlib.sha256(entrypoint.read_bytes()).hexdigest()
                if entrypoint.is_file()
                else None,
                'scope': 'Actual launch checkpoint and current source inventory; recorded hashes, rather than commit identity alone, determine source equivalence.',
            },
            artifact,
            indent=2,
            allow_nan=False,
        )
    with (output / 'environment.json').open('x') as artifact:
        json.dump(
            {
                'python': sys.version,
                'platform': platform.platform(),
                'versions': {
                    name: importlib.metadata.version(name)
                    for name in ('mlx', 'mlx-metal', 'numpy', 'brian2', 'torch')
                },
                'MLX_ENABLE_TF32': precision,
                'compilation': 'disabled',
                'device': mx.device_info(),
                'cpu_threads': torch.get_num_threads(),
                'cpu_interop_threads': torch.get_num_interop_threads(),
                'cpu_default_dtype': str(torch.get_default_dtype()),
                'cpu_deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
                'source_sha256': sources,
                'scope': 'Qualification execution with complete fly_brain package source inventory, including sources not loaded in this process. Input load is outside timing; no benchmark or unified-memory claim.',
            },
            artifact,
            indent=2,
            allow_nan=False,
        )
