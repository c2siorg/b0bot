import pytest
from unittest.mock import MagicMock


def make_state(**kwargs):
    base = {
        "user_input": "",
        "intent": None,
        "keywords": [],
        "retrieved_articles": [],
        "llm_response": None,
        "session_id": "test-session",
        "chat_history": [],
        "notification_triggered": False,
        "analysis": None,
    }
    base.update(kwargs)
    return base


class TestScraperAgent:
    def test_keyword_search_called_with_meaningful_keywords(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = [{"headlines": "t", "author": "x", "newsDate": "01/01/2026", "newsURL": "http://x.com", "fullNews": ""}]
        mocker.patch.object(scraper_module, "db", mock_db)
        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware", "attack"])
        scraper_agent(state)
        mock_db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="ransomware attack", search_type="hybrid", query_vector=None
        )

    def test_generic_terms_filtered_out(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = [{"headlines": "t", "author": "x", "newsDate": "01/01/2026", "newsURL": "http://x.com", "fullNews": ""}]
        mocker.patch.object(scraper_module, "db", mock_db)
        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["cybersecurity", "news", "ransomware"])
        scraper_agent(state)
        mock_db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="ransomware", search_type="hybrid", query_vector=None
        )

    def test_falls_back_when_all_keywords_are_generic(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = []
        mocker.patch.object(scraper_module, "db", mock_db)
        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["cybersecurity", "news"])
        scraper_agent(state)
        mock_db.get_news_collections.assert_called_once_with()

    def test_falls_back_when_keyword_search_returns_empty(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.side_effect = [[], [{"headlines": "test", "author": "x", "newsDate": "01/01/2026", "newsURL": "http://x.com", "fullNews": ""}]]
        mocker.patch.object(scraper_module, "db", mock_db)
        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware"])
        scraper_agent(state)
        assert mock_db.get_news_collections.call_count == 2

    def test_articles_normalized_correctly(self, mocker):
        from agents import scraper as scraper_module
        raw = [{"headlines": "Test", "author": "Src", "newsDate": "01/01/2026", "newsURL": "http://x.com", "fullNews": "body text"}]
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = raw
        mocker.patch.object(scraper_module, "db", mock_db)
        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware"])
        result = scraper_agent(state)
        assert result["retrieved_articles"][0] == {"title": "Test", "source": "Src", "date": "01/01/2026", "url": "http://x.com", "body": "body text"}

    def test_query_embedded_and_passed_to_hybrid_search(self, mocker):
        from agents import scraper as scraper_module
        mock_db = MagicMock()
        mock_db.get_news_collections.return_value = [{"headlines": "t", "author": "x", "newsDate": "01/01/2026", "newsURL": "http://x.com", "fullNews": ""}]
        mocker.patch.object(scraper_module, "db", mock_db)
        mock_vector = [0.1] * 384
        mocker.patch.object(scraper_module, "generate_embedding", return_value=mock_vector)
        from agents.scraper import scraper_agent
        state = make_state(intent="search", keywords=["ransomware", "attack"], user_input="latest ransomware attack news")
        scraper_agent(state)
        mock_db.get_news_collections.assert_called_once_with(
            is_keyword=True, keyword="ransomware attack", search_type="hybrid", query_vector=mock_vector
        )
