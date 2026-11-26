from openpyxl import load_workbook

def read_excel_batches(file, batch_size=1000):

    workbook = load_workbook(
        file,
        read_only=True,
        data_only=True
    )

    try:
        sheet = workbook.active

        rows = sheet.iter_rows(values_only=True)

        coloumn = ['name','email','role_id','experience_years','status']
        batch = []
        first_row = True

        for excel_row_number, row in enumerate(rows, start=1):
            if first_row:
                first_row = False
                normalized = [
                    str(value).strip().lower()
                    if value is not None
                    else ""
                    for value in row
                ]
                if normalized[:len(coloumn)] == coloumn:
                    continue
            record = dict(zip(coloumn,row))
            record["_row_number"] = excel_row_number
            batch.append(record)

            if len(batch) == batch_size:
                yield batch
                batch=[]

        if batch:
            yield batch
            batch.clear()
    finally:
        workbook.close()

