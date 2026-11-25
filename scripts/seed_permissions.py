import sys

from app.database import SessionLocal
from app.services.permission_seed_service import seed_permission_catalogue


def main() -> int:
    try:
        with SessionLocal.begin() as db:
            created_permissions, created_assignments = (
                seed_permission_catalogue(db)
            )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(
        "Permission seeding complete: "
        f"{created_permissions} permissions and "
        f"{created_assignments} role-permission associations added."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
