def _client():
    from app import app
    app.config["TESTING"] = True
    return app.test_client()


class TestLandingRoute:
    def test_renders_landing_page(self, mocker):
        client = _client()
        response = client.get("/")
        assert response.status_code == 200
        assert b"Autonomous Threat Intelligence" in response.data

    def test_get_started_links_to_dashboard(self, mocker):
        client = _client()
        response = client.get("/")
        assert b'href="/dashboard" class="btn-primary"' in response.data

    def test_nav_links_point_to_real_pages(self, mocker):
        client = _client()
        response = client.get("/")
        body = response.get_data(as_text=True)
        assert '<a href="/dashboard">Home</a>' in body
        assert '<a href="/sources">Sources</a>' in body
        assert '<a href="/chat">Chat</a>' in body
        assert '<a href="/subscribe">Subscribe</a>' in body
