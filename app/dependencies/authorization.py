from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy import false, or_, select, true
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.database import get_db
from app.dependencies.auth import get_current_employee
from app.models.employee import Employee
from app.models.employee_project_allocation import EmployeeProjectAllocation
from app.models.employee_role import EmployeeRole
from app.models.permission import Permission
from app.models.project import Project
from app.models.project_manager import ProjectManager
from app.models.role import Role
from app.models.role_permission import RolePermission


def _employee_role_names(db: Session, employee_id: UUID) -> set[str]:
    role_names = db.scalars(
        select(Role.role_name)
        .join(EmployeeRole, EmployeeRole.role_id == Role.role_id)
        .where(EmployeeRole.employee_id == employee_id)
    )
    return set(role_names)


def employee_has_role(
    db: Session,
    employee_id: UUID,
    role_name: str,
) -> bool:
    return role_name in _employee_role_names(db, employee_id)


def has_permission(
    db: Session,
    employee_id: UUID,
    permission_name: str,
) -> bool:
    permission_exists = (
        select(1)
        .select_from(EmployeeRole)
        .join(
            RolePermission,
            RolePermission.role_id == EmployeeRole.role_id,
        )
        .join(
            Permission,
            Permission.permission_id == RolePermission.permission_id,
        )
        .where(
            EmployeeRole.employee_id == employee_id,
            Permission.name == permission_name,
        )
        .exists()
    )
    return bool(db.scalar(select(permission_exists)))


def ensure_permission(
    db: Session,
    employee_id: UUID,
    permission_name: str,
) -> None:
    if not has_permission(db, employee_id, permission_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def require_permission(permission_name: str) -> Callable[..., Employee]:
    def permission_dependency(
        employee: Employee = Depends(get_current_employee),
        db: Session = Depends(get_db),
    ) -> Employee:
        ensure_permission(db, employee.employee_id, permission_name)
        return employee

    return permission_dependency


def require_admin_permission(permission_name: str) -> Callable[..., Employee]:
    def admin_permission_dependency(
        employee: Employee = Depends(require_permission(permission_name)),
        db: Session = Depends(get_db),
    ) -> Employee:
        if not employee_has_role(db, employee.employee_id, "Admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required",
            )
        return employee

    return admin_permission_dependency


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found",
    )


def employee_scope_filter(
    db: Session,
    current_employee: Employee,
) -> ColumnElement[bool]:
    role_names = _employee_role_names(db, current_employee.employee_id)
    if "Admin" in role_names:
        return true()

    scopes = []
    if "Manager" in role_names:
        scopes.append(
            select(1)
            .select_from(EmployeeProjectAllocation)
            .join(
                ProjectManager,
                ProjectManager.project_id
                == EmployeeProjectAllocation.project_id,
            )
            .where(
                EmployeeProjectAllocation.employee_id == Employee.employee_id,
                ProjectManager.manager_id == current_employee.employee_id,
            )
            .exists()
        )

    if "Employee" in role_names:
        scopes.append(Employee.employee_id == current_employee.employee_id)

    return or_(*scopes) if scopes else false()


def project_scope_filter(
    db: Session,
    current_employee: Employee,
) -> ColumnElement[bool]:
    role_names = _employee_role_names(db, current_employee.employee_id)
    if "Admin" in role_names:
        return true()

    scopes = []
    if "Manager" in role_names:
        scopes.append(
            select(1)
            .select_from(ProjectManager)
            .where(
                ProjectManager.project_id == Project.project_id,
                ProjectManager.manager_id == current_employee.employee_id,
            )
            .exists()
        )

    if "Employee" in role_names:
        scopes.append(
            select(1)
            .select_from(EmployeeProjectAllocation)
            .where(
                EmployeeProjectAllocation.project_id == Project.project_id,
                EmployeeProjectAllocation.employee_id
                == current_employee.employee_id,
            )
            .exists()
        )

    return or_(*scopes) if scopes else false()


def allocation_scope_filter(
    db: Session,
    current_employee: Employee,
) -> ColumnElement[bool]:
    role_names = _employee_role_names(db, current_employee.employee_id)
    if "Admin" in role_names:
        return true()

    scopes = []
    if "Manager" in role_names:
        scopes.append(
            select(1).select_from(ProjectManager)
            .where(
                ProjectManager.project_id
                == EmployeeProjectAllocation.project_id,
                ProjectManager.manager_id == current_employee.employee_id,
            )
            .exists()
        )

    if "Employee" in role_names:
        scopes.append(
            EmployeeProjectAllocation.employee_id
            == current_employee.employee_id
        )

    return or_(*scopes) if scopes else false()


def get_employee_in_scope(
    db: Session,
    current_employee: Employee,
    employee_id: UUID,
) -> Employee:
    employee = db.scalar(
        select(Employee)
        .where(Employee.employee_id == employee_id)
        .where(employee_scope_filter(db, current_employee))
    )
    if employee is None:
        raise _not_found()
    return employee


def get_project_in_scope(
    db: Session,
    current_employee: Employee,
    project_id: UUID,
) -> Project:
    project = db.scalar(
        select(Project)
        .where(Project.project_id == project_id)
        .where(project_scope_filter(db, current_employee))
    )
    if project is None:
        raise _not_found()
    return project


def get_allocation_in_scope(
    db: Session,
    current_employee: Employee,
    allocation_id: UUID,
) -> EmployeeProjectAllocation:
    allocation = db.scalar(
        select(EmployeeProjectAllocation)
        .where(EmployeeProjectAllocation.allocation_id == allocation_id)
        .where(allocation_scope_filter(db, current_employee))
    )
    if allocation is None:
        raise _not_found()
    return allocation


def require_employee_access(
    employee_id: UUID = Path(...),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> Employee:
    return get_employee_in_scope(db, current_employee, employee_id)


def require_project_access(
    project_id: UUID = Path(...),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> Project:
    return get_project_in_scope(db, current_employee, project_id)


def require_allocation_access(
    allocation_id: UUID = Path(...),
    current_employee: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> EmployeeProjectAllocation:
    return get_allocation_in_scope(db, current_employee, allocation_id)
