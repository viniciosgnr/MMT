
import pdfplumber
import os

pdf_path = "MMT Specifications/METERING MANAGEMENT TOOL FUNCTIONAL SPECIFICATION.PDF"
output_path = "MMT Specifications/extracted_pdf.txt"

if not os.path.exists(pdf_path):
    print(f"Error: {pdf_path} not found")
    exit(1)

with pdfplumber.open(pdf_path) as pdf:
    with open(output_path, "w", encoding="utf-8") as f:
        for i, page in enumerate(pdf.pages):
            f.write(f"--- Page {i+1} ---\n")
            text = page.extract_text()
            if text:
                f.write(text)
            f.write("\n\n")

print(f"Text extracted to {output_path}")
