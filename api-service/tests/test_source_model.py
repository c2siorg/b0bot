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
    def test_returns_rows_on_success(self, mocker):
        from models import SourceModel
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.get_all_sources()
        assert result == [{"id": "1", "name": "Test", "url": "https://x.com/feed", "status": "active"}]

    def test_returns_empty_list_on_db_error(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "get_connection", side_effect=Exception("db down"))
        db = SourceDB()
        result = db.get_all_sources()
        assert result == []


class TestCreateSource:
    def test_returns_true_on_successful_insert(self, mocker):
        from models import SourceModel
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

    def test_returns_false_on_duplicate_url(self, mocker):
        from models import SourceModel
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = None
        mocker.patch.object(SourceModel, "get_connection", return_value=conn_cm)
        db = SourceDB()
        result = db.create_source(name="Test Feed", url="https://x.com/feed")
        assert result is False

    def test_returns_none_on_db_error(self, mocker):
        from models import SourceModel
        mocker.patch.object(SourceModel, "get_connection", side_effect=Exception("db down"))
        db = SourceDB()
        result = db.create_source(name="Test Feed", url="https://x.com/feed")
        assert result is None
