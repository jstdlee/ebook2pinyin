from __future__ import annotations

from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from .annotator import (
    AnnotationOptions,
    PinyinBackend,
    PinyinDependencyError,
    annotate_html,
    is_chinese,
    ruby_css,
)
from .progress import ProgressCallback, Stage, noop_progress


def pdf_to_epub(
    input_path: Path,
    output_path: Path,
    backend: PinyinBackend,
    options: AnnotationOptions,
    progress: ProgressCallback = noop_progress,
) -> Path:
    try:
        import fitz
    except ImportError as exc:
        raise PinyinDependencyError(
            "PDF to EPUB conversion requires PyMuPDF. Install it with: python -m pip install pymupdf"
        ) from exc

    doc = fitz.open(input_path)
    total = max(doc.page_count, 1)
    pages: list[tuple[str, bytes]] = []
    for page_index in range(doc.page_count):
        page = doc[page_index]
        progress(Stage("extract", page_index + 1, total, f"Extracting page {page_index + 1}"))
        html = _page_to_xhtml(input_path.stem, page_index + 1, _extract_page_paragraphs(page))
        annotated = annotate_html(html, backend, options, inject_css=False).encode("utf-8")
        pages.append((f"Text/page{page_index + 1:04d}.xhtml", annotated))
    doc.close()

    progress(Stage("package", 0, 1, "Writing EPUB"))
    _write_epub_from_pages(output_path, input_path.stem, pages, options)
    progress(Stage("done", 1, 1, f"Wrote {output_path.name}"))
    return output_path


def annotate_pdf(
    input_path: Path,
    output_path: Path,
    backend: PinyinBackend,
    options: AnnotationOptions,
    progress: ProgressCallback = noop_progress,
) -> Path:
    try:
        import fitz
    except ImportError as exc:
        raise PinyinDependencyError(
            "PDF annotation requires PyMuPDF. Install it with: python -m pip install pymupdf"
        ) from exc

    doc = fitz.open(input_path)
    total = max(doc.page_count, 1)
    for page_index in range(doc.page_count):
        page = doc[page_index]
        progress(Stage("annotate", page_index + 1, total, f"Annotating page {page_index + 1}"))
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    _annotate_span(page, span, backend, options)

    progress(Stage("package", 0, 1, "Writing PDF"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    progress(Stage("done", 1, 1, f"Wrote {output_path.name}"))
    return output_path


def _extract_page_paragraphs(page) -> list[str]:
    blocks = page.get_text("blocks")
    text_blocks = [block for block in blocks if len(block) >= 7 and block[6] == 0 and block[4].strip()]
    text_blocks.sort(key=lambda block: (round(block[1], 1), round(block[0], 1)))
    return [_merge_pdf_lines(block[4].splitlines()) for block in text_blocks]


def _merge_pdf_lines(lines: list[str]) -> str:
    merged = ""
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if not merged:
            merged = line
        elif _needs_space(merged[-1], line[0]):
            merged += " " + line
        else:
            merged += line
    return merged


def _needs_space(left: str, right: str) -> bool:
    return left.isascii() and right.isascii() and left.isalnum() and right.isalnum()


def _page_to_xhtml(title: str, page_number: int, paragraphs: list[str]) -> str:
    body = "\n".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs if paragraph)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{escape(title)} - {page_number}</title>
  <link rel="stylesheet" type="text/css" href="../ebook2pinyin.css" />
</head>
<body>
  <section class="pdf-page" id="page-{page_number}">
    <h2>Page {page_number}</h2>
    {body}
  </section>
</body>
</html>
"""


def _write_epub_from_pages(
    output_path: Path,
    title: str,
    pages: list[tuple[str, bytes]],
    options: AnnotationOptions,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w") as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        epub.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
""",
            compress_type=ZIP_DEFLATED,
        )
        for filename, data in pages:
            epub.writestr(f"OEBPS/{filename}", data, compress_type=ZIP_DEFLATED)
        epub.writestr(
            "OEBPS/ebook2pinyin.css",
            _epub_css(options).encode("utf-8"),
            compress_type=ZIP_DEFLATED,
        )
        epub.writestr(
            "OEBPS/nav.xhtml",
            _nav_xhtml(title, pages).encode("utf-8"),
            compress_type=ZIP_DEFLATED,
        )
        epub.writestr(
            "OEBPS/content.opf",
            _opf(title, pages).encode("utf-8"),
            compress_type=ZIP_DEFLATED,
        )


def _epub_css(options: AnnotationOptions) -> str:
    return f"""
body {{
  font-family: serif;
  line-height: 1.65;
  margin: 5%;
}}

.pdf-page {{
  page-break-after: always;
}}

.pdf-page h2 {{
  color: #666;
  font-size: 0.85em;
  font-weight: normal;
  margin: 0 0 1em;
}}

p {{
  margin: 0 0 0.85em;
  text-indent: 2em;
}}

{ruby_css(options)}
""".strip()


def _nav_xhtml(title: str, pages: list[tuple[str, bytes]]) -> str:
    links = "\n".join(
        f'      <li><a href="{escape(filename)}">Page {index}</a></li>'
        for index, (filename, _data) in enumerate(pages, start=1)
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>{escape(title)} Navigation</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{escape(title)}</h1>
    <ol>
{links}
    </ol>
  </nav>
</body>
</html>
"""


def _opf(title: str, pages: list[tuple[str, bytes]]) -> str:
    manifest_items = "\n".join(
        f'    <item id="page{index:04d}" href="{escape(filename)}" media-type="application/xhtml+xml" />'
        for index, (filename, _data) in enumerate(pages, start=1)
    )
    spine_items = "\n".join(
        f'    <itemref idref="page{index:04d}" />'
        for index in range(1, len(pages) + 1)
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">ebook2pinyin-{escape(title)}</dc:identifier>
    <dc:title>{escape(title)}</dc:title>
    <dc:language>zh</dc:language>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="css" href="ebook2pinyin.css" media-type="text/css" />
{manifest_items}
  </manifest>
  <spine>
{spine_items}
  </spine>
</package>
"""


def _annotate_span(page, span: dict, backend: PinyinBackend, options: AnnotationOptions) -> None:
    text = span.get("text", "")
    if not any(is_chinese(char) for char in text):
        return

    bbox = span.get("bbox")
    if not bbox:
        return
    x0, y0, x1, _y1 = bbox
    width = max(x1 - x0, 1)
    char_width = width / max(len(text), 1)
    font_size = max(float(span.get("size", 10.0)) * options.rt_size, 3.0)
    y = max(y0 - font_size * 0.25, 0)

    for index, (char, pinyin) in enumerate(backend.annotate(text)):
        if not pinyin or not is_chinese(char):
            continue
        x = x0 + index * char_width
        page.insert_text(
            (x, y),
            pinyin,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            overlay=True,
        )
