from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.skill import Skill
from app.schemas.skill import SkillCreate, SkillUpdate


# CREATE SKILL
def create_skill(db: Session, skill_data: SkillCreate):

    existing_skill = db.scalar(
        select(Skill).where(
            Skill.skill_name == skill_data.skill_name
        )
    )

    if existing_skill:
        raise ValueError("Skill already exists")

    new_skill = Skill(
        skill_name=skill_data.skill_name,
        description=skill_data.description
    )

    try:
        db.add(new_skill)
        db.commit()
        db.refresh(new_skill)

        return new_skill

    except IntegrityError:
        db.rollback()
        raise ValueError("Skill already exists")


# GET ALL SKILLS
def get_all_skills(db: Session):

    statement = select(Skill).order_by(Skill.skill_id)

    return db.scalars(statement).all()


# GET SKILL BY ID
def get_skill_by_id(db: Session, skill_id: int):

    return db.get(Skill, skill_id)


# UPDATE SKILL
def update_skill(
    db: Session,
    skill_id: int,
    skill_data: SkillUpdate
):

    skill = db.get(Skill, skill_id)

    if skill is None:
        return None

    existing_skill = db.scalar(
        select(Skill).where(
            Skill.skill_name == skill_data.skill_name,
            Skill.skill_id != skill_id
        )
    )

    if existing_skill:
        raise ValueError("Skill name already exists")

    skill.skill_name = skill_data.skill_name
    skill.description = skill_data.description

    try:
        db.commit()
        db.refresh(skill)

        return skill

    except IntegrityError:
        db.rollback()
        raise ValueError("Skill name already exists")


# DELETE SKILL
def delete_skill(db: Session, skill_id: int):

    skill = db.get(Skill, skill_id)

    if skill is None:
        return False

    try:
        db.delete(skill)
        db.commit()

        return True

    except IntegrityError:
        db.rollback()
        raise RuntimeError(
            "Cannot delete skill because it is associated with employees"
        )