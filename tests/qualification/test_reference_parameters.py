import ast
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType

import pytest

from fly_brain.qualification import reference_parameters
from fly_brain.qualification.adapters import torch_reference
from tests.support.reference_baseline import ORIGINAL_SHA256, original_source
from tests.support.reference_baseline import original as original

pytestmark = [pytest.mark.integration, pytest.mark.reference]


def test_factory_preserves_original_ast_order_scalar_types_and_fresh_values(
    original: tuple[ModuleType, ModuleType],
) -> None:
    baseline, _ = original
    previous = ast.parse(original_source('torch_reference'))
    current = ast.parse(Path(torch_reference.__file__).read_bytes())
    factory = next(
        node
        for node in previous.body
        if isinstance(node, ast.FunctionDef) and node.name == 'model_parameters'
    )
    extracted = ast.parse(Path(reference_parameters.__file__).read_bytes()).body

    def dump(node: ast.AST) -> str:
        return ast.dump(node, include_attributes=False)

    assert list(map(dump, extracted)) == [dump(factory)]
    assert list(map(dump, current.body)) == [
        dump(node) for node in previous.body if node is not factory
    ]
    assert not hasattr(torch_reference, 'model_parameters')
    expected = baseline.model_parameters()
    first = reference_parameters.model_parameters()
    second = reference_parameters.model_parameters()

    def typed(
        values: Mapping[str, float],
    ) -> tuple[tuple[str, type[object], float], ...]:
        return tuple((key, type(value), value) for key, value in values.items())

    assert len(first) == 10 and typed(first) == typed(expected) == typed(second)
    assert type(first['scalePoisson']) is int and first['scalePoisson'] == 250
    assert first is not second and first is not expected
    first['scalePoisson'] = 0
    assert typed(second) == typed(expected)
    print(
        json.dumps(
            {
                'baseline': ORIGINAL_SHA256,
                'factory_ast': hashlib.sha256(dump(factory).encode()).hexdigest(),
                'ordered_values': list(expected.items()),
            }
        )
    )
