import os, sys
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.excel_utils import extract_sheet_text

path = r"ViusalAI_GamesTeam_AudioForHelp/AGR.xls"
sheet = "Paytable"

print("Reading:", path, sheet)
data = extract_sheet_text(path, sheet)
print("Columns:", data["columns"])  # Excel-like letters
print("Markdown:\n")
print(data["markdown"]) 
