from pydantic import BaseModel, ConfigDict, Field


class SkillCreate(BaseModel):
    skill_name: str = Field(
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )


class SkillUpdate(BaseModel):
    skill_name: str = Field(
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=500
    )


class SkillResponse(BaseModel):
    skill_id: int
    skill_name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)