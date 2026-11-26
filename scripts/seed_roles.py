from sqlalchemy import or_, select

from app.database import SessionLocal
from app.db_compat import exact_string_equal
from app.models.role import Role


ROLE_NAMES = ("Admin", "Manager", "Employee")


def seed_roles(db) -> tuple[list[str], list[str]]:
    existing_names = set(
        db.scalars(
            select(Role.role_name).where(
                or_(
                    *(
                        exact_string_equal(Role.role_name, role_name)
                        for role_name in ROLE_NAMES
                    )
                )
            )
        ).all()
    )

    already_existing = [
        role_name
        for role_name in ROLE_NAMES
        if role_name in existing_names
    ]
    created = [
        role_name
        for role_name in ROLE_NAMES
        if role_name not in existing_names
    ]
    db.add_all(Role(role_name=role_name) for role_name in created)
    db.flush()
    return created, already_existing


def main() -> int:
    with SessionLocal.begin() as db:
        created, already_existing = seed_roles(db)

    created_summary = ", ".join(created) if created else "none"
    existing_summary = (
        ", ".join(already_existing) if already_existing else "none"
    )
    print(
        "Role initialization complete: "
        f"created [{created_summary}]; "
        f"already existed [{existing_summary}]."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
