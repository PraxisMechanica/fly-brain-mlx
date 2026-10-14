from pathlib import Path
from types import ModuleType
from typing import NoReturn

import numpy as np
import pytest

from fly_brain.simulation.identifiers import FlyWireIds64, NeuronRows32
from fly_brain.simulation.models import Connectome, InputPin
from tests.integration.test_fan_in_grouping import NATIVE, SOURCE, check_types
from tests.integration.test_fan_in_grouping import probe as probe
from tests.quality.support import PROJECT
from tests.quality.test_input_audit_boundary import TARGETS, contract
from tests.quality.test_input_audit_boundary import sources as mapping_sources
from tests.quality.test_parity_stimulus_boundary import lint

pytestmark = pytest.mark.unit
RULE = 'DEP003/ROLE005: Fan-in analysis uses owned mapping services'
SOURCES = (
    'fly_brain.qualification.input_patterns',
    'fly_brain.qualification.adapters.fan_in_probe',
)
PURE = """{imports}
from fly_brain.qualification.input_patterns import InputPatterns, analyze_inputs, prepare_inputs
from fly_brain.simulation.models import Connectome
def use(network: Connectome) -> InputPatterns:
    return analyze_inputs(prepare_inputs(network), absolute_counts={value})
"""


def sources(root: Path, source: str, target: str, code: str) -> Path:
    config = mapping_sources(root, target, code, source=source)
    for name in set(SOURCES) - {source}:
        (root / 'src' / Path(*name.split('.')).with_suffix('.py')).write_text(
            'VALUE = 1\n'
        )
    config.write_text(contract(RULE))
    return config


@pytest.mark.parametrize('source', SOURCES)
@pytest.mark.parametrize('target', TARGETS)
def test_native_mapping_contract_rejects_each_target_then_repairs(
    tmp_path: Path, source: str, target: str
) -> None:
    config = sources(
        tmp_path, source, target, f'from {target} import VALUE as hidden\n'
    )
    result, output = lint(tmp_path, config)
    assert (
        result != 0,
        RULE in output,
        source in output,
        target in output,
        '(l.1)' in output,
    ) == (True,) * 5
    (tmp_path / 'src' / Path(*source.split('.')).with_suffix('.py')).write_text(
        'from fly_brain.qualification.ports import VALUE\n'
    )
    assert lint(tmp_path, config)[0] == 0


def test_transitive_reexport_weakening_close_literal_and_actual_sources(
    tmp_path: Path,
) -> None:
    config = sources(
        tmp_path,
        SOURCES[0],
        TARGETS[0],
        'from fly_brain.qualification.mapping_helper import VALUE\n',
    )
    result, output = lint(tmp_path, config)
    assert (
        result != 0,
        SOURCES[0] in output,
        TARGETS[0] in output,
        'mapping_helper' in output,
        '(l.1)' in output,
    ) == (True,) * 5
    config.write_text(
        contract(RULE).replace(
            'allow_indirect_imports = false', 'allow_indirect_imports = true'
        )
    )
    assert lint(tmp_path, config)[0] == 0
    config.write_text(contract(RULE))
    (tmp_path / 'src/fly_brain/qualification/input_patterns.py').write_text(
        '# import simulation.mapping\nVALUE = "absolute_count_sums"\n'
    )
    assert (lint(tmp_path, config)[0], lint(PROJECT, config)[0]) == (0, 0)


def test_required_count_reader_rejects_omission_result_then_repairs_and_weakens(
    tmp_path: Path,
) -> None:
    source = SOURCE.read_text()
    (tmp_path / 'api.py').write_text(source)
    supplied = NATIVE.format(keyword=', read_grouping=reader')
    missing = supplied.replace(
        ', read_absolute_counts=build_absolute_count_reader()', '', 1
    ).replace('build_absolute_count_reader, ', '', 1)
    check_types(tmp_path, missing, 1, 'consumer.py:', '"read_absolute_counts"')
    check_types(tmp_path, supplied, 0)
    wrong = supplied.replace(
        'read_absolute_counts=build_absolute_count_reader()',
        'read_absolute_counts=lambda network: 0',
        1,
    )
    check_types(tmp_path, wrong, 1, 'consumer.py:', 'reportArgumentType')
    weakened = source.replace(
        'from fly_brain.simulation.models import Connectome, InputPin',
        'from fly_brain.simulation.input_service import read_absolute_counts\n'
        'from fly_brain.simulation.models import Connectome, InputPin',
    ).replace(
        'read_absolute_counts: AbsoluteCountReader,',
        'read_absolute_counts: AbsoluteCountReader = read_absolute_counts,',
    )
    assert weakened != source
    (tmp_path / 'api.py').write_text(weakened)
    check_types(tmp_path, missing, 0)


@pytest.mark.parametrize(
    'imports,value,status,diagnostic',
    (
        (
            'from fly_brain.simulation.module import build_absolute_count_reader',
            'build_absolute_count_reader()',
            1,
            'reportArgumentType',
        ),
        (
            'import numpy as np',
            'np.zeros(network.neuron_ids.size, dtype=np.float32)',
            1,
            'reportArgumentType',
        ),
        (
            'from fly_brain.simulation.module import build_absolute_count_reader',
            'build_absolute_count_reader()(network)',
            0,
            '0 errors',
        ),
        (
            'import numpy as np',
            'np.zeros(network.neuron_ids.size, dtype=np.int64)',
            0,
            '0 errors',
        ),
    ),
)
def test_pure_completion_requires_data_without_accepting_callbacks(
    tmp_path: Path, imports: str, value: str, status: int, diagnostic: str
) -> None:
    check_types(tmp_path, PURE.format(imports=imports, value=value), status, diagnostic)


def test_real_failed_prefix_precedes_every_reader(
    tmp_path: Path, probe: ModuleType
) -> None:
    network = Connectome(
        FlyWireIds64(np.array([10], dtype=np.int64)),
        NeuronRows32(np.array([], dtype=np.int32)),
        NeuronRows32(np.array([], dtype=np.int32)),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    calls: list[str] = []

    def forbidden(*values: object) -> NoReturn:
        calls.append('collaborator')
        raise AssertionError('Failed prefix must not acquire inputs')

    with pytest.raises(IndexError, match='index 0 out-of-bounds in add.reduceat'):
        probe.run(
            network,
            InputPin('csv', 'parquet', 1, 0),
            tmp_path / 'fan-in',
            '0',
            build_cases=forbidden,
            read_grouping=forbidden,
            read_absolute_counts=forbidden,
        )
    assert calls == []
