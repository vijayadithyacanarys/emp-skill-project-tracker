from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db_compat import exact_string_equal
from app.models.employee import Employee
from app.models.employee_role import EmployeeRole
from app.models.project import Project
from app.models.project_manager import ProjectManager
from app.models.role import Role


def assign_employee_role(
    db: Session,
    employee_id: UUID,
    role_id: int,
) -> Role:
    if db.get(Employee, employee_id) is None:
        raise LookupError("Employee not found")

    role = db.get(Role, role_id)
    if role is None:
        raise LookupError("Role not found")

    assignment_key = (employee_id, role_id)
    if db.get(EmployeeRole, assignment_key) is not None:
        raise ValueError("Role is already assigned to employee")

    try:
        employee = db.get(Employee, employee_id)
        existing_assignments = db.scalars(
            select(EmployeeRole.role_id).where(
                EmployeeRole.employee_id == employee_id
            )
        ).all()

        db.add(EmployeeRole(employee_id=employee_id, role_id=role_id))
        db.flush()
        resulting_role_ids = db.scalars(
            select(EmployeeRole.role_id).where(
                EmployeeRole.employee_id == employee_id
            )
        ).all()
        if employee.role_id not in resulting_role_ids:
            employee.role_id = min(resulting_role_ids)
        elif not existing_assignments:
            employee.role_id = role_id
        db.commit()
        return role
    except IntegrityError as error:
        db.rollback()
        raise ValueError("Role is already assigned to employee") from error


def remove_employee_role(
    db: Session,
    employee_id: UUID,
    role_id: int,
) -> bool:
    if db.get(Employee, employee_id) is None:
        raise LookupError("Employee not found")

    if db.get(Role, role_id) is None:
        raise LookupError("Role not found")

    assignment = db.get(EmployeeRole, (employee_id, role_id))
    if assignment is None:
        return False

    remaining_role_ids = db.scalars(
        select(EmployeeRole.role_id).where(
            EmployeeRole.employee_id == employee_id,
            EmployeeRole.role_id != role_id,
        )
    ).all()
    if not remaining_role_ids:
        raise ValueError(
            "Employee must retain at least one role"
        )

    try:
        db.delete(assignment)
        db.flush()
        employee = db.get(Employee, employee_id)
        if employee.role_id == role_id:
            employee.role_id = min(remaining_role_ids)
        elif employee.role_id not in remaining_role_ids:
            employee.role_id = min(remaining_role_ids)
        db.commit()
        return True
    except IntegrityError as error:
        db.rollback()
        raise RuntimeError(
            "Unable to remove employee role because of conflicting data"
        ) from error


def get_employee_roles(db: Session, employee_id: UUID) -> list[Role]:
    if db.get(Employee, employee_id) is None:
        raise LookupError("Employee not found")

    return db.scalars(
        select(Role)
        .join(EmployeeRole, EmployeeRole.role_id == Role.role_id)
        .where(EmployeeRole.employee_id == employee_id)
        .order_by(Role.role_name)
    ).all()


def assign_project_manager(
    db: Session,
    project_id: UUID,
    manager_id: UUID,
) -> Employee:
    if db.get(Project, project_id) is None:
        raise LookupError("Project not found")

    manager = db.get(Employee, manager_id)
    if manager is None:
        raise LookupError("Employee not found")

    manager_role = db.scalar(
        select(EmployeeRole.employee_id)
        .join(Role, Role.role_id == EmployeeRole.role_id)
        .where(
            EmployeeRole.employee_id == manager_id,
            exact_string_equal(Role.role_name, "Manager"),
        )
        .limit(1)
    )
    if manager_role is None:
        raise ValueError("Employee must have the Manager role")

    assignment_key = (project_id, manager_id)
    if db.get(ProjectManager, assignment_key) is not None:
        raise ValueError("Employee is already assigned as a project manager")

    try:
        db.add(ProjectManager(project_id=project_id, manager_id=manager_id))
        db.commit()
        return manager
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "Employee is already assigned as a project manager"
        ) from error


def remove_project_manager(
    db: Session,
    project_id: UUID,
    manager_id: UUID,
) -> bool:
    if db.get(Project, project_id) is None:
        raise LookupError("Project not found")

    if db.get(Employee, manager_id) is None:
        raise LookupError("Employee not found")

    assignment = db.get(ProjectManager, (project_id, manager_id))
    if assignment is None:
        return False

    db.delete(assignment)
    db.commit()
    return True


def get_project_managers(db: Session, project_id: UUID) -> list[Employee]:
    if db.get(Project, project_id) is None:
        raise LookupError("Project not found")

    return db.scalars(
        select(Employee)
        .join(ProjectManager, ProjectManager.manager_id == Employee.employee_id)
        .where(ProjectManager.project_id == project_id)
        .order_by(Employee.name)
    ).all()
