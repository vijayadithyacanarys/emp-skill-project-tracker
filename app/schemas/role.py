from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    role_name: str = Field(min_length=2, max_length=50)


class RoleUpdate(BaseModel):
    role_name: str = Field(min_length=2, max_length=50)


class RoleResponse(BaseModel):
    role_id: int
    role_name: str

    model_config = ConfigDict(from_attributes=True)