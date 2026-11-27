from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.question_choice import (
    ChoiceCreate,
    ChoiceResponse,
    EmployeeChoiceResponse,
)


class QuestionCreate(BaseModel):
    question_text: str = Field(min_length=1)
    question_order: int = Field(gt=0)
    marks: int = Field(default=1, gt=0)
    choices: list[ChoiceCreate] = Field(min_length=4, max_length=4)

    model_config = ConfigDict(extra="forbid")

    @field_validator("question_text")
    @classmethod
    def reject_blank_question_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question_text must not be empty")
        return value

    @model_validator(mode="after")
    def validate_choices(self):
        if len(self.choices) != 4:
            raise ValueError("A question must contain exactly four choices")

        if sum(choice.is_correct for choice in self.choices) != 1:
            raise ValueError("Exactly one choice must be correct")

        choice_orders = {choice.choice_order for choice in self.choices}
        if choice_orders != {1, 2, 3, 4}:
            raise ValueError("Choice orders must contain each value from 1 to 4")

        return self


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(default=None, min_length=1)
    question_order: int | None = Field(default=None, gt=0)
    marks: int | None = Field(default=None, gt=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("question_text")
    @classmethod
    def reject_blank_question_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("question_text must not be empty")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set:
            raise ValueError("At least one question field must be provided")

        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Question fields cannot be null")

        return self


class QuestionResponse(BaseModel):
    question_id: UUID
    assignment_id: UUID
    question_text: str
    question_order: int
    marks: int
    choices: list[ChoiceResponse]

    model_config = ConfigDict(from_attributes=True)


class EmployeeQuestionResponse(BaseModel):
    question_id: UUID
    question_text: str
    question_order: int
    marks: int
    choices: list[EmployeeChoiceResponse]

    model_config = ConfigDict(from_attributes=True)
