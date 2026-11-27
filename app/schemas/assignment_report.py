from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.employee_assignment import AssignmentResult, AssignmentStatus


class ManagerEmployeeIdentityResponse(BaseModel):
    employee_id: UUID
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class ManagerEmployeeAssignmentResponse(BaseModel):
    employee_assignment_id: UUID
    employee: ManagerEmployeeIdentityResponse
    status: AssignmentStatus
    score: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
    )
    result: AssignmentResult | None
    assigned_at: datetime
    submitted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ManagerAssignmentReportResponse(BaseModel):
    assignment_id: UUID
    title: str
    employee_assignments: list[ManagerEmployeeAssignmentResponse]

    model_config = ConfigDict(from_attributes=True)
