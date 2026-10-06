from pathlib import Path

from .models import Connectome, InputPin
from .ports import ConnectomeReaderFactory


def load_pinned_inputs(
    project: Path, reader_factory: ConnectomeReaderFactory
) -> tuple[Connectome, InputPin]:
    reader = reader_factory()
    pin = InputPin(
        '52b0ac6094cd32c546f8d4c341e094376f48f4e791f8db9b166de5dff8199ea4',
        'efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347',
        138639,
        15091983,
    )
    connectome = reader(
        project / 'data/2025_Completeness_783.csv',
        project / 'data/2025_Connectivity_783.parquet',
        pin,
    )
    return connectome, pin
