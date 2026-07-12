from pathlib import Path
from zipfile import ZipFile

from mobi_pinyin.annotator import AnnotationOptions
from mobi_pinyin.epub import annotate_epub


class FakeBackend:
    values = {"中": "zhong", "国": "guo"}

    def annotate(self, text: str):
        return [(char, self.values.get(char)) for char in text]


def test_annotate_epub_rewrites_html_and_adds_css(tmp_path: Path):
    source = tmp_path / "book.epub"
    output = tmp_path / "book.pinyin.epub"
    with ZipFile(source, "w") as epub:
        epub.writestr("mimetype", "application/epub+zip")
        epub.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
        )
        epub.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest><item id="chapter" href="Text/chapter.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="chapter"/></spine>
</package>""",
        )
        epub.writestr("OEBPS/Text/chapter.xhtml", "<html><head></head><body><p>中国</p></body></html>")

    annotate_epub(source, output, FakeBackend(), AnnotationOptions())

    with ZipFile(output) as epub:
        chapter = epub.read("OEBPS/Text/chapter.xhtml").decode("utf-8")
        opf = epub.read("OEBPS/content.opf").decode("utf-8")
        css = epub.read("OEBPS/mobi-pinyin.css").decode("utf-8")

    assert '<ruby class="pinyin-ruby">中<rt>zhong</rt></ruby>' in chapter
    assert 'href="../mobi-pinyin.css"' in chapter
    assert 'href="mobi-pinyin.css"' in opf
    assert "ruby.pinyin-ruby" in css
