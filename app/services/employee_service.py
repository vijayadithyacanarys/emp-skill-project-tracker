import uuid

from sqlalchemy import select, insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee
from app.models.role import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.models.employee_skill import EmployeeSkill
from app.models.employee_project_allocation import EmployeeProjectAllocation


# CREATE EMPLOYEE
def create_employee(db: Session, employee_data: EmployeeCreate):

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
        db.commit()
        db.refresh(new_employee)

        return new_employee

    except IntegrityError:
        db.rollback()
        raise ValueError("Employee email already exists")


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
        setattr(employee, field, value)

    try:
        db.commit()
        db.refresh(employee)

        return employee

    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")


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

def bulk_insert_employees(db : Session, batch):
    records = []
    for record in batch:
        record = dict(record)
        record_status = record.get("status", "active")
        if record_status not in ("active", "inactive"):
            raise ValueError(
                f"Invalid employee status: {record_status}. "
                "Expected 'active' or 'inactive'"
            )
        record["status"] = record_status
        records.append(record)

    stmt = insert(Employee)
    db.execute(stmt, records)

    db.commit()