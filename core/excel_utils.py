"""Utilities for reading Excel sheets and exporting their content."""

import os
from typing import Any, Dict, List

from core.common import debug_print


def _engine_for_excel(path: str) -> str:
    """Pick a pandas engine based on file extension.
    - .xlsx/.xlsm -> openpyxl
    - .xls -> xlrd
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xlsm"]:
        return "openpyxl"
    if ext == ".xls":
        return "xlrd"
    # Fallback to let pandas decide
    return None  # type: ignore


def extract_sheet_text(excel_path: str, sheet_name: str) -> Dict[str, Any]:
    """Read an Excel sheet and extract row/column data plus Markdown table.

    Returns a dict with:
      - sheet_name: str
      - columns: List[str]
      - rows: List[Dict[str, Any]]  (per row values keyed by column name)
      - flat_text: List[str]        (non-empty, de-duplicated cell strings in row order)
      - markdown: str               (GitHub‑flavored Markdown table of the sheet)
    """
    import pandas as pd
    from pandas.api.types import is_numeric_dtype

    def _stringify(value: Any) -> str:
        if value is None:
            return ""
        # pandas uses NaN/NaT for missing; treat as empty
        try:
            import math
            if isinstance(value, float) and math.isnan(value):
                return ""
        except Exception:
            pass
        # Normalize common numeric representations to mimic typical Excel integer display
        try:
            import math
            if isinstance(value, float) and math.isfinite(value):
                if value.is_integer():
                    return str(int(value))
        except Exception:
            pass
        # Convert to string and normalize newlines for Markdown tables
        s = str(value)
        if s is None:
            return ""
        # Replace newlines with <br> to keep table structure
        s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
        # Escape pipe characters which are column separators in Markdown tables
        s = s.replace("|", "\\|")
        return s

    def _dataframe_to_markdown(df_in: "pd.DataFrame") -> str:
        # Ensure string column names
        df_local = df_in.copy()
        df_local.columns = [str(c) for c in df_local.columns]

        # Prepare per-column alignment based on dtype (numeric -> right)
        aligns = [
            ("right" if is_numeric_dtype(df_local[col]) else "left")
            for col in df_local.columns
        ]

        # Compute column widths (consider header and all cells as strings)
        widths: List[int] = []
        for idx, col in enumerate(df_local.columns):
            header_len = len(_stringify(col))
            max_cell_len = header_len
            if not df_local.empty:
                for v in df_local[col].tolist():
                    cell_len = len(_stringify(v))
                    if cell_len > max_cell_len:
                        max_cell_len = cell_len
            # Minimum width of 3 so the separator has at least '---'
            widths.append(max(3, max_cell_len))

        # Build header row
        header_cells = []
        for i, col in enumerate(df_local.columns):
            text = _stringify(col)
            header_cells.append(text.ljust(widths[i]))
        header_row = "| " + " | ".join(header_cells) + " |"

        # Build alignment separator row
        sep_cells = []
        for i, align in enumerate(aligns):
            if align == "right":
                # ---: for right alignment, width dictates dashes
                sep = "-" * (widths[i] - 1) + ":"
            elif align == "center":
                # :---: (not used by default, but keep logic for completeness)
                inner = "-" * max(1, widths[i] - 2)
                sep = ":" + inner + ":"
            else:
                # left: ---
                sep = "-" * widths[i]
            sep_cells.append(sep)
        sep_row = "| " + " | ".join(sep_cells) + " |"

        # Build data rows
        body_rows: List[str] = []
        for _, row in df_local.iterrows():
            cells = []
            for i, col in enumerate(df_local.columns):
                val = row[col]
                s = _stringify(val)
                if aligns[i] == "right":
                    cells.append(s.rjust(widths[i]))
                elif aligns[i] == "center":
                    # center pad (rarely used); approximate by ljust/rjust split
                    total = widths[i]
                    left = (total - len(s)) // 2
                    right = total - len(s) - left
                    cells.append(" " * left + s + " " * right)
                else:
                    cells.append(s.ljust(widths[i]))
            body_rows.append("| " + " | ".join(cells) + " |")

        parts = [header_row, sep_row]
        parts.extend(body_rows)
        return "\n".join(parts)

    engine = _engine_for_excel(excel_path)
    # Read without treating any row as header to preserve the exact grid shape.
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine=engine, header=None)

    # Helper to convert 0-based column index to Excel-like letters (A, B, ..., Z, AA, AB, ...)
    def _col_letter(idx: int) -> str:
        s = ""
        n = idx
        while True:
            n, r = divmod(n, 26)
            s = chr(ord('A') + r) + s
            if n == 0:
                break
            n -= 1
        return s

    # Keep internal numeric index for markdown; export column labels for metadata
    column_labels = [_col_letter(i) for i in range(len(df.columns))]

    rows: List[Dict[str, Any]] = []
    flat: List[str] = []
    seen = set()

    for _, row in df.iterrows():
        row_dict: Dict[str, Any] = {}
        for i, col in enumerate(df.columns):
            val = row[col]
            # Keep native types but also build flat text list from strings/numbers
            row_dict[column_labels[i]] = val if (pd.notna(val)) else None
            if pd.notna(val):
                if isinstance(val, str):
                    text = val.strip()
                else:
                    # Convert numbers and other simple types to string
                    text = str(val).strip()
                if text:
                    if text not in seen:
                        flat.append(text)
                        seen.add(text)
        rows.append(row_dict)

    # Build markdown with empty header cells so we don't introduce fake names like "Unnamed: 0".
    def _dataframe_to_markdown_no_header(df_in: "pd.DataFrame") -> str:
        df_local = df_in.copy()
        # Determine alignments based on dtype
        aligns = [
            ("right" if is_numeric_dtype(df_local[col]) else "left")
            for col in df_local.columns
        ]

        # Compute column widths from cell contents only (ignore header)
        widths: List[int] = []
        for col in df_local.columns:
            max_cell_len = 0
            if not df_local.empty:
                for v in df_local[col].tolist():
                    cell_len = len(_stringify(v))
                    if cell_len > max_cell_len:
                        max_cell_len = cell_len
            widths.append(max(3, max_cell_len))

        # Header row with empty labels to mimic sheets without headers
        header_cells = ["".ljust(w) for w in widths]
        header_row = "| " + " | ".join(header_cells) + " |"

        # Alignment row
        sep_cells = []
        for i, align in enumerate(aligns):
            if align == "right":
                sep = "-" * (max(3, widths[i]) - 1) + ":"
            elif align == "center":
                inner = "-" * max(1, widths[i] - 2)
                sep = ":" + inner + ":"
            else:
                sep = "-" * max(3, widths[i])
            sep_cells.append(sep)
        sep_row = "| " + " | ".join(sep_cells) + " |"

        # Body rows
        body_rows: List[str] = []
        for _, row in df_local.iterrows():
            cells = []
            for i, col in enumerate(df_local.columns):
                s = _stringify(row[col])
                if aligns[i] == "right":
                    cells.append(s.rjust(widths[i]))
                elif aligns[i] == "center":
                    total = widths[i]
                    left = (total - len(s)) // 2
                    right = total - len(s) - left
                    cells.append(" " * left + s + " " * right)
                else:
                    cells.append(s.ljust(widths[i]))
            body_rows.append("| " + " | ".join(cells) + " |")

        return "\n".join([header_row, sep_row] + body_rows)

    markdown = _dataframe_to_markdown_no_header(df)

    return {
        "sheet_name": sheet_name,
        "columns": column_labels,
        "rows": rows,
        "flat_text": flat,
        "markdown": markdown,
    }

def export_sheet_pdf(excel_path: str, sheet_name: str, output_pdf: str) -> str:
    """Render an Excel sheet to PDF.

    This helper reads the specified sheet into a DataFrame, converts it to
    HTML, and then writes that HTML to a PDF file. The output directory is
    created if it does not already exist.

    Returns the path to the generated PDF.
    """
    import pandas as pd
    import os

    # Read the sheet using the appropriate engine
    engine = _engine_for_excel(excel_path)
    df = pd.read_excel(excel_path, sheet_name=sheet_name, engine=engine)

    # Convert DataFrame to HTML
    html = df.to_html(index=False)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_pdf) or ".", exist_ok=True)

    # Attempt to convert HTML to PDF using pdfkit or weasyprint
    try:
        import pdfkit

        pdfkit.from_string(html, output_pdf)
    except Exception:
        from weasyprint import HTML  # type: ignore

        HTML(string=html).write_pdf(output_pdf)

    return output_pdf
