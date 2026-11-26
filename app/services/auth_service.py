import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db_compat import validate_email_whitespace
from app.models.employee import Employee
from app.models.employee_credential import EmployeeCredential
from app.utils.security import hashed_password, verify_password


_DUMMY_PASSWORD_HASH = hashed_password("Not-a-Valid-Employee-p@ssword")


def create_employee_credential(
    db: Session,
    employee_email: str,
    password: str,
    commit: bool = True,
) -> None:
    if not password:
        raise ValueError("Password must not be empty")

    validate_email_whitespace(
        employee_email,
        db.get_bind().dialect.name,
    )

    employee = db.scalar(
        select(Employee).where(Employee.email == employee_email)
    )
    if employee is None:
        raise LookupError("Employee not found")

    stored_email = employee.email
    if db.get(EmployeeCredential, stored_email) is not None:
        raise ValueError("Credentials already exist for this employee")

    credential = EmployeeCredential(
        emp_email=stored_email,
        password_hash=hashed_password(password),
        credential_version=uuid.uuid4(),
    )
    db.add(credential)

    if commit:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            if db.get(EmployeeCredential, stored_email) is not None:
                raise ValueError(
                    "Credentials already exist for this employee"
                ) from None
            raise
    else:
        db.flush()


def authenticate_employee(
    db: Session,
    employee_email: str,
    password: str,
) -> tuple[Employee, uuid.UUID] | None:
    validate_email_whitespace(
        employee_email,
        db.get_bind().dialect.name,
    )

    credential = db.get(EmployeeCredential, employee_email)
    if credential is None:
        verify_password(password, _DUMMY_PASSWORD_HASH)
        return None

    if not verify_password(password, credential.password_hash):
        return None

    employee = credential.employee
    if employee is None or employee.status != "active":
        return None

    return employee, credential.credential_version


def rotate_employee_credential(
    db: Session,
    employee_email: str,
    password: str,
) -> EmployeeCredential:
    if not password:
        raise ValueError("Password must not be empty")

    validate_email_whitespace(
        employee_email,
        db.get_bind().dialect.name,
    )

    credential = db.get(EmployeeCredential, employee_email)
    if credential is None:
        raise LookupError("Employee credentials not found")

    credential.password_hash = hashed_password(password)
    credential.credential_version = uuid.uuid4()

    try:
        db.commit()
        db.refresh(credential)
        return credential
    except IntegrityError:
        db.rollback()
        raise
