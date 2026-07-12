from pathlib import Path

from mobi_pinyin.progress import Stage
import mobi_pinyin.web as web


class UploadedFile:
    def __init__(self, name: str) -> None:
        self.name = name


def test_web_conversion_streams_progress_before_result(tmp_path: Path, monkeypatch):
    source = tmp_path / "book.epub"
    source.write_text("dummy", encoding="utf-8")

    def fake_convert_book(input_path, output_path, *, options, progress):
        progress(Stage("read", 0, 1, "Reading EPUB package"))
        progress(Stage("annotate", 1, 2, "Annotating chapter.xhtml"))
        Path(output_path).write_text("done", encoding="utf-8")
        progress(Stage("done", 1, 1, "Wrote book.pinyin.epub"))
        return Path(output_path)

    monkeypatch.setattr(web, "convert_book", fake_convert_book)

    updates = list(web._convert_upload(UploadedFile(str(source)), 1.0, 0.5, 1.9, "tone"))

    assert updates[0] == (None, "[queued] Starting conversion")
    assert any("Annotating chapter.xhtml" in status for _, status in updates)
    assert updates[-1][0].endswith("book_pinyin.epub")
    assert "Wrote book.pinyin.epub" in updates[-1][1]
