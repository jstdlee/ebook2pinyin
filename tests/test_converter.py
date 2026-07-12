from pathlib import Path

import pytest

import ebook2pinyin.converter as converter
from ebook2pinyin.converter import convert_book, default_output_path


def test_default_output_path_keeps_reader_format_except_pdf():
    assert default_output_path(Path("book.epub")) == Path("book_pinyin.epub")
    assert default_output_path(Path("book.mobi")) == Path("book_pinyin.mobi")
    assert default_output_path(Path("book.pdf")) == Path("book_pinyin.epub")


def test_convert_book_requires_matching_output_format(tmp_path: Path):
    source = tmp_path / "book.epub"
    source.write_bytes(b"not a real epub")

    with pytest.raises(ValueError, match="Output format must match input format"):
        convert_book(source, tmp_path / "book.pdf")


def test_pdf_input_can_output_epub_or_pdf(tmp_path: Path, monkeypatch):
    source = tmp_path / "book.pdf"
    source.write_bytes(b"not a real pdf")
    calls: list[str] = []

    monkeypatch.setattr(converter, "PyPinyinBackend", lambda style: object())
    monkeypatch.setattr(
        converter,
        "pdf_to_epub",
        lambda source, destination, backend, options, progress: calls.append("epub") or destination,
    )
    monkeypatch.setattr(
        converter,
        "annotate_pdf",
        lambda source, destination, backend, options, progress: calls.append("pdf") or destination,
    )

    assert convert_book(source, tmp_path / "book.pinyin.epub") == tmp_path / "book.pinyin.epub"
    assert convert_book(source, tmp_path / "book.pinyin.pdf") == tmp_path / "book.pinyin.pdf"
    assert calls == ["epub", "pdf"]


def test_pdf_input_rejects_other_output_formats(tmp_path: Path):
    source = tmp_path / "book.pdf"
    source.write_bytes(b"not a real pdf")

    with pytest.raises(ValueError, match="PDF output format"):
        convert_book(source, tmp_path / "book.mobi")
