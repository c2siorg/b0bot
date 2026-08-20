from unittest.mock import MagicMock


def _client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


class TestDashboardRoute:
    def test_renders_with_default_newest_filter(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_dashboard_feed.return_value = []
        mock_db.get_top_news.return_value = []
        mock_db.get_cve_watchlist.return_value = []
        mock_db.get_distinct_sources.return_value = []
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/dashboard")
        assert response.status_code == 200
        mock_db.get_dashboard_feed.assert_called_once_with(filter="newest", source=None)

    def test_invalid_filter_falls_back_to_newest(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_dashboard_feed.return_value = []
        mock_db.get_top_news.return_value = []
        mock_db.get_cve_watchlist.return_value = []
        mock_db.get_distinct_sources.return_value = []
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/dashboard?filter=' OR 1=1--")
        assert response.status_code == 200
        mock_db.get_dashboard_feed.assert_called_once_with(filter="newest", source=None)

    def test_valid_filter_and_source_passed_through(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_dashboard_feed.return_value = []
        mock_db.get_top_news.return_value = []
        mock_db.get_cve_watchlist.return_value = []
        mock_db.get_distinct_sources.return_value = []
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/dashboard?filter=critical&source=Krebs")
        assert response.status_code == 200
        mock_db.get_dashboard_feed.assert_called_once_with(filter="critical", source="Krebs")

    def test_feed_content_rendered(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_dashboard_feed.return_value = [
            {"id": "1", "title": "Test Article", "url": "https://x.com", "summary": "a summary", "source_name": "Krebs", "ingested_time": "10:30"}
        ]
        mock_db.get_top_news.return_value = []
        mock_db.get_cve_watchlist.return_value = []
        mock_db.get_distinct_sources.return_value = []
        mocker.patch.object(NewsRoutes, "news_db", mock_db)
        client = _client()
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"Test Article" in response.data
