import pandas as pd
import os
import sys

# Force stdout to utf-8 just in case
sys.stdout.reconfigure(encoding='utf-8')

file_path = 'Autoavaliação vôlei de praia (1).xlsx'

def safe_print(text):
    try:
        print(text)
    except Exception:
        # Fallback for tough chars
        try:
            print(text.encode('ascii', 'replace').decode('ascii'))
        except:
             print("<unprintable content>")

if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
else:
    try:
        xl = pd.ExcelFile(file_path)
        print(f"Sheet names: {xl.sheet_names}")
        
        for sheet in xl.sheet_names:
            print(f"\n--- Processing Sheet: {sheet} ---")
            # Read header=None to see row indices clearly
            df = xl.parse(sheet, header=None)
            print("First 15 rows (raw):")
            # Print row by row to easier debug
            for idx, row in df.head(15).iterrows():
                safe_print(f"Row {idx}: {row.tolist()}")
            
    except Exception as e:
        print(f"Error reading Excel file: {e}")
