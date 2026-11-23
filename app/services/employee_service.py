import uuid

from sqlalchemy import select, insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee
from app.models.role import Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


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
        experience_years=employee_data.experience_years
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

    # Validate the new role
    role = db.get(Role, employee_data.role_id)

    if role is None:
        raise ValueError("Role does not exist")

    # Check whether another employee uses this email
    existing_employee = db.scalar(
        select(Employee).where(
            Employee.email == employee_data.email,
            Employee.employee_id != employee_id
        )
    )

    if existing_employee:
        raise ValueError("Email already registered")

    employee.name = employee_data.name
    employee.email = employee_data.email
    employee.role_id = employee_data.role_id
    employee.experience_years = employee_data.experience_years

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

    stmt = insert(Employee)

    db.execute(stmt, batch)

    db.commit()