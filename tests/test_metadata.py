from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from ebook2pinyin.metadata import default_output_path_for_book, epub_title, safe_filename


def test_safe_filename_removes_windows_reserved_characters():
    assert safe_filename('A:B/C*D?"E<Z>|') == "A_B_C_D__E_Z__"


def test_default_output_uses_pdf_filename_and_epub_suffix():
    assert default_output_path_for_book(Path("货币战争4.pdf")) == Path("货币战争4_pinyin.epub")


def test_epub_title_from_metadata_drives_default_output(tmp_path: Path):
    source = tmp_path / "download-name.epub"
    with ZipFile(source, "w") as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        epub.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>""",
            compress_type=ZIP_DEFLATED,
        )
        epub.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>真正书名: 测试</dc:title></metadata>
  <manifest><item id="chapter" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest>
  <spine><itemref idref="chapter"/></spine>
</package>""",
            compress_type=ZIP_DEFLATED,
        )

    assert epub_title(source) == "真正书名: 测试"
    assert default_output_path_for_book(source) == tmp_path / "真正书名_ 测试_pinyin.epub"
