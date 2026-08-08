import json
from unittest.mock import MagicMock


def _client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


class TestChatPostRoute:
    def test_missing_message_returns_400(self, mocker):
        client = _client()
        response = client.post("/chat", json={"session_id": "s1"})
        assert response.status_code == 400

    def test_article_id_in_payload_fetches_and_force_grounds(self, mocker):
        from routes import NewsRoutes
        mock_news_db = MagicMock()
        article = {"id": "1", "title": "Critical RCE Found", "summary": "s", "source_name": "Krebs"}
        mock_news_db.get_article_by_id.return_value = article
        mocker.patch.object(NewsRoutes, "news_db", mock_news_db)

        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "llm_response": json.dumps({"message": "answer", "articles": []}),
            "intent": "grounded",
        }
        mocker.patch("agents.agent_graph", mock_graph)

        client = _client()
        response = client.post("/chat", json={
            "message": "tell me about this article: Critical RCE Found",
            "session_id": "s1",
            "article_id": "1",
        })
        assert response.status_code == 200
        mock_news_db.get_article_by_id.assert_called_once_with("1")
        invoke_kwargs = mock_graph.invoke.call_args[0][0]
        assert invoke_kwargs["active_article"] == article
        assert invoke_kwargs["force_grounded"] is True

    def test_no_article_id_never_grounds(self, mocker):
        """Grounding is single-turn only - a plain follow-up message with no
        article_id in the payload never grounds, regardless of prior turns."""
        from routes import NewsRoutes
        mock_news_db = MagicMock()
        mocker.patch.object(NewsRoutes, "news_db", mock_news_db)

        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "llm_response": json.dumps({"message": "answer", "articles": [{"headlines": "x"}]}),
            "intent": "search",
        }
        mocker.patch("agents.agent_graph", mock_graph)

        client = _client()
        response = client.post("/chat", json={"message": "tell me more", "session_id": "s1"})
        assert response.status_code == 200
        mock_news_db.get_article_by_id.assert_not_called()
        invoke_kwargs = mock_graph.invoke.call_args[0][0]
        assert invoke_kwargs["active_article"] is None
        assert invoke_kwargs["force_grounded"] is False
