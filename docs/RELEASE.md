# Release guide

This project ships Python code. It does not bundle Calibre, KindleGen, k2pdfopt,
book samples, credentials, or generated pinyin ebooks.

## Runtime dependency model

Required Python packages:

- `pypinyin`: Chinese character to pinyin conversion.
- `beautifulsoup4`: EPUB/HTML parsing and rewriting.
- `pymupdf`: PDF text extraction and optional annotated PDF output.
- `typer`: CLI.

Optional Python packages:

- `gradio`: single-book web UI.
- `pytest`: development tests.

External tools:

- Calibre `ebook-convert`: required for MOBI/AZW3 conversion.
- Calibre `ebook-meta`: optional but recommended for MOBI/AZW3 metadata title extraction.

Format support by dependency:

| Format | Required dependencies | Notes |
| --- | --- | --- |
| EPUB | Python packages only | Rewrites XHTML/HTML and injects ruby CSS. |
| PDF -> EPUB | Python packages only | Extracts text with PyMuPDF and repacks as reflowable EPUB. |
| PDF -> PDF | Python packages only | Adds fixed-layout overlay with PyMuPDF. |
| MOBI/AZW3 | Calibre + Python packages | Converts through EPUB, annotates, then converts back. |

## User installation

Core CLI:

```powershell
python -m pip install ebook2pinyin
```

CLI plus web UI:

```powershell
python -m pip install "ebook2pinyin[web]"
```

Local editable development install:

```powershell
python -m pip install -e ".[all]"
```

Install Calibre separately from <https://calibre-ebook.com/>. On Windows, make
sure the Calibre install directory is visible on `PATH`, for example:

```powershell
$env:Path -split ';' | Select-String -Pattern 'Calibre'
ebook-convert --version
ebook-meta --version
```

After changing `PATH`, open a new terminal.

## Dependency verification

Run:

```powershell
ebook2pinyin doctor
```

Expected for full functionality:

```text
OK      pypinyin         required Chinese -> pinyin annotation
OK      beautifulsoup4   required EPUB/HTML rewriting
OK      pymupdf          required PDF input/output
OK      gradio           optional web UI
OK      ebook-convert    required MOBI/AZW3 conversion
OK      ebook-meta       optional MOBI/AZW3 title detection
```

If `ebook-convert` is missing, EPUB/PDF conversion can still work, but MOBI/AZW3
conversion will fail.

## Pre-release checklist

1. Verify the tree is clean:

   ```powershell
   git status --short
   ```

2. Verify no credentials or private books are tracked:

   ```powershell
   git ls-files | Select-String -Pattern 'credential|secret|token|books/'
   ```

3. Run tests:

   ```powershell
   python -m pytest
   ```

4. Run dependency check:

   ```powershell
   ebook2pinyin doctor
   ```

5. Smoke test representative inputs:

   ```powershell
   ebook2pinyin convert books/sample.epub --overwrite
   ebook2pinyin convert books/sample.pdf --overwrite
   ebook2pinyin convert books/sample.mobi --overwrite
   ebook2pinyin web --host 127.0.0.1 --port 7860
   ```

6. Confirm generated files are ignored:

   ```powershell
   git status --short
   ```

## Build artifacts

Build source and wheel distributions:

```powershell
python -m pip install build twine
python -m build
python -m twine check dist/*
```

The `dist/` directory is ignored by Git and should be uploaded to the package
registry or release page, not committed.

## GitHub release

1. Update version in `pyproject.toml`.
2. Commit the version bump.
3. Create and push a tag:

   ```powershell
   git tag v0.1.0
   git push github main --tags
   ```

4. Create a GitHub release with:

   - Supported formats: EPUB, PDF, MOBI, AZW3.
   - Required external dependency for MOBI/AZW3: Calibre.
   - License notes: project MIT, Calibre GPL, PyMuPDF AGPL/commercial.
   - A reminder to run `ebook2pinyin doctor`.

## Optional PyPI publishing

Use an API token stored outside the repository.

```powershell
python -m twine upload dist/*
```

Never commit `.pypirc`, API tokens, OAuth credentials, sample books, or generated
ebook outputs.
