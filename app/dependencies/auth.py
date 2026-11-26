from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.employee_credential import EmployeeCredential
from app.utils.security import verify_access_token
from app.utils.security import JWTConfigurationError


bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_employee(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Employee:
    if credentials is None:
        raise _unauthorized()

    try:
        claims = verify_access_token(credentials.credentials)
        employee_id = UUID(claims["sub"])
        credential_version = UUID(claims["credential_version"])
    except (
        PyJWTError,
        JWTConfigurationError,
        KeyError,
        TypeError,
        ValueError,
    ):
        raise _unauthorized() from None

    employee = db.get(Employee, employee_id)
    if employee is None or employee.status != "active":
        raise _unauthorized()

    current_credential_version = db.scalar(
        select(EmployeeCredential.credential_version).where(
            EmployeeCredential.emp_email == employee.email
        )
    )
    if current_credential_version != credential_version:
        raise _unauthorized()

    return employee