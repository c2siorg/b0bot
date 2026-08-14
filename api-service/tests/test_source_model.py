from unittest.mock import MagicMock
from models.SourceModel import SourceDB


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
    return mock_conn_cm, mock_conn, mock_cur


class TestGetAllSources:
    def test_cache_miss_queries_db_and_populates_cache(self, mocker):
        from models import SourceModel
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mocker.patch.object(SourceModel, "redis_client", mock_redis)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.get_all_sources()
        assert result == [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]
        mock_redis.setex.assert_called_once()
        cache_key = mock_redis.setex.call_args[0][0]
        assert cache_key == SourceModel.SOURCES_CACHE_KEY

    def test_cache_hit_skips_db_entirely(self, mocker):
        from models import SourceModel
        import json
        mock_redis = MagicMock()
        cached_sources = [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]
        mock_redis.get.return_value = json.dumps(cached_sources)
        mocker.patch.object(SourceModel, "redis_client", mock_redis)
        db_connection_spy = mocker.patch.object(SourceModel, "get_connection")
        db = SourceDB()
        result = db.get_all_sources()
        assert result == cached_sources
        db_connection_spy.assert_not_called()

    def test_no_redis_falls_back_to_db_directly(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "redis_client", None)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.get_all_sources()
        assert result == [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]

    def test_returns_empty_list_on_db_error(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "redis_client", None)
        mocker.patch.object(SourceModel, "get_connection", side_effect=Exception("db down"))
        db = SourceDB()
        result = db.get_all_sources()
        assert result == []

    def test_redis_error_on_read_falls_back_to_db(self, mocker):
        from models import SourceModel
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("redis down")
        mocker.patch.object(SourceModel, "redis_client", mock_redis)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.get_all_sources()
        assert result == [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]


class TestCreateSource:
    def test_returns_true_on_successful_insert(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "redis_client", None)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = {"id": "new-uuid"}
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.create_source(name="Test Feed", url="https://x.com/feed")
        assert result is True
        sql, params = mock_cur.execute.call_args[0]
        assert "INSERT INTO sources" in sql
        assert "ON CONFLICT (url) DO NOTHING" in sql
        assert params == {"name": "Test Feed", "url": "https://x.com/feed"}
        mock_conn.commit.assert_called_once()

    def test_successful_insert_invalidates_cache(self, mocker):
        from models import SourceModel
        mock_redis = MagicMock()
        mocker.patch.object(SourceModel, "redis_client", mock_redis)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = {"id": "new-uuid"}
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        db.create_source(name="Test Feed", url="https://x.com/feed")
        mock_redis.delete.assert_called_once_with(SourceModel.SOURCES_CACHE_KEY)

    def test_returns_false_on_duplicate_url(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "redis_client", None)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = None
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.create_source(name="Test Feed", url="https://x.com/feed")
        assert result is False

    def test_duplicate_url_does_not_invalidate_cache(self, mocker):
        from models import SourceModel
        mock_redis = MagicMock()
        mocker.patch.object(SourceModel, "redis_client", mock_redis)
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = None
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        db.create_source(name="Test Feed", url="https://x.com/feed")
        mock_redis.delete.assert_not_called()

    def test_returns_none_on_db_error(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "redis_client", None)
        mocker.patch.object(SourceModel, "get_connection", side_effect=Exception("db down"))
        db = SourceDB()
        result = db.create_source(name="Test Feed", url="https://x.com/feed")
        assert result is None
