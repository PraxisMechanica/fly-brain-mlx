from pathlib import Path

from tests.quality.test_boundaries import source_project
from tests.quality.test_parity_stimulus_boundary import lint


def test_concrete_observation_types_need_no_generic_neutral_wrapper(
    tmp_path: Path,
) -> None:
    config = source_project(
        tmp_path,
        {
            'fly_brain.simulation.observations': 'from fly_brain.simulation.backend import VALUE\n',
            'fly_brain.qualification.ports': 'from fly_brain.simulation.observations import VALUE\n',
        },
    )
    result, output = lint(tmp_path, config)
    assert result == 0, output
