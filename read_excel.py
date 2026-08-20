import openpyxl

wb = openpyxl.load_workbook("review_materials/清洁残留计算所需信息.xlsx")
ws = wb.active
for i, row in enumerate(ws.iter_rows(values_only=True)):
    print(f"Row {i+1}:", row)
