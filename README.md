# Marketing Tool

This project uses `pdfkit` to convert HTML content into PDF files. It relies on the external `wkhtmltopdf` binary.

## Installation

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Install the `wkhtmltopdf` command-line tool:

   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install wkhtmltopdf
     ```
   - **macOS** (Homebrew):
     ```bash
     brew install wkhtmltopdf
     ```

Ensure `wkhtmltopdf` is available on your `PATH` before running the application.
