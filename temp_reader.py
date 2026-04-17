from openpyxl import load_workbook
import pandas as pd
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

wb = load_workbook('MMT Specifications/All Periodic Analyses.xlsx', data_only=True)
ws = wb.active
visible_data = []
for row in ws.rows:
    if not ws.row_dimensions[row[0].row].hidden:
        visible_data.append([cell.value for cell in row])

if len(visible_data) > 1:
    df = pd.DataFrame(visible_data[1:], columns=visible_data[0])
    print(df.to_markdown(index=False))
else:
    print("No visible data found")
