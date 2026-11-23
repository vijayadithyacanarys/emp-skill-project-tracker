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

        for row in rows:
            record = dict(zip(coloumn,row))
            batch.append(record)

            if len(batch) == batch_size:
                yield batch
                batch=[]

        if batch:
            yield batch
            batch.clear()
    finally:
        workbook.close()

