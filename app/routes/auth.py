from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import AccessTokenResponse, LoginRequest
from app.services.auth_service import authenticate_employee
from app.utils.security import JWTConfigurationError, create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=AccessTokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> AccessTokenResponse:
    authenticated_employee = authenticate_employee(
        db,
        login_data.email,
        login_data.password.get_secret_value(),
    )
    if authenticated_employee is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    employee, credential_version = authenticated_employee
    try:
        access_token = create_access_token(
            employee.employee_id,
            credential_version,
        )
    except JWTConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication is not configured",
        ) from error

    return AccessTokenResponse(access_token=access_token)
