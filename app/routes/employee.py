from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    status,
    UploadFile
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from zipfile import BadZipFile

from app.database import get_db
from app.dependencies.authorization import (
    employee_has_role,
    employee_scope_filter,
    require_admin_permission,
    require_employee_access,
    require_permission,
)
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse
)
from app.schemas.role import EmployeeRoleAssignmentCreate, RoleResponse
from app.services.employee_service import (
    create_employee,
    update_employee,
    delete_employee
)
from app.services.rbac_assignment_service import (
    assign_employee_role,
    get_employee_roles,
    remove_employee_role,
)


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)

from app.utils.excel_parser import read_excel_batches
from app.services.employee_service import bulk_insert_employees


@router.post("/upload-employees")
def upload_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("employee:create")),
):

    total_inserted = 0

    try:
        if db.in_transaction():
            db.rollback()
        with db.begin():
            for batch in read_excel_batches(file.file):
                bulk_insert_employees(db, batch)
                total_inserted += len(batch)

        return {
            "message": "Employees imported successfully",
            "total_inserted": total_inserted
        }

    except (ValueError, LookupError, BadZipFile) as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee import contains conflicting records",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to import employees",
        )




# CREATE EMPLOYEE
@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee_endpoint(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("employee:create")),
):
    try:
        return create_employee(db, employee_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# GET ALL EMPLOYEES
@router.get(
    "/",
    response_model=list[EmployeeResponse]
)
def get_all_employees_endpoint(
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("employee:read")
    ),
):
    return db.scalars(
        select(Employee)
        .where(employee_scope_filter(db, current_employee))
        .order_by(Employee.name)
    ).all()


# GET EMPLOYEE BY ID
@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def get_employee_by_id_endpoint(
    current_employee: Employee = Depends(
        require_permission("employee:read")
    ),
    authorized_employee: Employee = Depends(require_employee_access),
):
    return authorized_employee


# UPDATE EMPLOYEE
@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def patch_employee_endpoint(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("employee:update")
    ),
    authorized_employee: Employee = Depends(require_employee_access),
):
    return _update_employee_endpoint(
        employee_id,
        employee_data,
        db,
        current_employee,
        authorized_employee,
    )


def _update_employee_endpoint(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session,
    current_employee: Employee,
    authorized_employee: Employee,
):
    is_admin = employee_has_role(
        db,
        current_employee.employee_id,
        "Admin",
    )
    if not is_admin:
        if authorized_employee.employee_id != current_employee.employee_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        privileged_fields = {"role_id", "status", "experience_years"}
        if privileged_fields.intersection(
            employee_data.model_dump(exclude_unset=True)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update privileged employee fields",
            )

    try:
        employee = update_employee(
            db,
            employee_id,
            employee_data
        )

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        return employee

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee_endpoint(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(
        require_permission("employee:update")
    ),
    authorized_employee: Employee = Depends(require_employee_access),
):
    return _update_employee_endpoint(
        employee_id,
        employee_data,
        db,
        current_employee,
        authorized_employee,
    )


# DELETE EMPLOYEE
@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_employee_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _current_employee: Employee = Depends(
        require_permission("employee:delete")
    ),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        deleted = delete_employee(db, employee_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.post(
    "/{employee_id}/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_employee_role_endpoint(
    employee_id: UUID,
    assignment: EmployeeRoleAssignmentCreate,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        return assign_employee_role(
            db,
            employee_id,
            assignment.role_id,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.get(
    "/{employee_id}/roles",
    response_model=list[RoleResponse],
)
def get_employee_roles_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db),
    _actor: Employee = Depends(require_permission("role:read")),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        return get_employee_roles(db, employee_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.delete(
    "/{employee_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_employee_role_endpoint(
    employee_id: UUID,
    role_id: int,
    db: Session = Depends(get_db),
    _admin: Employee = Depends(
        require_admin_permission("role:assign")
    ),
    _authorized_employee: Employee = Depends(require_employee_access),
):
    try:
        removed = remove_employee_role(db, employee_id, role_id)
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee role assignment not found",
        )