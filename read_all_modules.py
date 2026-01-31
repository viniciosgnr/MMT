
import pandas as pd
import os

excel_path = "MMT Specifications/MMT_Modules_Description.xlsx"
df = pd.read_excel(excel_path)

# Normalize column names to avoid issues with newlines
df.columns = [c.replace('\n', ' ').strip() for c in df.columns]

output = []
for index, row in df.iterrows():
    module_id = str(row.get('#', 'N/A'))
    module_name = str(row.get('MODULE', 'N/A'))
    problem = str(row.get('THE PROBLEM SOLVED BY THIS MODULE', 'N/A'))
    how_it_works = str(row.get('HOW IT WORKS', 'N/A'))
    inter_connectivity = str(row.get('INTER CONNECTIVITY [integration with other modules?]', 'N/A'))
    feature = str(row.get('FEATURE', 'N/A'))
    
    output.append(f"--- {module_id}: {module_name} ---")
    output.append(f"Problem: {problem}")
    output.append(f"How it works: {how_it_works}")
    output.append(f"Inter-connectivity: {inter_connectivity}")
    output.append(f"Feature: {feature}")
    output.append("-" * 30)

with open("MMT Specifications/full_specs.txt", "w") as f:
    f.write("\n".join(output))

print("Full specs extracted to MMT Specifications/full_specs.txt")
