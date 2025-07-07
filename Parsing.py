import pdfplumber
import re

with pdfplumber.open("Annual Reports/Airbus Annual Report 2024.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"

matches = re.findall(r'Scope 1[^0-9]*([\d,\.]+)', text)
print("Gefundene Scope-1-Werte:", matches)
