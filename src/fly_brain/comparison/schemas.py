from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import ComparisonRequest


class ComparisonOptions(BaseModel):
    model_config = ConfigDict(frozen=True)

    first: Path
    second: Path
    duration_s: float = Field(gt=0, allow_inf_nan=False)
    trials: int = Field(gt=0)
    tolerance_ms: float = Field(ge=0, allow_inf_nan=False)
    first_label: str = Field(min_length=1)
    second_label: str = Field(min_length=1)

    @field_validator('first', 'second')
    @classmethod
    def existing_file(cls, value: Path) -> Path:
        value = value.resolve()
        if not value.is_file():
            raise ValueError(f'Spike file does not exist: {value}')
        return value

    def to_request(self) -> ComparisonRequest:
        return ComparisonRequest(
            self.first,
            self.second,
            self.duration_s,
            self.trials,
            self.tolerance_ms,
            self.first_label,
            self.second_label,
        )
