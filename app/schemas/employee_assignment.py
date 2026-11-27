from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.assignment import AssignmentResponse
from app.schemas.assignment_question import EmployeeQuestionResponse


AssignmentStatus = Literal["assigned", "submitted"]
AssignmentResult = Literal["passed", "failed"]


class AssignmentAllocate(BaseModel):
    employee_id: UUID
    assignment_id: UUID

    model_config = ConfigDict(extra="forbid")


class EmployeeAssignmentResponse(BaseModel):
    employee_assignment_id: UUID
    employee_id: UUID
    assignment_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    status: AssignmentStatus
    score: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    result: AssignmentResult | None
    submitted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class EmployeeAssignmentDetailResponse(EmployeeAssignmentResponse):
    assignment: AssignmentResponse

    model_config = ConfigDict(from_attributes=True)


class EmployeeAssignmentContentResponse(BaseModel):
    assignment_id: UUID
    title: str
    description: str | None
    pass_percentage: int
    questions: list[EmployeeQuestionResponse]

    model_config = ConfigDict(from_attributes=True)


class EmployeeAssignedAssignmentResponse(BaseModel):
    employee_assignment_id: UUID
    assignment_id: UUID
    assignment: EmployeeAssignmentContentResponse
    assigned_at: datetime
    status: AssignmentStatus
    score: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    result: AssignmentResult | None
    submitted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AssignmentSubmission(BaseModel):
    answers: dict[UUID, UUID]

    model_config = ConfigDict(extra="forbid")

    @field_validator("answers")
    @classmethod
    def require_answers(cls, value: dict[UUID, UUID]) -> dict[UUID, UUID]:
        if not value:
            raise ValueError("At least one question answer must be provided")
        return value


class AssignmentResultResponse(BaseModel):
    employee_assignment_id: UUID
    assignment_id: UUID
    score: Decimal = Field(
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    result: AssignmentResult
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
