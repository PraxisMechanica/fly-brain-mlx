from collections.abc import Callable

from importlinter import api

from tests.quality.support import PROJECT
from tools.code_quality.boundaries import Configuration, review
from tools.code_quality.impact import current_graph


def test_actual_mlx_assembly_and_independent_references_are_permitted() -> None:
    read: Callable[[str], object] = vars(api)['read_configuration']
    configuration = Configuration.model_validate(read(str(PROJECT / 'pyproject.toml')))
    graph = current_graph(PROJECT, None)
    implementations = {
        'fly_brain.simulation.backend.engines',
        'fly_brain.simulation.observation_module',
        'fly_brain.qualification.adapters.torch_reference',
        'fly_brain.qualification.adapters.brian_reference',
    }
    assert implementations <= graph.modules
    assert review(configuration, graph, implementations) == 0
