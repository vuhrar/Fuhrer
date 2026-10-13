from official_source_sync import _extract_articles


def test_extracts_numeric_official_articles():
    text = "المادة 1: هذا نص نظامي طويل موثق. المادة 2: نص المادة الثانية الموثق بشكل كافٍ."
    articles = _extract_articles(text)
    assert [item["article"] for item in articles] == ["1", "2"]
    assert all(item["needs_verification"] is False for item in articles)


def test_extracts_arabic_heading_articles_when_numeric_markers_are_absent():
    text = "المادة الأولى: " + ("نص نظامي " * 10) + " المادة الثانية: " + ("نص نظامي " * 10)
    articles = _extract_articles(text)
    assert len(articles) == 2
    assert articles[0]["article"] == "1"
    assert articles[1]["article"] == "2"


def test_short_or_untrusted_content_is_not_promoted():
    assert _extract_articles("صفحة لا تحتوي على مواد نظامية") == []
