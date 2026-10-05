import hashlib
import importlib.metadata
import json
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from packaging.requirements import Requirement

from fly_brain.simulation.models import Connectome, Stimulus

from .observer_evidence import array_record
from .observer_stream import StreamShape


def file_record(path: Path) -> dict[str, str | int]:
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {'sha256': digest.hexdigest(), 'bytes': size}


def installed_packages() -> dict[str, object]:
    pending = ['brian2']
    packages: dict[str, object] = {}
    while pending:
        distribution = importlib.metadata.distribution(pending.pop())
        name = distribution.metadata['Name'].lower()
        if name in packages:
            continue
        paths = distribution.files
        if paths is None:
            raise ValueError(f'Cannot bind installed reference dependency: {name}')
        packages[name] = {
            'version': distribution.version,
            'files': {
                str(path): file_record(Path(str(distribution.locate_file(path))))
                for path in sorted(paths)
                if path.suffix != '.pyc' and '__pycache__' not in path.parts
            },
        }
        for requirement in distribution.requires or ():
            dependency = Requirement(requirement)
            if dependency.marker is None or dependency.marker.evaluate({'extra': ''}):
                pending.append(dependency.name)
    return packages


def generated_files(directory: Path) -> dict[str, dict[str, str | int]]:
    return {
        str(path.relative_to(directory)): file_record(path)
        for path in sorted(directory.rglob('*'))
        if path.is_file()
        and (
            path.suffix in ('.cpp', '.c', '.h', '.hpp')
            or path.name in ('makefile', 'make.deps')
            or 'static_arrays' in path.relative_to(directory).parts
        )
    }


def create(
    connectome: Connectome,
    stimulus: Stimulus,
    silenced: tuple[int, ...],
    shape: StreamShape,
    files: Mapping[str, str],
    directory: Path,
    context: Mapping[str, object],
) -> tuple[str, dict[str, object]]:
    record: dict[str, object] = {
        'engine': 'brian2-cpp-standalone',
        'inputs': {
            name: array_record(getattr(connectome, name))
            for name in (
                'neuron_ids',
                'sources',
                'destinations',
                'counts',
                'weights_mv',
            )
        },
        'events': array_record(stimulus.events),
        'targets': list(stimulus.targets),
        'silenced': list(silenced),
        'dt_ms': 0.1,
        'shape': asdict(shape),
        'native_files': dict(files),
        'generated': generated_files(directory),
        'build_context': dict(context),
    }
    encoded = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest(), record
