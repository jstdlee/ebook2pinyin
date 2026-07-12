from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from xml.etree import ElementTree as ET


CONTAINER = "META-INF/container.xml"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
DC_NS = "http://purl.org/dc/elements/1.1/"
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
WHITESPACE = re.compile(r"\s+")


def default_output_path_for_book(source: Path) -> Path:
    title = book_title(source)
    output_suffix = ".epub" if source.suffix.lower() == ".pdf" else source.suffix
    filename = f"{safe_filename(title)}_pinyin{output_suffix}"
    return source.with_name(filename)


def book_title(source: Path) -> str:
    suffix = source.suffix.lower()
    if suffix == ".epub":
        return epub_title(source) or source.stem
    if suffix in {".mobi", ".azw3"}:
        return calibre_title(source) or source.stem
    return source.stem


def epub_title(source: Path) -> str | None:
    try:
        with zipfile.ZipFile(source, "r") as epub:
            container = ET.fromstring(epub.read(CONTAINER))
            rootfile = container.find(f".//{{{CONTAINER_NS}}}rootfile")
            if rootfile is None:
                rootfile = container.find(".//rootfile")
            if rootfile is None:
                return None
            opf_path = rootfile.attrib.get("full-path")
            if not opf_path:
                return None
            opf = ET.fromstring(epub.read(opf_path))
    except (KeyError, ET.ParseError, zipfile.BadZipFile, OSError):
        return None

    title = opf.findtext(f".//{{{DC_NS}}}title") or opf.findtext(".//title")
    return normalize_title(title)


def calibre_title(source: Path) -> str | None:
    ebook_meta = shutil.which("ebook-meta")
    if not ebook_meta:
        return None
    try:
        completed = subprocess.run(
            [ebook_meta, str(source)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    for line in completed.stdout.splitlines():
        if line.lower().startswith("title"):
            _, _, value = line.partition(":")
            return normalize_title(value)
    return None


def normalize_title(title: str | None) -> str | None:
    if not title:
        return None
    title = WHITESPACE.sub(" ", title).strip()
    return title or None


def safe_filename(value: str, max_length: int = 120) -> str:
    value = normalize_title(value) or "book"
    value = INVALID_FILENAME_CHARS.sub("_", value)
    value = value.rstrip(" .")
    if len(value) > max_length:
        value = value[:max_length].rstrip(" .")
    return value or "book"
