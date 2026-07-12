from pathlib import Path

from mobi_pinyin.annotator import AnnotationOptions
import mobi_pinyin.calibre as calibre


class FakeBackend:
    def annotate(self, text: str):
        return [(char, None) for char in text]


def test_mobi_output_uses_kf8_capable_package(monkeypatch, tmp_path: Path):
    source = tmp_path / "book.mobi"
    output = tmp_path / "book.pinyin.mobi"
    source.write_bytes(b"mobi")
    commands: list[list[str]] = []

    monkeypatch.setattr(calibre.shutil, "which", lambda name: "ebook-convert")
    monkeypatch.setattr(calibre, "_run", lambda command: commands.append(command))
    monkeypatch.setattr(
        calibre,
        "annotate_epub",
        lambda input_path, output_path, backend, options, progress: Path(output_path).write_bytes(b"epub"),
    )

    calibre.annotate_via_calibre(source, output, FakeBackend(), AnnotationOptions())

    assert commands[-1][-2:] == ["--mobi-file-type", "both"]


def test_azw3_output_does_not_use_mobi_package_option(monkeypatch, tmp_path: Path):
    source = tmp_path / "book.azw3"
    output = tmp_path / "book.pinyin.azw3"
    source.write_bytes(b"azw3")
    commands: list[list[str]] = []

    monkeypatch.setattr(calibre.shutil, "which", lambda name: "ebook-convert")
    monkeypatch.setattr(calibre, "_run", lambda command: commands.append(command))
    monkeypatch.setattr(
        calibre,
        "annotate_epub",
        lambda input_path, output_path, backend, options, progress: Path(output_path).write_bytes(b"epub"),
    )

    calibre.annotate_via_calibre(source, output, FakeBackend(), AnnotationOptions())

    assert "--mobi-file-type" not in commands[-1]


def test_mobi_output_falls_back_to_kf8_only(monkeypatch, tmp_path: Path):
    source = tmp_path / "book.mobi"
    output = tmp_path / "book.pinyin.mobi"
    source.write_bytes(b"mobi")
    commands: list[list[str]] = []

    monkeypatch.setattr(calibre.shutil, "which", lambda name: "ebook-convert")

    def fake_run(command: list[str]) -> None:
        commands.append(command)
        if command[-1] == "both":
            raise RuntimeError("hybrid failed")

    monkeypatch.setattr(calibre, "_run", fake_run)
    monkeypatch.setattr(
        calibre,
        "annotate_epub",
        lambda input_path, output_path, backend, options, progress: Path(output_path).write_bytes(b"epub"),
    )

    calibre.annotate_via_calibre(source, output, FakeBackend(), AnnotationOptions())

    assert commands[-2][-2:] == ["--mobi-file-type", "both"]
    assert commands[-1][-2:] == ["--mobi-file-type", "new"]


def test_mobi_output_falls_back_to_legacy_mobi(monkeypatch, tmp_path: Path):
    source = tmp_path / "book.mobi"
    output = tmp_path / "book.pinyin.mobi"
    source.write_bytes(b"mobi")
    commands: list[list[str]] = []

    monkeypatch.setattr(calibre.shutil, "which", lambda name: "ebook-convert")

    def fake_run(command: list[str]) -> None:
        commands.append(command)
        if command[-1] in {"both", "new"}:
            raise RuntimeError("kf8 failed")

    monkeypatch.setattr(calibre, "_run", fake_run)
    monkeypatch.setattr(
        calibre,
        "annotate_epub",
        lambda input_path, output_path, backend, options, progress: Path(output_path).write_bytes(b"epub"),
    )

    calibre.annotate_via_calibre(source, output, FakeBackend(), AnnotationOptions())

    assert commands[-3][-2:] == ["--mobi-file-type", "both"]
    assert commands[-2][-2:] == ["--mobi-file-type", "new"]
    assert commands[-1][-2:] == ["--mobi-file-type", "old"]
