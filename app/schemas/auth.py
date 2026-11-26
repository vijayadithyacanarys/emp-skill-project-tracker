from pydantic import BaseModel, EmailStr, SecretStr, field_validator

from app.db_compat import (
    is_mssql_database_configured,
    validate_email_whitespace,
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr

    @field_validator("email", mode="before")
    @classmethod
    def reject_mssql_email_whitespace(cls, value: object) -> object:
        if is_mssql_database_configured():
            validate_email_whitespace(value, "mssql")
        return value


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
