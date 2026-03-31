"""
Unit tests for the CyberNews aggregator package.

Bug fixes vs. the original unitTest_cybernews.py
──────────────────────────────────────────────────
1. setUp calls CyberNews() which immediately instantiates Extractor,
   RSSExtractor, YouTubeConnector, and NewsAPIConnector — all of which
   make network calls or require API keys. All external I/O is now mocked.

2. test_get_news called self.news.get_news(news) for every valid news type,
   which triggers real HTTP scraping. Replaced with mocked Extractor responses.

3. Added tests for the Sorting utility (pure logic, no mocks needed).
4. Added tests for the Performance utility (pure logic, no mocks needed).
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_ARTICLE = {
    "id": 20250101,
    "headlines": "Critical CVE-2025-9999 found in OpenSSL",
    "author":    "CISA",
    "fullNews":  "A critical remote code execution vulnerability was disclosed in OpenSSL...",
    "newsURL":   "https://cisa.gov/known-exploited-vulnerabilities/cve-2025-9999",
    "newsImgURL": "https://cisa.gov/img/cve.png",
    "newsDate":  "January 01, 2025",
}


def _make_cybernews_with_mock_extractor():
    """
    Return a CyberNews instance where all external I/O is replaced with mocks.

    Strategy: construct the object first, then swap its private attributes so
    no real HTTP requests or API calls ever fire. This avoids the complexity of
    patching module-level imports before the class is instantiated.
    """
    from cybernews.CyberNews import CyberNews

    # Stub Extractor so its __init__ (httpx.Client) never fires
    mock_extractor = MagicMock()
    mock_extractor.data_extractor.return_value = [SAMPLE_ARTICLE.copy()]

    mock_rss  = MagicMock()
    mock_rss.process_feeds.return_value = []

    mock_yt   = MagicMock()
    mock_yt.extract.return_value = []

    mock_napi = MagicMock()
    mock_napi.extract.return_value = []

    # Patch the four constructors so __init__ uses mocks, not real classes
    with patch("cybernews.CyberNews.Extractor",        return_value=mock_extractor), \
         patch("cybernews.CyberNews.RSSExtractor",     return_value=mock_rss), \
         patch("cybernews.CyberNews.YouTubeConnector", return_value=mock_yt), \
         patch("cybernews.CyberNews.NewsAPIConnector", return_value=mock_napi):
        news = CyberNews()

    # The object now holds references to our mocks — no context manager needed
    return news




# ─────────────────────────────────────────────────────────────────────────────
# CyberNews tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCyberNewsInit:
    """CyberNews.__init__ loads news_types.json and social_sources.json."""

    def test_get_news_types_is_not_empty(self):
        news = _make_cybernews_with_mock_extractor()
        news_types = news.get_news_types
        assert isinstance(news_types, list)
        assert len(news_types) > 0

    def test_known_news_types_are_present(self):
        news = _make_cybernews_with_mock_extractor()
        news_types = news.get_news_types
        for expected in ["general", "dataBreach", "cyberAttack", "vulnerability", "malware", "security"]:
            assert expected in news_types, f"'{expected}' missing from news_types"


class TestCyberNewsGetNews:
    """CyberNews.get_news() returns a list of articles for valid types."""

    @pytest.mark.parametrize("news_type", [
        "general", "dataBreach", "cyberAttack", "vulnerability", "malware", "security",
    ])
    def test_get_news_returns_list_for_valid_type(self, news_type):
        news = _make_cybernews_with_mock_extractor()
        result = news.get_news(news_type)
        assert isinstance(result, list), f"get_news('{news_type}') should return a list"
        assert len(result) > 0, f"get_news('{news_type}') should return at least one article"

    @pytest.mark.parametrize("news_type", [
        "general", "dataBreach", "cyberAttack",
    ])
    def test_each_article_has_required_keys(self, news_type):
        news = _make_cybernews_with_mock_extractor()
        articles = news.get_news(news_type)
        required = {"headlines", "author", "fullNews", "newsURL", "newsDate"}
        for article in articles:
            missing = required - set(article.keys())
            assert not missing, f"Article missing keys: {missing}"

    @pytest.mark.parametrize("invalid_type", ["", "Invalid", "hacking", "123"])
    def test_get_news_raises_valueerror_for_invalid_type(self, invalid_type):
        news = _make_cybernews_with_mock_extractor()
        with pytest.raises(ValueError, match=f"'{invalid_type}'"):
            news.get_news(invalid_type)


# ─────────────────────────────────────────────────────────────────────────────
# Sorting utility tests  (pure logic — no mocks needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestSorting:
    """cybernews.sorting.Sorting — date parsing and ordering logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from cybernews.sorting import Sorting
        self.sorting = Sorting()

    def test_ordering_date_american_format(self):
        """'January 15, 2025' → integer 20250115."""
        result = self.sorting.ordering_date("January 15, 2025")
        assert result == 20250115

    def test_ordering_date_day_first_format(self):
        """'15 January 2025' → integer 20250115."""
        result = self.sorting.ordering_date("15 January 2025")
        assert result == 20250115

    def test_ordering_date_na_returns_1(self):
        """'N/A' dates get the lowest sort priority (1)."""
        result = self.sorting.ordering_date("N/A")
        assert result == 1

    def test_ordering_date_invalid_returns_1(self):
        """Unparseable strings fall back to 1."""
        result = self.sorting.ordering_date("not a date")
        assert result == 1

    def test_ordering_news_sorts_newest_first(self):
        articles = [
            {"id": self.sorting.ordering_date("January 01, 2024"), "headlines": "Old"},
            {"id": self.sorting.ordering_date("January 01, 2025"), "headlines": "New"},
            {"id": self.sorting.ordering_date("January 01, 2023"), "headlines": "Older"},
        ]
        sorted_articles = self.sorting.ordering_news(articles)
        assert sorted_articles[0]["headlines"] == "New"
        assert sorted_articles[-1]["headlines"] == "Older"

    def test_ordering_news_assigns_uuid_ids(self):
        """After sorting, all IDs are reassigned as large integers (UUID ints)."""
        articles = [{"id": 20250101, "headlines": "Test"}]
        sorted_articles = self.sorting.ordering_news(articles)
        # UUID int is much larger than a date integer
        assert sorted_articles[0]["id"] > 10 ** 15


# ─────────────────────────────────────────────────────────────────────────────
# Performance utility tests  (pure logic — no mocks needed)
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """cybernews.performance.Performance — text cleaning and validation helpers."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from cybernews.performance import Performance
        self.perf = Performance()

    def test_remove_symbols_strips_non_alphanumeric(self):
        assert self.perf.remove_symbols("hello, world!") == "hello world"

    def test_remove_symbols_empty_string(self):
        assert self.perf.remove_symbols("") == ""

    def test_remove_symbols_none_returns_empty(self):
        assert self.perf.remove_symbols(None) == ""

    def test_valid_url_check_accepts_https(self):
        assert self.perf.valid_url_check("https://cisa.gov") is True

    def test_valid_url_check_accepts_http(self):
        assert self.perf.valid_url_check("http://example.com") is True

    def test_valid_url_check_rejects_relative(self):
        assert self.perf.valid_url_check("/relative/path") is False

    def test_valid_url_check_rejects_empty(self):
        assert self.perf.valid_url_check("") is False

    def test_spam_content_check_detects_known_keywords(self):
        assert self.perf.spam_content_check("buy now limited offer") is True

    def test_spam_content_check_passes_clean_content(self):
        assert self.perf.spam_content_check("Critical CVE in OpenSSL patched") is False

    def test_is_valid_author_name_rejects_date_strings(self):
        """A date like 'Jan 01 2025' should NOT be treated as an author name."""
        assert self.perf.is_valid_author_name("Jan 01 2025") is False

    def test_is_valid_author_name_accepts_real_names(self):
        assert self.perf.is_valid_author_name("John Doe") is True

    def test_format_author_name_collapses_whitespace(self):
        assert self.perf.format_author_name("  John   Doe  ") == "John Doe"
