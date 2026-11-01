import pandas as pd
import sys

file_path = '/app/temp_imports/1777190043.354289_Клиенты доставки 26.04.2026 10.35.20.xlsx'
try:
    df = pd.read_excel(file_path)
    print("COLUMNS_START")
    print(list(df.columns))
    print("COLUMNS_END")
except Exception as e:
    print(f"ERROR: {e}")
