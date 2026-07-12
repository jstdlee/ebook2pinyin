# Binary dependencies

The project does not require bundled executables for normal operation.

Recommended external tools:

- Calibre `ebook-convert` / `ebook-meta`: required for MOBI and AZW3 conversion. Calibre is GPL-licensed; install it separately from <https://calibre-ebook.com/>.
- PyMuPDF: used through the Python package `pymupdf` for PDF text extraction and optional fixed-layout PDF overlay. PyMuPDF is AGPL/commercial dual licensed.

Historical local tools:

- `kindlegen.exe`: Amazon KindleGen is discontinued and proprietary. Do not redistribute it unless you have the right to do so.
- `k2pdfopt.exe`: useful for PDF reshaping workflows, but not used by the current code path. Verify its upstream license before redistribution.

Local `.exe` files in this directory are ignored by Git. Keep them only as machine-local helpers.
