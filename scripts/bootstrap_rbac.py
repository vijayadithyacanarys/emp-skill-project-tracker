import uuid
from getpass import getpass
import sys

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.db_compat import exact_string_equal, validate_email_whitespace
from app.models.employee import Employee
from app.models.employee_credential import EmployeeCredential
from app.models.employee_role import EmployeeRole
from app.models.role import Role
from app.services.auth_service import (
    create_employee_credential,
)
from app.services.permission_seed_service import seed_permission_catalogue
from scripts.seed_roles import seed_roles


def _find_role(db, role_name: str) -> Role:
    role = db.scalar(
        select(Role).where(exact_string_equal(Role.role_name, role_name))
    )
    if role is None:
        raise LookupError(f"{role_name} role was not created")
    return role


def main() -> int:
    admin_email = input("Initial Admin employee email: ").strip()
    if not admin_email:
        print("Admin employee email is required.", file=sys.stderr)
        return 1

    admin_name = None
    promote_existing = False
    credential_created = False

    with SessionLocal() as db:
        dialect_name = db.get_bind().dialect.name
        if dialect_name != "mssql":
            admin_email = admin_email.strip()
        try:
            validate_email_whitespace(admin_email, dialect_name)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1

        employee = db.scalar(
            select(Employee).where(
                exact_string_equal(Employee.email, admin_email)
            )
        )
        existing_credential = (
            db.get(EmployeeCredential, employee.email)
            if employee is not None
            else None
        )

    if employee is None:
        admin_name = input("Initial Admin employee name: ").strip()
        if len(admin_name) < 2:
            print(
                "Initial Admin employee name must be at least 2 characters.",
                file=sys.stderr,
            )
            return 1
    else:
        if employee.status != "active":
            print(
                "Inactive employees cannot be promoted to Admin.",
                file=sys.stderr,
            )
            return 1

        confirmation = input(
            "An existing employee was found. Promote it to Admin? "
            "Type YES to confirm: "
        ).strip()
        if confirmation != "YES":
            print("Admin promotion cancelled.", file=sys.stderr)
            return 1
        promote_existing = True

    if existing_credential is None:
        password = getpass("Initial Admin password: ")
        confirmation_password = getpass("Confirm initial Admin password: ")
        if password != confirmation_password:
            print("Passwords do not match.", file=sys.stderr)
            return 1
        if not password:
            print("Password must not be empty.", file=sys.stderr)
            return 1
    else:
        password = None

    try:
        with SessionLocal.begin() as db:
            created_roles, existing_roles = seed_roles(db)
            created_permissions, created_assignments = (
                seed_permission_catalogue(db)
            )
            admin_role = _find_role(db, "Admin")

            employee = db.scalar(
                select(Employee).where(
                    exact_string_equal(Employee.email, admin_email)
                )
            )
            if employee is None:
                employee = Employee(
                    employee_id=uuid.uuid4(),
                    name=admin_name,
                    email=admin_email,
                    role_id=admin_role.role_id,
                    experience_years=0,
                    status="active",
                )
                db.add(employee)
                db.flush()
                db.add(
                    EmployeeRole(
                        employee_id=employee.employee_id,
                        role_id=admin_role.role_id,
                    )
                )
            else:
                if employee.status != "active":
                    raise ValueError(
                        "Inactive employees cannot be promoted to Admin"
                    )
                if not promote_existing:
                    raise ValueError(
                        "Existing employee promotion was not confirmed"
                    )
                employee.role_id = admin_role.role_id
                assignments = db.scalars(
                    select(EmployeeRole).where(
                        EmployeeRole.employee_id == employee.employee_id
                    )
                ).all()
                if not any(
                    assignment.role_id == admin_role.role_id
                    for assignment in assignments
                ):
                    db.add(
                        EmployeeRole(
                            employee_id=employee.employee_id,
                            role_id=admin_role.role_id,
                        )
                    )

            credential = db.get(
                EmployeeCredential,
                employee.email,
            )
            if credential is None:
                if password is None:
                    raise ValueError(
                        "Initial Admin password is required"
                    )
                create_employee_credential(
                    db,
                    employee.email,
                    password,
                    commit=False,
                )
                credential_created = True
    except (LookupError, ValueError, IntegrityError) as error:
        print(str(error), file=sys.stderr)
        return 1

    print(
        "RBAC bootstrap complete: "
        f"roles created [{', '.join(created_roles) or 'none'}]; "
        f"roles existing [{', '.join(existing_roles) or 'none'}]; "
        f"{created_permissions} permissions and "
        f"{created_assignments} role-permission associations added."
    )
    if credential_created:
        print("Initial Admin credentials created.")
    else:
        print("Existing Admin credentials preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
