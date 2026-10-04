from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator

from fly_brain.qualification.models import QualificationRequest


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

    def to_request(self) -> QualificationRequest:
        return QualificationRequest(self.project, self.output)
