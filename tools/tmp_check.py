"""Utility script to inspect Excel sheets.

This helper originally printed Markdown output for quick inspection of Excel
content.  The Markdown workflow is now deprecated in favor of exporting the
extracted table to a PDF document so it can be shared more easily.

Running the script will still display the Markdown to the console for
backwards compatibility but also writes a simple PDF alongside the source
Excel file.
"""

import os
import sys
import warnings

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.excel_utils import extract_sheet_text


def export_markdown_to_pdf(markdown: str, pdf_path: str) -> None:
    """Write Markdown text to a basic PDF file.

    The conversion is intentionally simple: each line of the Markdown string is
    drawn to the PDF using a monospaced font.  This avoids heavy dependencies
    and provides a lightweight way to share the extracted table when the
    Markdown workflow is no longer the primary target.
    """

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception as exc:  # pragma: no cover - best effort runtime import
        raise RuntimeError("reportlab is required for PDF export") from exc

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    x_margin, y_margin = 40, 40
    line_height = 14

    y = height - y_margin
    for line in markdown.splitlines():
        if y < y_margin:  # start a new page when reaching bottom
            c.showPage()
            y = height - y_margin
        c.drawString(x_margin, y, line)
        y -= line_height

    c.save()


path = r"ViusalAI_GamesTeam_AudioForHelp/AGR.xls"
sheet = "Paytable"

print("Reading:", path, sheet)
data = extract_sheet_text(path, sheet)
print("Columns:", data["columns"])  # Excel-like letters

warnings.warn(
    "Markdown output is deprecated; a PDF export will be generated instead.",
    DeprecationWarning,
)

# Still print Markdown for debugging/legacy reasons
print("Markdown:\n")
print(data["markdown"])

pdf_path = os.path.splitext(path)[0] + ".pdf"
try:
    export_markdown_to_pdf(data["markdown"], pdf_path)
    print("PDF exported to:", pdf_path)
except Exception as exc:
    print("PDF export skipped:", exc)
