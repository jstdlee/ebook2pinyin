from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re
from typing import Iterable, Protocol

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
SKIP_TEXT_PARENTS = {
    "script",
    "style",
    "ruby",
    "rt",
    "rp",
    "svg",
    "math",
    "textarea",
    "code",
    "pre",
}


class PinyinDependencyError(RuntimeError):
    """Raised when the pinyin backend is unavailable."""


class PinyinBackend(Protocol):
    def annotate(self, text: str) -> list[tuple[str, str | None]]:
        """Return one `(character, pinyin)` tuple per character."""


@dataclass(frozen=True)
class AnnotationOptions:
    ruby_size: float = 1.0
    rt_size: float = 0.5
    line_height: float = 1.9
    style: str = "tone"


class PyPinyinBackend:
    def __init__(self, style: str = "tone") -> None:
        try:
            from pypinyin import Style, lazy_pinyin
        except ImportError as exc:
            raise PinyinDependencyError(
                "pypinyin is required for Chinese annotation. "
                "Install it with: python -m pip install pypinyin"
            ) from exc

        styles = {
            "tone": Style.TONE,
            "tone2": Style.TONE2,
            "tone3": Style.TONE3,
            "plain": Style.NORMAL,
        }
        if style not in styles:
            valid = ", ".join(sorted(styles))
            raise ValueError(f"Unsupported pinyin style '{style}'. Choose one of: {valid}.")

        self._lazy_pinyin = lazy_pinyin
        self._style = styles[style]

    def annotate(self, text: str) -> list[tuple[str, str | None]]:
        pinyin_values = iter(
            self._lazy_pinyin(text, style=self._style, errors=lambda chars: list(chars))
        )
        annotated: list[tuple[str, str | None]] = []
        for char in text:
            if is_chinese(char):
                annotated.append((char, next(pinyin_values)))
            else:
                annotated.append((char, None))
                next(pinyin_values, None)
        return annotated


def is_chinese(char: str) -> bool:
    return bool(CJK_RE.fullmatch(char))


def ruby_css(options: AnnotationOptions) -> str:
    return f"""
ruby.pinyin-ruby {{
  font-size: {options.ruby_size:.3g}em;
  line-height: {options.line_height:.3g}em;
  padding: 0 0.08em;
  letter-spacing: 0;
}}

ruby.pinyin-ruby rt {{
  font-size: {options.rt_size:.3g}em;
  font-family: sans-serif;
  line-height: 1;
}}
""".strip()


def annotate_text(text: str, backend: PinyinBackend) -> str:
    pieces: list[str] = []
    for char, pinyin in backend.annotate(text):
        if pinyin and is_chinese(char):
            pieces.append(
                f'<ruby class="pinyin-ruby">{escape(char)}<rt>{escape(pinyin)}</rt></ruby>'
            )
        else:
            pieces.append(escape(char))
    return "".join(pieces)


def annotate_html(
    html: str,
    backend: PinyinBackend,
    options: AnnotationOptions | None = None,
    inject_css: bool = True,
) -> str:
    options = options or AnnotationOptions()
    soup = BeautifulSoup(html, "html.parser")

    for node in _candidate_text_nodes(soup):
        if not CJK_RE.search(str(node)):
            continue
        fragment = BeautifulSoup(annotate_text(str(node), backend), "html.parser")
        node.replace_with(*fragment.contents)

    if inject_css:
        _inject_inline_css(soup, ruby_css(options))

    return str(soup)


def _candidate_text_nodes(soup: BeautifulSoup) -> Iterable[NavigableString]:
    for node in list(soup.find_all(string=True)):
        parent = node.parent
        if not parent:
            continue
        if _has_skipped_parent(parent):
            continue
        if not node.strip():
            continue
        yield node


def _has_skipped_parent(tag: Tag) -> bool:
    current: Tag | None = tag
    while current is not None and getattr(current, "name", None):
        if current.name.lower() in SKIP_TEXT_PARENTS:
            return True
        current = current.parent if isinstance(current.parent, Tag) else None
    return False


def _inject_inline_css(soup: BeautifulSoup, css: str) -> None:
    head = soup.head
    if head is None:
        html = soup.html
        head = soup.new_tag("head")
        if html is not None:
            html.insert(0, head)
        else:
            soup.insert(0, head)

    existing = head.find("style", attrs={"data-ebook2pinyin": "true"})
    if existing is None:
        style = soup.new_tag("style")
        style["data-ebook2pinyin"] = "true"
        style.string = css
        head.append(style)
    else:
        existing.string = css
