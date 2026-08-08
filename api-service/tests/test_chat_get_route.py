from unittest.mock import MagicMock


def _client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


class TestChatGetRoute:
    def test_renders_without_article_id(self, mocker):
        client = _client()
        response = client.get("/chat")
        assert response.status_code == 200
        assert b"pendingArticleId = null;" in response.data

    def test_renders_with_article_context_when_article_id_given(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_article_by_id.return_value = {
            "id": "1", "title": "Critical RCE Found", "url": "https://x.com",
            "summary": "s", "source_name": "Krebs",
        }
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/chat?article_id=1")
        assert response.status_code == 200
        assert b"Critical RCE Found" in response.data
        mock_db.get_article_by_id.assert_called_once_with("1")

    def test_unknown_article_id_renders_normally(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_article_by_id.return_value = None
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/chat?article_id=nonexistent")
        assert response.status_code == 200
        assert b"pendingArticleId = null;" in response.data

    def test_apostrophe_in_title_escaped_safely(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_article_by_id.return_value = {
            "id": "1", "title": "Hacker's New Toolkit Exposed", "url": "https://x.com",
            "summary": "s", "source_name": "Krebs",
        }
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/chat?article_id=1")
        body = response.get_data(as_text=True)
        assert "\\u0027" in body
        assert "\\\\'" not in body
