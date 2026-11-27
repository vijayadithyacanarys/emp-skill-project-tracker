from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ChoiceCreate(BaseModel):
    choice_text: str = Field(min_length=1)
    choice_order: int = Field(ge=1, le=4)
    is_correct: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("choice_text")
    @classmethod
    def reject_blank_choice_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("choice_text must not be empty")
        return value


class ChoiceUpdate(BaseModel):
    choice_text: str | None = Field(default=None, min_length=1)
    choice_order: int | None = Field(default=None, ge=1, le=4)
    is_correct: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("choice_text")
    @classmethod
    def reject_blank_choice_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("choice_text must not be empty")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one choice field must be provided")

        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Choice fields cannot be null")

        return self


class ChoiceResponse(BaseModel):
    choice_id: UUID
    question_id: UUID
    choice_text: str
    choice_order: int
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


class EmployeeChoiceResponse(BaseModel):
    choice_id: UUID
    choice_text: str

    model_config = ConfigDict(from_attributes=True)
