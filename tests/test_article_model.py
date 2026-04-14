import pytest
from datetime import datetime
from models.article import NormalizedArticle


def test_generate_id_consistency():
    url = "https://example.com/article"
    id1 = NormalizedArticle.generate_id(url)
    id2 = NormalizedArticle.generate_id(url)
    assert id1 == id2


def test_content_hash_consistency():
    title = "Test Title"
    content = "Test Content"
    h1 = NormalizedArticle.compute_content_hash(title, content)
    h2 = NormalizedArticle.compute_content_hash(title, content)
    assert h1 == h2


def test_valid_article_creation():
    article = NormalizedArticle(
        id="123",
        title="Test",
        source="bleepingcomputer",
        source_type="rss",
        credibility_tier=1,
        published_at=datetime.now(),
        content="Some content",
        tags=[],
        content_hash="abc",
        cvss_score=None,
    )
    assert article.title == "Test"


def test_invalid_credibility_tier():
    with pytest.raises(ValueError):
        NormalizedArticle(
            id="123",
            title="Test",
            source="x",
            source_type="rss",
            credibility_tier=5,
            published_at=datetime.now(),
            content="text",
            tags=[],
            content_hash="abc",
        )


def test_from_scraper_dict():
    data = {
        "url": "https://example.com",
        "title": "Sample",
        "source": "testsource",
        "published_at": datetime.now(),
        "content": "content here",
        "tags": ["security"],
    }

    article = NormalizedArticle.from_scraper_dict(data)

    assert article.id is not None
    assert article.content_hash is not None
    assert article.source_type == "scraper"


class MockEntry:
    def __init__(self):
        self.link = "https://rss.com/article"
        self.title = "RSS Title"
        self.summary = "RSS content"
        self.published_parsed = (2024, 1, 1, 0, 0, 0)


def test_from_rss_entry():
    entry = MockEntry()
    article = NormalizedArticle.from_rss_entry(entry)

    assert article.source_type == "rss"
    assert article.id is not None