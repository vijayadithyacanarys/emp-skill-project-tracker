from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, project_data: ProjectCreate):
    project = Project(**project_data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_all_projects(db: Session):
    statement = select(Project).order_by(Project.project_name)
    return db.scalars(statement).all()


def get_project_by_id(db: Session, project_id: UUID):
    return db.get(Project, project_id)


def update_project(
    db: Session,
    project_id: UUID,
    project_data: ProjectUpdate
):
    project = db.get(Project, project_id)

    if project is None:
        return None

    for field, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: UUID):
    project = db.get(Project, project_id)

    if project is None:
        return False

    try:
        db.delete(project)
        db.commit()
        return True

    except IntegrityError as error:
        db.rollback()
        raise RuntimeError(
            "Cannot delete project because employee allocations exist"
        ) from error
