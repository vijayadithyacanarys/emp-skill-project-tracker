
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.employee_project_allocation import EmployeeProjectAllocation
from app.database import get_db
from app.dependencies.authorization import (
    allocation_scope_filter,
    ensure_permission,
    get_project_in_scope,
    require_allocation_access,
    require_employee_access,
    require_permission,
    require_project_access,
)
from app.models.employee import Employee
from app.models.project import Project

from app.schemas.employee_project_allocation import (
    EmployeeProjectAllocationCreate,
    EmployeeProjectAllocationUpdate,
    EmployeeProjectAllocationStatusUpdate,
    EmployeeProjectAllocationResponse,
)

from app.services.employee_project_allocation_service import (
    create_allocation,
    update_allocation,
    update_allocation_status,
    cancel_allocation,
    complete_allocation,
)


router = APIRouter(
    prefix="/allocations",
    tags=["Employee Project Allocations"],
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
    current_employee: Employee = Depends(
        require_permission("allocation:create")
    ),
):
    get_project_in_scope(
        db,
        current_employee,
        allocation.project_id,
    )
    return create_allocation(
        db=db,
        allocation=allocation,
        assigned_by=current_employee.employee_id
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
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("allocation:read")
    ),
):
    return db.scalars(
        select(EmployeeProjectAllocation).where(
            allocation_scope_filter(db, current_employee)
        )
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
    _actor: Employee = Depends(require_permission("allocation:read")),
    authorized_allocation: EmployeeProjectAllocation = Depends(
        require_allocation_access
    ),
):
    return authorized_allocation


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
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("allocation:read")
    ),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    return db.scalars(
        select(EmployeeProjectAllocation)
        .where(
            EmployeeProjectAllocation.employee_id == employee_id,
            allocation_scope_filter(db, current_employee),
        )
    ).all()


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
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("allocation:read")
    ),
    _authorized_project: Project = Depends(require_project_access),
):
    return db.scalars(
        select(EmployeeProjectAllocation)
        .where(
            EmployeeProjectAllocation.project_id == project_id,
            allocation_scope_filter(db, current_employee),
        )
    ).all()


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
    db: Session = Depends(get_db),
    _actor: Employee = Depends(
        require_permission("allocation:update")
    ),
    _authorized_allocation: EmployeeProjectAllocation = Depends(
        require_allocation_access
    ),
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
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("allocation:update")
    ),
    _authorized_allocation: EmployeeProjectAllocation = Depends(
        require_allocation_access
    ),
):
    if status_data.status == "cancelled":
        ensure_permission(
            db,
            current_employee.employee_id,
            "allocation:cancel",
        )
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
    db: Session = Depends(get_db),
    _actor: Employee = Depends(
        require_permission("allocation:cancel")
    ),
    _authorized_allocation: EmployeeProjectAllocation = Depends(
        require_allocation_access
    ),
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
    db: Session = Depends(get_db),
    _actor: Employee = Depends(
        require_permission("allocation:update")
    ),
    _authorized_allocation: EmployeeProjectAllocation = Depends(
        require_allocation_access
    ),
):
    return complete_allocation(
        db=db,
        allocation_id=allocation_id
    )
