from pathlib import Path

import pytest

from tests.quality.test_boundaries import source_project
from tests.quality.test_parity_stimulus_boundary import lint


@pytest.mark.parametrize(
    'source',
    ('qualification.session_observer', 'simulation.observations'),
)
def test_local_observation_types_may_depend_on_concrete_backend_values(
    tmp_path: Path, source: str
) -> None:
    config = source_project(
        tmp_path,
        {
            'fly_brain.'
            + source: 'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n'
            '    from fly_brain.simulation.backend import VALUE\n'
        },
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output
