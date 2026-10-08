from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fly_brain.infrastructure.output_paths import require_retained_output
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase, QualificationRequest
from fly_brain.simulation.models import ExperimentName


class QualificationOptions(BaseModel):
    model_config = ConfigDict(frozen=True)
    project: Path
    output: Path

    @field_validator('project')
    @classmethod
    def project_contains_qualification(cls, value: Path) -> Path:
        project = value.resolve()
        if not (project / 'tests/qualification').is_dir():
            raise ValueError('Project must contain the qualification suite')
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
    def output_is_retained(self) -> 'QualificationOptions':
        require_retained_output(self.output, self.project)
        return self

    def to_request(self) -> QualificationRequest:
        return QualificationRequest(self.project, self.output)


class ParityOptions(QualificationOptions):
    experiment: ExperimentName = 'sugar'
    duration_s: float = 0.1
    trial: int = Field(default=0, ge=0, le=4)

    @model_validator(mode='after')
    def case_is_prescribed(self) -> 'ParityOptions':
        if (
            self.duration_s not in (0.1, 1.0, 10.0)
            or self.to_case() not in required_cases()
        ):
            raise ValueError('Parity options must select one prescribed frozen case')
        return self

    def to_case(self) -> ParityCase:
        return ParityCase(self.experiment, round(self.duration_s * 10000), self.trial)
