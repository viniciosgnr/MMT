import pandas as pd
file_path = "/home/marcosgnr/MMT/MMT Specifications/All Periodic Analyses.xlsx"
df = pd.read_excel(file_path, sheet_name=0)
combinations = df[['Classification', 'Type', 'Local', 'Intervalo entre coletas', 'Disembark', 'Laboratory', 'Report', 'FC (Flow Computer)', 'Validação', 'Obs.:']].drop_duplicates()
print(combinations.to_string())
