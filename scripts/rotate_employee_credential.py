from getpass import getpass
import sys

from app.database import SessionLocal
from app.services.auth_service import rotate_employee_credential
from app.db_compat import validate_email_whitespace


def main() -> int:
    employee_email = input("Existing employee email: ")
    password = getpass("New password: ")
    confirmation = getpass("Confirm new password: ")

    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1
    if not password:
        print("Password must not be empty.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            if db.get_bind().dialect.name != "mssql":
                employee_email = employee_email.strip()
            validate_email_whitespace(
                employee_email,
                db.get_bind().dialect.name,
            )
            rotate_employee_credential(
                db,
                employee_email,
                password,
            )
        except (LookupError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1

    print(
        "Employee credential rotated; previously issued access tokens "
        "are now invalid."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
