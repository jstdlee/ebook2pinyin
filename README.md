# ebook2pinyin

`ebook2pinyin` turns Chinese ebooks and documents into pinyin-annotated reader files.
It is designed for single-book CLI conversion and a lightweight Gradio web UI.

## Supported Inputs

- EPUB: rewrites the package XHTML/HTML with native `<ruby><rt>...</rt></ruby>` pinyin annotations.
- PDF: defaults to text extraction into a reflowable pinyin EPUB. This gives a much better reading experience than squeezing pinyin onto fixed PDF pages. If you explicitly pass a `.pdf` output path, the CLI can still create a fixed-layout annotated PDF overlay.
- AZW3 / MOBI: converts through Calibre, annotates the EPUB intermediate, then converts back. MOBI is first attempted as a KF8-capable hybrid file so ruby can survive on modern Kindle readers.

## Output Naming

When `--output` is omitted, output names use:

```text
<book title or pdf filename>_pinyin.<ext>
```

EPUB titles come from OPF metadata. MOBI/AZW3 titles use Calibre `ebook-meta` when available. PDF uses the original PDF filename.

Examples:

```text
货币战争4.pdf -> 货币战争4_pinyin.epub
download.epub with title "真正书名" -> 真正书名_pinyin.epub
book.mobi with title "鲁滨逊漂流记" -> 鲁滨逊漂流记_pinyin.mobi
```

## Install

```powershell
python -m pip install -e ".[all]"
```

## Dependencies

This is not a pure-Python converter for every ebook format.

Python package dependencies:

- `pypinyin`: Chinese character to pinyin conversion.
- `beautifulsoup4`: HTML/XHTML parsing and rewriting for EPUB.
- `pymupdf`: PDF text extraction and optional fixed-layout PDF output.
- `typer`: CLI.
- `gradio`: optional web UI, installed by `.[web]` or `.[all]`.

External binary dependencies:

- Calibre `ebook-convert`: required for MOBI and AZW3 conversion.
- Calibre `ebook-meta`: optional, used to read MOBI/AZW3 titles for better output names.

EPUB and PDF paths are implemented with Python libraries. MOBI/AZW3 are not; they convert through Calibre:

```text
MOBI/AZW3 -> ebook-convert -> EPUB -> add pinyin ruby -> ebook-convert -> MOBI/AZW3
```

Install Calibre separately from <https://calibre-ebook.com/> and make sure `ebook-convert` and `ebook-meta` are on `PATH`.

Check the current machine:

```powershell
ebook2pinyin doctor
```

If a required item is missing, `doctor` prints the install/configuration step to fix it.

## CLI

```powershell
ebook2pinyin convert input.epub
ebook2pinyin convert input.pdf
ebook2pinyin convert input.pdf --output input_pinyin.pdf --rt-size 0.35
ebook2pinyin convert input.mobi
ebook2pinyin convert input.azw3
```

Use `--output` to force a specific output path. For PDF inputs, `.epub` and `.pdf` outputs are both allowed; `.epub` is the recommended default.

## Gradio

```powershell
ebook2pinyin web --host 127.0.0.1 --port 7860
```

The web UI accepts one book at a time and streams conversion stages/progress.

## Binary Dependencies

The repository does not bundle required executables. Calibre is the external binary dependency for MOBI/AZW3.

See [bin/README.md](bin/README.md) for notes about local helper binaries and redistribution/licensing cautions.

## Development

```powershell
python -m pytest
```

The repository `.gitignore` excludes local book corpora, generated pinyin outputs, Python caches, local environments, credentials, and local `.exe` helper binaries.

## Release

See [docs/RELEASE.md](docs/RELEASE.md) for the full release checklist, including dependency verification, build artifacts, GitHub release notes, and optional PyPI publishing.

## License

Project code is released under the MIT License. See [LICENSE](LICENSE).

Important dependency notes:

- Calibre is GPL-licensed and is not bundled here.
- PyMuPDF is AGPL/commercial dual licensed.
- Gradio is Apache-2.0 licensed.
- pypinyin and Beautiful Soup are MIT licensed.
