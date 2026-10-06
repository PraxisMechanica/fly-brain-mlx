import json

from .models import SimulationRequest
from .ports import SimulationUseCase


def simulation(request: SimulationRequest, use_case: SimulationUseCase) -> int:
    result = use_case(request)
    print(
        json.dumps(
            {
                'spike_file': str(result.spike_file),
                'spikes': result.spikes,
                'active_neurons': result.active_neurons,
                'elapsed_s': result.elapsed_s,
            },
            indent=2,
        )
    )
    return 0
