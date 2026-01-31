
import pandas as pd
import openpyxl
import os

excel_path = "MMT Specifications/MMT_Modules_Description.xlsx"
output_path = "MMT Specifications/excel_summary.txt"

if not os.path.exists(excel_path):
    print(f"Error: {excel_path} not found")
    exit(1)

text_output = []

try:
    xl = pd.ExcelFile(excel_path)
    text_output.append(f"File: {excel_path}")
    text_output.append(f"Sheets: {xl.sheet_names}\n")

    for sheet in xl.sheet_names:
        text_output.append(f"=== Sheet: {sheet} ===")
        df = pd.read_excel(excel_path, sheet_name=sheet)
        text_output.append(f"Columns: {list(df.columns)}")
        text_output.append("First 5 rows:")
        text_output.append(df.head(5).to_string())
        text_output.append("\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_output))

    print(f"Excel summary saved to {output_path}")

except Exception as e:
    print(f"Error processing excel: {e}")
