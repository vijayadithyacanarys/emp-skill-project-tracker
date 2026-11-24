from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


AllocationStatus = Literal["planned", "active", "completed", "cancelled"]



class EmployeeProjectAllocationCreate(BaseModel):
    employee_id: UUID
    project_id: UUID
    allocation_percentage: Decimal = Field(
        gt=Decimal("0"),
        le=Decimal("100"),
        max_digits=5,
        decimal_places=2
    )
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class EmployeeProjectAllocationUpdate(BaseModel):
    allocation_percentage: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        le=Decimal("100"),
        max_digits=5,
        decimal_places=2
    )
    start_date: date | None = None
    end_date: date | None = None


    @model_validator(mode="after")
    def validate_update(self):
        for field in (
            "allocation_percentage",
            "start_date",
            "end_date"
        ):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
            
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must be on or after start_date")
        return self


class EmployeeProjectAllocationStatusUpdate(BaseModel):
    status: AllocationStatus


class EmployeeProjectAllocationResponse(BaseModel):
    allocation_id: UUID
    employee_id: UUID
    project_id: UUID
    allocation_percentage: Decimal
    assigned_by: UUID 
    status: AllocationStatus
    start_date: date
    end_date: date

    model_config = ConfigDict(from_attributes=True)
