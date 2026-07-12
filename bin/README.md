# Binary dependencies

`bin/` is intentionally empty in the public repository except for this note.
Local `.exe` files are ignored by Git because their licenses and distribution rights
must be handled separately.

Current runtime tools:

- Calibre `ebook-convert`: required for MOBI and AZW3 conversion.
- Calibre `ebook-meta`: optional, used to read MOBI/AZW3 titles.
- PyMuPDF: used through the Python package `pymupdf` for PDF text extraction and optional fixed-layout PDF overlay.

Install Calibre separately from <https://calibre-ebook.com/> and keep its command
line tools on `PATH`. Run `ebook2pinyin doctor` to check the current machine.

Historical local tools:

- `kindlegen.exe`: Amazon KindleGen is discontinued and proprietary. Do not redistribute it unless you have the right to do so.
- `k2pdfopt.exe`: useful for PDF reshaping workflows, but not used by the current code path. Verify its upstream license before redistribution.

License notes:

- Calibre is GPL licensed and is not bundled here.
- PyMuPDF is AGPL/commercial dual licensed.
