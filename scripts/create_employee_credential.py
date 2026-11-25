from getpass import getpass
import sys

from app.database import SessionLocal
from app.services.auth_service import create_employee_credential


def main() -> int:
    employee_email = input("Existing employee email: ").strip()
    password = getpass("Password: ")
    confirmation = getpass("Confirm password: ")

    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1
    if not password:
        print("Password must not be empty.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            create_employee_credential(db, employee_email, password)
        except (LookupError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1

    print("Employee credentials created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
