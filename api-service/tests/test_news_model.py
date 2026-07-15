from unittest.mock import MagicMock


def make_conn_mock():
    """Build a mock get_connection() context manager returning a mock cursor."""
    mock_cur = MagicMock()
    mock_cur_cm = MagicMock()
    mock_cur_cm.__enter__.return_value = mock_cur
    mock_cur_cm.__exit__.return_value = False

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur_cm

    mock_conn_cm = MagicMock()
    mock_conn_cm.__enter__.return_value = mock_conn
    mock_conn_cm.__exit__.return_value = False

    return mock_conn_cm, mock_cur


class TestCybernewsDB:
    def test_hybrid_query_used_when_query_vector_provided(self, mocker):
        from models import NewsModel

        conn_cm, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"headlines": "t"}]
        mocker.patch.object(NewsModel, "get_connection", return_value=conn_cm)
        mocker.patch.object(NewsModel, "register_vector", MagicMock())

        db = NewsModel.CybernewsDB()
        vector = [0.1] * 384
        result = db.get_news_collections(is_keyword=True, keyword="ransomware", query_vector=vector, alpha=0.3, limit=10)

        assert result == [{"headlines": "t"}]
        sql, params = mock_cur.execute.call_args[0]
        assert "embedding <=>" in sql
        assert params == {"kw": "ransomware", "alpha": 0.3, "query_vector": vector, "limit": 10}

    def test_ilike_query_used_when_no_query_vector(self, mocker):
        from models import NewsModel

        conn_cm, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"headlines": "t"}]
        mocker.patch.object(NewsModel, "get_connection", return_value=conn_cm)
        mocker.patch.object(NewsModel, "register_vector", MagicMock())

        db = NewsModel.CybernewsDB()
        result = db.get_news_collections(is_keyword=True, keyword="ransomware", limit=10)

        assert result == [{"headlines": "t"}]
        sql, params = mock_cur.execute.call_args[0]
        assert "ILIKE" in sql
        assert params == {"kw": "%ransomware%", "limit": 10}

    def test_default_query_when_no_keyword(self, mocker):
        from models import NewsModel

        conn_cm, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = []
        mocker.patch.object(NewsModel, "get_connection", return_value=conn_cm)
        mocker.patch.object(NewsModel, "register_vector", MagicMock())

        db = NewsModel.CybernewsDB()
        result = db.get_news_collections(limit=10)

        assert result == []
        sql, params = mock_cur.execute.call_args[0]
        assert "WHERE" not in sql
        assert params == {"limit": 10}

    def test_returns_empty_list_on_db_error(self, mocker):
        from models import NewsModel

        mocker.patch.object(NewsModel, "get_connection", side_effect=Exception("connection refused"))

        db = NewsModel.CybernewsDB()
        result = db.get_news_collections(is_keyword=True, keyword="ransomware")

        assert result == []

    def test_register_vector_called_when_available(self, mocker):
        from models import NewsModel

        conn_cm, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = []
        mock_register = MagicMock()
        mocker.patch.object(NewsModel, "get_connection", return_value=conn_cm)
        mocker.patch.object(NewsModel, "register_vector", mock_register)

        db = NewsModel.CybernewsDB()
        db.get_news_collections(limit=10)

        mock_register.assert_called_once()
