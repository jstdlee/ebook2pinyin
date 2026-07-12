from pathlib import Path
from zipfile import ZipFile

import pytest

from ebook2pinyin.annotator import AnnotationOptions
from ebook2pinyin.pdf import pdf_to_epub


class FakeBackend:
    values = {"中": "zhong", "国": "guo"}

    def annotate(self, text: str):
        return [(char, self.values.get(char)) for char in text]


def test_pdf_to_epub_extracts_text_and_adds_ruby(tmp_path: Path):
    fitz = pytest.importorskip("fitz")
    source = tmp_path / "book.pdf"
    output = tmp_path / "book.pinyin.epub"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "\u4e2d\u56fd", fontname="china-s", fontsize=12)
    doc.save(source)
    doc.close()

    pdf_to_epub(source, output, FakeBackend(), AnnotationOptions())

    with ZipFile(output) as epub:
        text = "".join(
            epub.read(name).decode("utf-8")
            for name in epub.namelist()
            if name.endswith((".html", ".xhtml"))
        )

    assert '<ruby class="pinyin-ruby">中<rt>zhong</rt></ruby>' in text
    assert '<ruby class="pinyin-ruby">国<rt>guo</rt></ruby>' in text
