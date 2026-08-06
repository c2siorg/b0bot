from unittest.mock import MagicMock


def _client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


class TestSourcesGetRoute:
    def test_get_renders_source_list(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.get_all_sources.return_value = [
            {"id": "1", "name": "Test Feed", "url": "https://example.com/feed", "status": "active"}
        ]
        mocker.patch.object(NewsRoutes, "source_db", mock_db)
        client = _client()
        response = client.get("/sources")
        assert response.status_code == 200
        assert b"Test Feed" in response.data


class TestAddSourceRoute:
    def test_missing_url_returns_400(self, mocker):
        client = _client()
        response = client.post("/sources", json={"name": "Test"})
        assert response.status_code == 400
        assert response.get_json()["success"] is False

    def test_invalid_url_format_returns_400(self, mocker):
        client = _client()
        response = client.post("/sources", json={"name": "Test", "url": "not-a-url"})
        assert response.status_code == 400
        assert response.get_json()["message"] == "please enter a valid url"

    def test_duplicate_url_returns_409(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.create_source.return_value = False
        mocker.patch.object(NewsRoutes, "source_db", mock_db)
        client = _client()
        response = client.post("/sources", json={"name": "Test", "url": "https://example.com/feed"})
        assert response.status_code == 409
        assert response.get_json()["message"] == "that source already exists"

    def test_db_error_returns_500(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.create_source.return_value = None
        mocker.patch.object(NewsRoutes, "source_db", mock_db)
        client = _client()
        response = client.post("/sources", json={"name": "Test", "url": "https://example.com/feed"})
        assert response.status_code == 500
        assert response.get_json()["success"] is False

    def test_successful_add_returns_200(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.create_source.return_value = True
        mocker.patch.object(NewsRoutes, "source_db", mock_db)
        client = _client()
        response = client.post("/sources", json={"name": "Test Feed", "url": "https://example.com/feed"})
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        mock_db.create_source.assert_called_once_with(name="Test Feed", url="https://example.com/feed")
