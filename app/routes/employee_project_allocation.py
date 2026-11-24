
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.employee_project_allocation import EmployeeProjectAllocation
from app.database import get_db
from app.dependencies.auth import get_current_admin

from app.schemas.employee_project_allocation import (
    EmployeeProjectAllocationCreate,
    EmployeeProjectAllocationUpdate,
    EmployeeProjectAllocationStatusUpdate,
    EmployeeProjectAllocationResponse,
)

from app.services.employee_project_allocation_service import (
    create_allocation,
    get_allocation_by_id,
    get_employee_allocations,
    get_project_allocations,
    update_allocation,
    update_allocation_status,
    cancel_allocation,
    complete_allocation,
)


router = APIRouter(
    prefix="/allocations",
    tags=["Employee Project Allocations"],
    dependencies=[Depends(get_current_admin)]
)


# --------------------------------------------------
# 1. Create allocation
# POST /allocations
# --------------------------------------------------

@router.post(
    "",
    response_model=EmployeeProjectAllocationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee_allocation(
    allocation: EmployeeProjectAllocationCreate,
    db: Session = Depends(get_db),
    admin_id: UUID = Depends(get_current_admin)
):
    return create_allocation(
        db=db,
        allocation=allocation,
        admin_id=admin_id
    )


# --------------------------------------------------
# 2. Get all allocations
# GET /allocations
# --------------------------------------------------

@router.get(
    "",
    response_model=list[EmployeeProjectAllocationResponse]
)
def read_all_allocations(
    db: Session = Depends(get_db)
):
    return db.scalars(
        select(EmployeeProjectAllocation)
    ).all()


# --------------------------------------------------
# 3. Get allocation by ID
# GET /allocations/{allocation_id}
# --------------------------------------------------

@router.get(
    "/{allocation_id}",
    response_model=EmployeeProjectAllocationResponse
)
def read_allocation(
    allocation_id: UUID,
    db: Session = Depends(get_db)
):
    return get_allocation_by_id(
        db=db,
        allocation_id=allocation_id
    )


# --------------------------------------------------
# 4. Get employee allocations
# GET /allocations/employees/{employee_id}
# --------------------------------------------------

@router.get(
    "/employees/{employee_id}",
    response_model=list[EmployeeProjectAllocationResponse]
)
def read_employee_allocations(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    return get_employee_allocations(
        db=db,
        employee_id=employee_id
    )


# --------------------------------------------------
# 5. Get project allocations
# GET /allocations/projects/{project_id}
# --------------------------------------------------

@router.get(
    "/projects/{project_id}",
    response_model=list[EmployeeProjectAllocationResponse]
)
def read_project_allocations(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    return get_project_allocations(
        db=db,
        project_id=project_id
    )


# --------------------------------------------------
# 6. Update allocation details
# PATCH /allocations/{allocation_id}
# --------------------------------------------------

@router.patch(
    "/{allocation_id}",
    response_model=EmployeeProjectAllocationResponse
)
def update_employee_allocation(
    allocation_id: UUID,
    allocation_data: EmployeeProjectAllocationUpdate,
    db: Session = Depends(get_db)
):
    return update_allocation(
        db=db,
        allocation_id=allocation_id,
        allocation_data=allocation_data
    )


# --------------------------------------------------
# 7. Update allocation status
# PATCH /allocations/{allocation_id}/status
# --------------------------------------------------

@router.patch(
    "/{allocation_id}/status",
    response_model=EmployeeProjectAllocationResponse
)
def update_employee_allocation_status(
    allocation_id: UUID,
    status_data: EmployeeProjectAllocationStatusUpdate,
    db: Session = Depends(get_db)
):
    return update_allocation_status(
        db=db,
        allocation_id=allocation_id,
        status_data=status_data
    )


# --------------------------------------------------
# 8. Cancel allocation (soft delete)
# DELETE /allocations/{allocation_id}
# --------------------------------------------------

@router.delete(
    "/{allocation_id}",
    response_model=EmployeeProjectAllocationResponse
)
def delete_employee_allocation(
    allocation_id: UUID,
    db: Session = Depends(get_db)
):
    return cancel_allocation(
        db=db,
        allocation_id=allocation_id
    )


# --------------------------------------------------
# 9. Complete allocation
# PATCH /allocations/{allocation_id}/complete
# --------------------------------------------------

@router.patch(
    "/{allocation_id}/complete",
    response_model=EmployeeProjectAllocationResponse
)
def complete_employee_allocation(
    allocation_id: UUID,
    db: Session = Depends(get_db)
):
    return complete_allocation(
        db=db,
        allocation_id=allocation_id
    )
