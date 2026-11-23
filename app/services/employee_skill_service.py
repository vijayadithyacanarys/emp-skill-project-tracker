from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee
from app.models.skill import Skill
from app.models.employee_skill import EmployeeSkill
from app.schemas.employee_skill import (
    EmployeeSkillCreate,
    EmployeeSkillUpdate
)


# ASSIGN SKILL TO EMPLOYEE
def assign_skill(
    db: Session,
    employee_id: UUID,
    skill_data: EmployeeSkillCreate
):

    # Check employee existence
    employee = db.get(Employee, employee_id)

    if employee is None:
        raise LookupError("Employee not found")

    # Check skill existence
    skill = db.get(Skill, skill_data.skill_id)

    if skill is None:
        raise LookupError("Skill not found")

    # Check duplicate assignment
    existing_assignment = db.get(
        EmployeeSkill,
        (employee_id, skill_data.skill_id)
    )

    if existing_assignment:
        raise ValueError("Skill already assigned to employee")

    new_assignment = EmployeeSkill(
        employee_id=employee_id,
        skill_id=skill_data.skill_id,
        proficiency_level=skill_data.proficiency_level,
        years_of_experience=skill_data.years_of_experience,
        verified=skill_data.verified
    )

    try:
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

        return new_assignment

    except IntegrityError:
        db.rollback()
        raise ValueError("Skill already assigned to employee")


# GET ALL SKILLS OF AN EMPLOYEE
def get_employee_skills(db: Session, employee_id: UUID):

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise LookupError("Employee not found")

    statement = (
        select(EmployeeSkill)
        .where(EmployeeSkill.employee_id == employee_id)
        .order_by(EmployeeSkill.skill_id)
    )

    return db.scalars(statement).all()


# GET PARTICULAR EMPLOYEE SKILL
def get_employee_skill(
    db: Session,
    employee_id: UUID,
    skill_id: int
):

    return db.get(
        EmployeeSkill,
        (employee_id, skill_id)
    )


# UPDATE EMPLOYEE SKILL
def update_employee_skill(
    db: Session,
    employee_id: UUID,
    skill_id: int,
    skill_data: EmployeeSkillUpdate
):

    assignment = db.get(
        EmployeeSkill,
        (employee_id, skill_id)
    )

    if assignment is None:
        return None

    assignment.proficiency_level = skill_data.proficiency_level
    assignment.years_of_experience = skill_data.years_of_experience
    assignment.verified = skill_data.verified

    try:
        db.commit()
        db.refresh(assignment)

        return assignment

    except IntegrityError:
        db.rollback()
        raise ValueError("Unable to update employee skill")

# REMOVE SKILL FROM EMPLOYEE
def remove_employee_skill(
    db: Session,
    employee_id: UUID,
    skill_id: int
):

    assignment = db.get(
        EmployeeSkill,
        (employee_id, skill_id)
    )

    if assignment is None:
        return False

    try:
        db.delete(assignment)
        db.commit()

        return True

    except IntegrityError:
        db.rollback()
        raise RuntimeError(
            "Unable to remove employee skill"
        )