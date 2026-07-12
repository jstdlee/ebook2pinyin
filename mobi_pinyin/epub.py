from __future__ import annotations

from pathlib import Path, PurePosixPath
import posixpath
import zipfile
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from .annotator import AnnotationOptions, PinyinBackend, annotate_html, ruby_css
from .progress import ProgressCallback, Stage, noop_progress


CONTAINER = "META-INF/container.xml"
OPF_NS = "http://www.idpf.org/2007/opf"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
HTML_MEDIA_TYPES = {
    "application/xhtml+xml",
    "text/html",
}


def annotate_epub(
    input_path: Path,
    output_path: Path,
    backend: PinyinBackend,
    options: AnnotationOptions,
    progress: ProgressCallback = noop_progress,
) -> Path:
    progress(Stage("read", 0, 1, "Reading EPUB package"))
    with zipfile.ZipFile(input_path, "r") as source:
        entries = {info.filename: source.read(info.filename) for info in source.infolist()}
        infos = {info.filename: info for info in source.infolist()}

    opf_path = _find_opf_path(entries)
    opf_root = ET.fromstring(entries[opf_path])
    html_items = _html_manifest_items(opf_root, opf_path)
    css_path = _css_path_for_opf(opf_path)

    total = max(len(html_items), 1)
    for index, item_path in enumerate(html_items, start=1):
        progress(Stage("annotate", index, total, f"Annotating {item_path}"))
        raw = entries.get(item_path)
        if raw is None:
            continue
        entries[item_path] = annotate_html(
            raw.decode(_guess_encoding(raw), errors="replace"),
            backend,
            options,
            inject_css=False,
        ).encode("utf-8")
        entries[item_path] = _link_stylesheet(entries[item_path], _relative_href(item_path, css_path))

    progress(Stage("package", 0, 1, "Writing EPUB package"))
    entries[css_path] = ruby_css(options).encode("utf-8")
    entries[opf_path] = _ensure_css_manifest(opf_root, opf_path, css_path)
    _write_epub(output_path, entries, infos)
    progress(Stage("done", 1, 1, f"Wrote {output_path.name}"))
    return output_path


def _find_opf_path(entries: dict[str, bytes]) -> str:
    if CONTAINER not in entries:
        raise ValueError("Invalid EPUB: missing META-INF/container.xml")

    container = ET.fromstring(entries[CONTAINER])
    rootfile = container.find(f".//{{{CONTAINER_NS}}}rootfile")
    if rootfile is None:
        rootfile = container.find(".//rootfile")
    if rootfile is None or "full-path" not in rootfile.attrib:
        raise ValueError("Invalid EPUB: missing rootfile full-path")
    return rootfile.attrib["full-path"]


def _html_manifest_items(opf_root: ET.Element, opf_path: str) -> list[str]:
    opf_dir = posixpath.dirname(opf_path)
    items: list[str] = []
    for item in opf_root.findall(f".//{{{OPF_NS}}}item") + opf_root.findall(".//item"):
        media_type = item.attrib.get("media-type", "")
        href = item.attrib.get("href", "")
        if not href:
            continue
        ext = PurePosixPath(href.split("#", 1)[0].split("?", 1)[0]).suffix.lower()
        if media_type in HTML_MEDIA_TYPES or ext in {".html", ".htm", ".xhtml"}:
            items.append(posixpath.normpath(posixpath.join(opf_dir, href)))
    return sorted(dict.fromkeys(items))


def _css_path_for_opf(opf_path: str) -> str:
    opf_dir = posixpath.dirname(opf_path)
    return posixpath.normpath(posixpath.join(opf_dir, "mobi-pinyin.css"))


def _relative_href(from_item: str, to_item: str) -> str:
    from_dir = posixpath.dirname(from_item) or "."
    return posixpath.relpath(to_item, from_dir)


def _link_stylesheet(html_bytes: bytes, href: str) -> bytes:
    soup = BeautifulSoup(html_bytes.decode("utf-8", errors="replace"), "html.parser")
    head = soup.head
    if head is None:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)
    existing = head.find("link", attrs={"data-mobi-pinyin": "true"})
    if existing is None:
        link = soup.new_tag("link", rel="stylesheet", href=href)
        link["data-mobi-pinyin"] = "true"
        head.append(link)
    else:
        existing["href"] = href
    return str(soup).encode("utf-8")


def _ensure_css_manifest(opf_root: ET.Element, opf_path: str, css_path: str) -> bytes:
    ET.register_namespace("", OPF_NS)
    manifest = opf_root.find(f".//{{{OPF_NS}}}manifest")
    if manifest is None:
        manifest = opf_root.find(".//manifest")
    if manifest is None:
        raise ValueError("Invalid EPUB: missing OPF manifest")

    href = _relative_href(opf_path, css_path)
    for item in list(manifest):
        if item.attrib.get("href") == href or item.attrib.get("id") == "mobi-pinyin-css":
            item.attrib.update({"href": href, "media-type": "text/css", "id": "mobi-pinyin-css"})
            break
    else:
        namespace = _namespace(manifest.tag)
        item_tag = f"{{{namespace}}}item" if namespace else "item"
        item = ET.Element(
            item_tag,
            {"id": "mobi-pinyin-css", "href": href, "media-type": "text/css"},
        )
        manifest.append(item)

    return ET.tostring(opf_root, encoding="utf-8", xml_declaration=True)


def _namespace(tag: str) -> str | None:
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None


def _guess_encoding(raw: bytes) -> str:
    sample = raw[:300].decode("ascii", errors="ignore").lower()
    if "charset=gb" in sample or "encoding=\"gb" in sample:
        return "gb18030"
    return "utf-8"


def _write_epub(output_path: Path, entries: dict[str, bytes], infos: dict[str, zipfile.ZipInfo]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w") as target:
        if "mimetype" in entries:
            target.writestr("mimetype", entries["mimetype"], compress_type=zipfile.ZIP_STORED)
        for filename, data in entries.items():
            if filename == "mimetype":
                continue
            source_info = infos.get(filename)
            compress_type = source_info.compress_type if source_info else zipfile.ZIP_DEFLATED
            target.writestr(filename, data, compress_type=compress_type)
