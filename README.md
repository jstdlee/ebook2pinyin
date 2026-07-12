# mobi-pinyin

`mobi-pinyin` turns Chinese ebooks and documents into pinyin-annotated reader files.
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

For MOBI/AZW3 conversion, install Calibre and make sure `ebook-convert` and `ebook-meta` are on `PATH`.

## CLI

```powershell
mobi-pinyin convert input.epub
mobi-pinyin convert input.pdf
mobi-pinyin convert input.pdf --output input_pinyin.pdf --rt-size 0.35
mobi-pinyin convert input.mobi
mobi-pinyin convert input.azw3
```

Use `--output` to force a specific output path. For PDF inputs, `.epub` and `.pdf` outputs are both allowed; `.epub` is the recommended default.

## Gradio

```powershell
mobi-pinyin web --host 127.0.0.1 --port 7860
```

The web UI accepts one book at a time and streams conversion stages/progress.

## Binary Dependencies

The current code path does not require bundled executables. Calibre is the main external binary dependency for MOBI/AZW3.

See [bin/README.md](bin/README.md) for notes about local helper binaries and redistribution/licensing cautions.

## Development

```powershell
python -m pytest
```

The repository `.gitignore` excludes local book corpora, generated pinyin outputs, Python caches, local environments, credentials, and local `.exe` helper binaries.

## License

Project code is released under the MIT License. See [LICENSE](LICENSE).

Important dependency notes:

- Calibre is GPL-licensed and is not bundled here.
- PyMuPDF is AGPL/commercial dual licensed.
- Gradio is Apache-2.0 licensed.
- pypinyin and Beautiful Soup are MIT licensed.
