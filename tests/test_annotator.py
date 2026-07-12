from ebook2pinyin.annotator import AnnotationOptions, annotate_html, annotate_text


class FakeBackend:
    values = {"中": "zhong", "国": "guo", "书": "shu"}

    def annotate(self, text: str):
        return [(char, self.values.get(char)) for char in text]


def test_annotate_text_wraps_only_chinese_characters():
    assert annotate_text("中国 A", FakeBackend()) == (
        '<ruby class="pinyin-ruby">中<rt>zhong</rt></ruby>'
        '<ruby class="pinyin-ruby">国<rt>guo</rt></ruby> A'
    )


def test_annotate_html_skips_existing_ruby_and_scripts():
    html = "<html><body><p>中国</p><ruby>书<rt>shu</rt></ruby><script>中国</script></body></html>"
    annotated = annotate_html(html, FakeBackend(), AnnotationOptions())

    assert annotated.count('<ruby class="pinyin-ruby">') == 2
    assert "<script>中国</script>" in annotated
    assert "<ruby>书<rt>shu</rt></ruby>" in annotated
