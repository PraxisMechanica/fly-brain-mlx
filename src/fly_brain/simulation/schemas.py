import math
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fly_brain.infrastructure.output_paths import require_retained_output

from .models import ExperimentName, SimulationRequest


class SimulationOptions(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)
    project: Path
    output: Path
    experiment: ExperimentName = 'sugar'
    duration_s: float = Field(default=0.1, gt=0)
    trials: int = Field(default=1, ge=1)
    seed: int = Field(default=20261004, ge=0)

    @field_validator('project')
    @classmethod
    def project_contains_inputs(cls, value: Path) -> Path:
        project = value.resolve()
        for name in ('2025_Completeness_783.csv', '2025_Connectivity_783.parquet'):
            if not (project / 'data' / name).is_file():
                raise ValueError(f'Project must contain data/{name}')
        return project

    @field_validator('output')
    @classmethod
    def output_is_fresh(cls, value: Path) -> Path:
        output = value.resolve()
        if output.exists():
            raise ValueError(
                'Output must be a new directory; existing data is preserved'
            )
        return output

    @model_validator(mode='after')
    def output_is_retained(self) -> 'SimulationOptions':
        require_retained_output(self.output, self.project)
        return self

    @field_validator('duration_s')
    @classmethod
    def duration_has_complete_timesteps(cls, value: float) -> float:
        steps = value * 10000
        if round(steps) < 1 or not math.isclose(
            steps, round(steps), rel_tol=0, abs_tol=1e-9
        ):
            raise ValueError('Duration must contain whole 0.1 ms timesteps')
        return value

    def to_request(self) -> SimulationRequest:
        return SimulationRequest(
            self.project,
            self.output,
            self.experiment,
            self.duration_s,
            self.trials,
            self.seed,
        )
