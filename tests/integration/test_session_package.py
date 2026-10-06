import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_session_contract_rules_and_assembly_import_without_engines_or_runtime_files(
    tmp_path: Path,
) -> None:
    source = """
import sys
import fly_brain.simulation.observations
import fly_brain.simulation.observation_ports
import fly_brain.simulation.observation_module
import fly_brain.qualification.ports
import fly_brain.qualification.session_expectations
import fly_brain.qualification.session_blocks
import fly_brain.qualification.session_observer
assert not {'mlx', 'torch', 'brian2', 'pyarrow'} & sys.modules.keys()
"""
    process = subprocess.run(
        [sys.executable, '-c', source],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert not list(tmp_path.iterdir())
