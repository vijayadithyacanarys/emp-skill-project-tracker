import uuid

from sqlalchemy import insert, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db_compat import validate_email_whitespace
from app.models.employee import Employee
from app.models.role import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.models.employee_skill import EmployeeSkill
from app.models.employee_project_allocation import EmployeeProjectAllocation
from app.models.employee_role import EmployeeRole


# CREATE EMPLOYEE
def create_employee(db: Session, employee_data: EmployeeCreate):
    validate_email_whitespace(
        employee_data.email,
        db.get_bind().dialect.name,
    )

    # Check whether the role exists
    role = db.get(Role, employee_data.role_id)

    if role is None:
        raise ValueError("Role does not exist")

    # Check whether email already exists
    existing_employee = db.scalar(
        select(Employee).where(
            Employee.email == employee_data.email
        )
    )

    if existing_employee:
        raise ValueError("Email already registered")

    new_employee = Employee(
        employee_id=uuid.uuid4(),
        name=employee_data.name,
        email=employee_data.email,
        role_id=employee_data.role_id,
        experience_years=employee_data.experience_years,
        status=employee_data.status
    )

    try:
        db.add(new_employee)
        db.flush()
        db.add(
            EmployeeRole(
                employee_id=new_employee.employee_id,
                role_id=role.role_id,
            )
        )
        db.commit()
        db.refresh(new_employee)

        return new_employee

    except IntegrityError as error:
        db.rollback()
        constraint = str(getattr(error.orig, "diag", "")).lower()
        message = str(error.orig).lower()
        if "email" in constraint or "email" in message:
            raise ValueError("Employee email already exists") from error
        if "employee_roles" in constraint or "employee_roles" in message:
            raise ValueError(
                "Unable to synchronize employee role assignment"
            ) from error
        raise ValueError(
            "Unable to create employee due to conflicting data"
        ) from error


# GET ALL EMPLOYEES
def get_all_employees(db: Session):

    statement = select(Employee).order_by(Employee.name)

    return db.scalars(statement).all()


# GET EMPLOYEE BY ID
def get_employee_by_id(db: Session, employee_id: uuid.UUID):

    return db.get(Employee, employee_id)


# UPDATE EMPLOYEE
def update_employee(
    db: Session,
    employee_id: uuid.UUID,
    employee_data: EmployeeUpdate
):

    employee = db.get(Employee, employee_id)

    if employee is None:
        return None

    updates = employee_data.model_dump(exclude_unset=True)

    if "email" in updates:
        validate_email_whitespace(
            updates["email"],
            db.get_bind().dialect.name,
        )

    if "role_id" in updates:
        role = db.get(Role, updates["role_id"])
        if role is None:
            raise ValueError("Role does not exist")

    if "email" in updates:
        existing_employee = db.scalar(
            select(Employee).where(
                Employee.email == updates["email"],
                Employee.employee_id != employee_id
            )
        )
        if existing_employee:
            raise ValueError("Email already registered")

    for field, value in updates.items():
        if field != "role_id":
            setattr(employee, field, value)

    if "role_id" in updates:
        assignment = db.get(
            EmployeeRole,
            (employee_id, updates["role_id"]),
        )
        if assignment is None:
            db.add(
                EmployeeRole(
                    employee_id=employee_id,
                    role_id=updates["role_id"],
                )
            )
            db.flush()

        role_ids = db.scalars(
            select(EmployeeRole.role_id).where(
                EmployeeRole.employee_id == employee_id
            )
        ).all()
        if updates["role_id"] not in role_ids:
            raise ValueError(
                "Selected role could not be assigned to employee"
            )
        employee.role_id = updates["role_id"]

    try:
        db.commit()
        db.refresh(employee)

        return employee

    except IntegrityError as error:
        db.rollback()
        constraint = str(getattr(error.orig, "diag", "")).lower()
        message = str(error.orig).lower()
        if "email" in constraint or "email" in message:
            raise ValueError("Email already registered") from error
        if "employee_roles" in constraint or "employee_roles" in message:
            raise ValueError(
                "Unable to synchronize employee role assignment"
            ) from error
        raise ValueError(
            "Unable to update employee due to conflicting data"
        ) from error


# DELETE EMPLOYEE
def delete_employee(db: Session, employee_id: uuid.UUID):

    employee = db.get(Employee, employee_id)

    if employee is None:
        return False

    has_skills = db.scalar(
        select(EmployeeSkill.employee_id)
        .where(EmployeeSkill.employee_id == employee_id)
        .limit(1)
    ) is not None
    has_allocations = db.scalar(
        select(EmployeeProjectAllocation.allocation_id)
        .where(
            (EmployeeProjectAllocation.employee_id == employee_id)
            | (EmployeeProjectAllocation.assigned_by == employee_id)
        )
        .limit(1)
    ) is not None

    if has_skills or has_allocations:
        employee.status = "inactive"
        db.commit()
        db.refresh(employee)
        return True

    try:
        db.delete(employee)
        db.commit()

        return True

    except IntegrityError:
        db.rollback()
        raise RuntimeError(
            "Cannot delete employee because related records exist"
        )

def bulk_insert_employees(db: Session, batch):
    dialect_name = db.get_bind().dialect.name
    records = []
    employee_roles = []
    batch_emails = set()

    for record in batch:
        record = dict(record)
        row_number = record.pop("_row_number", None)
        row_label = (
            f"Row {row_number}" if row_number is not None else "Excel row"
        )

        name = record.get("name")
        if not isinstance(name, str) or len(name.strip()) < 2:
            raise ValueError(f"{row_label}: name is required and must be at least 2 characters")

        email = record.get("email")
        if not isinstance(email, str) or not email.strip():
            raise ValueError(f"{row_label}: email is required")
        if dialect_name != "mssql":
            email = email.strip()
        try:
            validate_email_whitespace(email, dialect_name)
        except ValueError as error:
            raise ValueError(f"{row_label}: {error}") from error

        normalized_email = email.lower()
        if normalized_email in batch_emails:
            raise ValueError(
                f"{row_label}: duplicate email '{email}' in upload"
            )
        batch_emails.add(normalized_email)

        existing_employee = db.scalar(
            select(Employee.employee_id).where(Employee.email == email)
        )
        if existing_employee is not None:
            raise ValueError(
                f"{row_label}: email '{email}' is already registered"
            )

        record_status = record.get("status", "active")
        if record_status not in ("active", "inactive"):
            raise ValueError(
                f"{row_label}: invalid employee status '{record_status}'. "
                "Expected 'active' or 'inactive'"
            )
        try:
            role_id = int(record.get("role_id"))
        except (TypeError, ValueError):
            raise ValueError(
                f"{row_label}: role_id must be an integer"
            ) from None

        role = db.get(Role, role_id)
        if role is None:
            raise ValueError(
                f"{row_label}: role_id {role_id} does not exist"
            )

        try:
            experience_years = float(record.get("experience_years", 0))
        except (TypeError, ValueError):
            raise ValueError(
                f"{row_label}: experience_years must be numeric"
            ) from None
        if experience_years < 0:
            raise ValueError(
                f"{row_label}: experience_years must be non-negative"
            )

        employee_id = uuid.uuid4()
        record["name"] = name.strip()
        record["email"] = email
        record["status"] = record_status
        record["role_id"] = role_id
        record["experience_years"] = experience_years
        record["employee_id"] = employee_id
        records.append(record)
        employee_roles.append(
            {
                "employee_id": employee_id,
                "role_id": role_id,
            }
        )

    if records:
        db.execute(insert(Employee), records)
        db.execute(insert(EmployeeRole), employee_roles)