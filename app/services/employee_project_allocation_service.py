from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.project import Project
from app.models.employee_project_allocation import EmployeeProjectAllocation

from app.schemas.employee_project_allocation import (
    EmployeeProjectAllocationCreate,
    EmployeeProjectAllocationUpdate,
    EmployeeProjectAllocationStatusUpdate,
)

def validate_employee_and_project(
    db: Session,
    employee_id: UUID,
    project_id: UUID
):
    employee = db.scalar(
        select(Employee).where(
            Employee.employee_id == employee_id
        )
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    project = db.scalar(
        select(Project).where(
            Project.project_id == project_id
        )
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return employee, project


def validate_allocation_capacity(
    db: Session,
    employee_id: UUID,
    allocation_percentage: Decimal,
    start_date,
    end_date,
    exclude_allocation_id: UUID | None = None
):
    query = select(
        func.coalesce(
            func.sum(
                EmployeeProjectAllocation.allocation_percentage
            ),
            0
        )
    ).where(
        EmployeeProjectAllocation.employee_id == employee_id,
        EmployeeProjectAllocation.status.in_(["planned", "active"]),
        EmployeeProjectAllocation.start_date <= end_date,
        EmployeeProjectAllocation.end_date >= start_date
    )

    if exclude_allocation_id:
        query = query.where(
            EmployeeProjectAllocation.allocation_id != exclude_allocation_id
        )

    existing_allocation = db.scalar(query)

    total_allocation = (
        Decimal(str(existing_allocation))
        + allocation_percentage
    )

    if total_allocation > Decimal("100"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Employee already has {existing_allocation}% allocation "
                f"during this period. Adding {allocation_percentage}% "
                f"would exceed the 100% limit."
            )
        )


def create_allocation(
    db: Session,
    allocation: EmployeeProjectAllocationCreate,
    admin_id: UUID
):
    try:
        # Lock the employee row to reduce concurrent over-allocation.
        employee = db.scalar(
            select(Employee)
            .where(Employee.employee_id == allocation.employee_id)
            .with_for_update()
        )

        if not employee:
            raise HTTPException(
                status_code=404,
                detail="Employee not found"
            )

        project = db.scalar(
            select(Project).where(
                Project.project_id == allocation.project_id
            )
        )

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        validate_allocation_capacity(
            db=db,
            employee_id=allocation.employee_id,
            allocation_percentage=allocation.allocation_percentage,
            start_date=allocation.start_date,
            end_date=allocation.end_date
        )

        new_allocation = EmployeeProjectAllocation(
            employee_id=allocation.employee_id,
            project_id=allocation.project_id,
            allocation_percentage=allocation.allocation_percentage,
            assigned_by=admin_id,
            start_date=allocation.start_date,
            end_date=allocation.end_date
        )

        db.add(new_allocation)
        db.commit()
        db.refresh(new_allocation)

        return new_allocation

    except Exception:
        db.rollback()
        raise


def get_allocation_by_id(
    db: Session,
    allocation_id: UUID
):
    allocation = db.get(
        EmployeeProjectAllocation,
        allocation_id
    )

    if not allocation:
        raise HTTPException(
            status_code=404,
            detail="Allocation not found"
        )

    return allocation


def get_employee_allocations(
    db: Session,
    employee_id: UUID
):
    employee = db.get(Employee, employee_id)

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return db.scalars(
        select(EmployeeProjectAllocation).where(
            EmployeeProjectAllocation.employee_id == employee_id
        )
    ).all()


def get_project_allocations(
    db: Session,
    project_id: UUID
):
    project = db.get(Project, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return db.scalars(
        select(EmployeeProjectAllocation).where(
            EmployeeProjectAllocation.project_id == project_id
        )
    ).all()


def update_allocation(
    db: Session,
    allocation_id: UUID,
    allocation_data: EmployeeProjectAllocationUpdate
):
    try:
        allocation = db.get(
            EmployeeProjectAllocation,
            allocation_id
        )

        if not allocation:
            raise HTTPException(
                status_code=404,
                detail="Allocation not found"
            )

        # Lock the employee row before checking capacity.
        db.scalar(
            select(Employee.employee_id)
            .where(Employee.employee_id == allocation.employee_id)
            .with_for_update()
        )

        update_data = allocation_data.model_dump(
            exclude_unset=True
        )

        # Combine existing values with submitted values.
        new_percentage = update_data.get(
            "allocation_percentage",
            allocation.allocation_percentage
        )

        new_start_date = update_data.get(
            "start_date",
            allocation.start_date
        )

        new_end_date = update_data.get(
            "end_date",
            allocation.end_date
        )

        if new_end_date < new_start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date must be on or after start_date"
            )

        # Check capacity only for allocations that consume capacity.
        if allocation.status in ["planned", "active"]:
            validate_allocation_capacity(
                db=db,
                employee_id=allocation.employee_id,
                allocation_percentage=new_percentage,
                start_date=new_start_date,
                end_date=new_end_date,
                exclude_allocation_id=allocation_id
            )

        for field, value in update_data.items():
            setattr(allocation, field, value)

        db.commit()
        db.refresh(allocation)

        return allocation

    except Exception:
        db.rollback()
        raise


def update_allocation_status(
    db: Session,
    allocation_id: UUID,
    status_data: EmployeeProjectAllocationStatusUpdate
):
    try:
        allocation = db.get(
            EmployeeProjectAllocation,
            allocation_id
        )

        if not allocation:
            raise HTTPException(
                status_code=404,
                detail="Allocation not found"
            )

        db.scalar(
            select(Employee.employee_id)
            .where(Employee.employee_id == allocation.employee_id)
            .with_for_update()
        )

        new_status = status_data.status

        # Reactivating an allocation must pass the capacity check.
        if new_status in ["planned", "active"]:
            validate_allocation_capacity(
                db=db,
                employee_id=allocation.employee_id,
                allocation_percentage=allocation.allocation_percentage,
                start_date=allocation.start_date,
                end_date=allocation.end_date,
                exclude_allocation_id=allocation_id
            )

        allocation.status = new_status

        db.commit()
        db.refresh(allocation)

        return allocation

    except Exception:
        db.rollback()
        raise
def cancel_allocation(
    db: Session,
    allocation_id: UUID
):
    try:
        allocation = db.scalar(
            select(EmployeeProjectAllocation)
            .where(
                EmployeeProjectAllocation.allocation_id == allocation_id
            )
            .with_for_update()
        )

        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allocation not found"
            )

        if allocation.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed allocations cannot be cancelled"
            )

        if allocation.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocation is already cancelled"
            )

        allocation.status = "cancelled"

        db.commit()
        db.refresh(allocation)

        return allocation

    except Exception:
        db.rollback()
        raise

def complete_allocation(
    db: Session,
    allocation_id: UUID
):
    try:
        allocation = db.scalar(
            select(EmployeeProjectAllocation)
            .where(
                EmployeeProjectAllocation.allocation_id == allocation_id
            )
            .with_for_update()
        )

        if not allocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Allocation not found"
            )

        if allocation.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocation is already completed"
            )

        if allocation.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancelled allocations cannot be completed"
            )

        if allocation.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active allocations can be completed"
            )

        allocation.status = "completed"

        db.commit()
        db.refresh(allocation)

        return allocation

    except Exception:
        db.rollback()
        raise