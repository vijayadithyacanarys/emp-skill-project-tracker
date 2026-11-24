from uuid import UUID
import traceback

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    status,
    UploadFile
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse
)
from app.services.employee_service import (
    create_employee,
    get_all_employees,
    get_employee_by_id,
    update_employee,
    delete_employee
)


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)

from app.utils.excel_parser import read_excel_batches
from app.services.employee_service import bulk_insert_employees


@router.post("/upload-employees")
def upload_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    total_inserted = 0

    try:

        for batch in read_excel_batches(file.file):

            bulk_insert_employees(db, batch)

            total_inserted += len(batch)

        return {
            "message": "Employees imported successfully",
            "total_inserted": total_inserted
        }

    except Exception as e:

        db.rollback()

        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", repr(e))

        if hasattr(e, "orig"):
            print("DATABASE ERROR:", repr(e.orig))

        traceback.print_exc()

        raise




# CREATE EMPLOYEE
@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED
)
def create_employee_endpoint(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_employee(db, employee_data)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# GET ALL EMPLOYEES
@router.get(
    "/",
    response_model=list[EmployeeResponse]
)
def get_all_employees_endpoint(
    db: Session = Depends(get_db)
):
    return get_all_employees(db)


# GET EMPLOYEE BY ID
@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def get_employee_by_id_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    employee = get_employee_by_id(db, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee


# UPDATE EMPLOYEE
@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def patch_employee_endpoint(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    try:
        employee = update_employee(
            db,
            employee_id,
            employee_data
        )

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        return employee

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee_endpoint(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    return patch_employee_endpoint(employee_id, employee_data, db)


# DELETE EMPLOYEE
@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_employee_endpoint(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    try:
        deleted = delete_employee(db, employee_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )