from unittest.mock import MagicMock


def _client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


class TestSubscribeFormRoute:
    def test_get_renders_form_with_interest_tags(self, mocker):
        client = _client()
        response = client.get("/subscribe")
        assert response.status_code == 200
        assert b"malware" in response.data
        assert b"ransomware" in response.data

    def test_email_prefilled_from_query_param(self, mocker):
        client = _client()
        response = client.get("/subscribe?email=test@example.com")
        assert response.status_code == 200
        assert b'value="test@example.com"' in response.data

    def test_no_email_param_renders_empty_prefill(self, mocker):
        client = _client()
        response = client.get("/subscribe")
        assert response.status_code == 200
        assert b'value=""' in response.data
        assert b"value=\"None\"" not in response.data


class TestSubscribePostRoute:
    def test_missing_email_returns_400(self, mocker):
        client = _client()
        response = client.post("/subscribe", json={"frequency": "daily", "interests": []})
        assert response.status_code == 400
        assert response.get_json()["success"] is False

    def test_invalid_frequency_returns_400(self, mocker):
        client = _client()
        response = client.post("/subscribe", json={"email": "test@example.com", "frequency": "monthly"})
        assert response.status_code == 400

    def test_unknown_interest_tags_filtered_out(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = True
        mocker.patch.object(NewsRoutes, "db", mock_db)
        client = _client()
        response = client.post("/subscribe", json={
            "email": "test@example.com",
            "frequency": "daily",
            "interests": ["malware", "not-a-real-tag"],
        })
        assert response.status_code == 200
        mock_db.create_subscriber.assert_called_once_with(email="test@example.com", frequency="daily", interests=["malware"])

    def test_db_failure_returns_500(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = False
        mocker.patch.object(NewsRoutes, "db", mock_db)
        client = _client()
        response = client.post("/subscribe", json={"email": "test@example.com", "frequency": "daily", "interests": []})
        assert response.status_code == 500
        assert response.get_json()["success"] is False

    def test_successful_subscribe_returns_200(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.create_subscriber.return_value = True
        mocker.patch.object(NewsRoutes, "db", mock_db)
        client = _client()
        response = client.post("/subscribe", json={"email": "test@example.com", "frequency": "weekly", "interests": ["cve"]})
        assert response.status_code == 200
        assert response.get_json()["success"] is True


class TestUnsubscribeRoute:
    def test_success_renders_confirmation(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.unsubscribe.return_value = True
        mocker.patch.object(NewsRoutes, "db", mock_db)
        client = _client()
        response = client.get("/unsubscribe/some-uuid")
        assert response.status_code == 200
        assert b"unsubscribed" in response.data.lower()
        mock_db.unsubscribe.assert_called_once_with("some-uuid")

    def test_unknown_id_renders_not_found_message(self, mocker):
        from routes import NewsRoutes
        mock_db = MagicMock()
        mock_db.unsubscribe.return_value = False
        mocker.patch.object(NewsRoutes, "db", mock_db)
        client = _client()
        response = client.get("/unsubscribe/nonexistent-uuid")
        assert response.status_code == 200
        assert b"couldn" in response.data.lower()
