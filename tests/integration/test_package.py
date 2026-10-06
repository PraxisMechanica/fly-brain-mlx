import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_installed_imports_have_no_engine_or_file_side_effects(tmp_path: Path) -> None:
    source = """
import sys
import fly_brain.simulation.models
import fly_brain.simulation.experiments
import fly_brain.simulation.stimuli
import fly_brain.simulation.service
import fly_brain.simulation.ports
import fly_brain.simulation.input_service
import fly_brain.simulation.commands
import fly_brain.simulation.module
import fly_brain.qualification.models
import fly_brain.qualification.service
import fly_brain.qualification.ports
import fly_brain.qualification.commands
import fly_brain.qualification.module
import fly_brain.comparison.models
import fly_brain.comparison.service
import fly_brain.comparison.ports
import fly_brain.comparison.reporting
import fly_brain.comparison.commands
import fly_brain.comparison.module
import fly_brain.cli
assert not {'mlx', 'torch', 'brian2', 'pyarrow'} & sys.modules.keys()
"""
    result = subprocess.run(
        [sys.executable, '-c', source],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not list(tmp_path.iterdir())


def test_installed_help_exposes_only_supported_commands(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, '-m', 'fly_brain', '--help'],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert 'qualify' in result.stdout and 'compare' in result.stdout
    assert 'simulate' in result.stdout
    assert 'cuda' not in result.stdout.lower()
