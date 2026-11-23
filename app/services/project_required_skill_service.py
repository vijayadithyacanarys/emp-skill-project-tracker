from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_required_skill import ProjectRequiredSkill
from app.models.skill import Skill
from app.schemas.project_required_skill import (
    ProjectRequiredSkillCreate,
    ProjectRequiredSkillUpdate
)


def add_required_skill(
    db: Session,
    project_id: UUID,
    requirement_data: ProjectRequiredSkillCreate
):
    if db.get(Project, project_id) is None:
        raise LookupError("Project not found")

    if db.get(Skill, requirement_data.skill_id) is None:
        raise LookupError("Skill not found")

    if db.get(
        ProjectRequiredSkill,
        (project_id, requirement_data.skill_id)
    ) is not None:
        raise ValueError("Skill is already required by this project")

    requirement = ProjectRequiredSkill(
        project_id=project_id,
        skill_id=requirement_data.skill_id,
        minimum_proficiency=requirement_data.minimum_proficiency,
        is_mandatory=requirement_data.is_mandatory
    )

    try:
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        return requirement
    except IntegrityError as error:
        db.rollback()
        raise ValueError(
            "Skill is already required by this project"
        ) from error


def get_project_required_skills(db: Session, project_id: UUID):
    if db.get(Project, project_id) is None:
        raise LookupError("Project not found")

    statement = (
        select(ProjectRequiredSkill)
        .where(ProjectRequiredSkill.project_id == project_id)
        .order_by(ProjectRequiredSkill.skill_id)
    )
    return db.scalars(statement).all()


def update_requirement(
    db: Session,
    project_id: UUID,
    skill_id: int,
    requirement_data: ProjectRequiredSkillUpdate
):
    requirement = db.get(
        ProjectRequiredSkill,
        (project_id, skill_id)
    )

    if requirement is None:
        return None

    for field, value in requirement_data.model_dump(exclude_unset=True).items():
        setattr(requirement, field, value)

    db.commit()
    db.refresh(requirement)
    return requirement


def remove_requirement(db: Session, project_id: UUID, skill_id: int):
    requirement = db.get(
        ProjectRequiredSkill,
        (project_id, skill_id)
    )

    if requirement is None:
        return False

    db.delete(requirement)
    db.commit()
    return True


def get_projects_requiring_skill(db: Session, skill_id: int):
    if db.get(Skill, skill_id) is None:
        raise LookupError("Skill not found")

    statement = (
        select(Project)
        .join(
            ProjectRequiredSkill,
            ProjectRequiredSkill.project_id == Project.project_id
        )
        .where(ProjectRequiredSkill.skill_id == skill_id)
        .order_by(Project.project_name)
    )
    return db.scalars(statement).all()
