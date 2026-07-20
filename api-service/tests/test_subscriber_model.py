from unittest.mock import MagicMock

from models.SubscriberModel import SubscriberDB


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


class TestSubscriberDB:
    def test_creates_subscriber_and_interests(self, mocker):
        from models import SubscriberModel
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = {"id": "subscriber-uuid-1"}
        mocker.patch.object(SubscriberModel, "get_connection", return_value=conn_cm)

        db = SubscriberDB()
        result = db.create_subscriber(email="test@example.com", frequency="daily", interests=["ransomware", "malware"])

        assert result is True
        first_sql, first_params = mock_cur.execute.call_args_list[0][0]
        assert "INSERT INTO subscribers" in first_sql
        assert "ON CONFLICT (email) DO UPDATE" in first_sql
        assert first_params == {"email": "test@example.com", "frequency": "daily"}

        interest_calls = mock_cur.execute.call_args_list[1:]
        assert len(interest_calls) == 2
        tags_inserted = {call[0][1]["tag"] for call in interest_calls}
        assert tags_inserted == {"ransomware", "malware"}
        mock_conn.commit.assert_called_once()

    def test_no_interests_still_creates_subscriber(self, mocker):
        from models import SubscriberModel
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = {"id": "subscriber-uuid-2"}
        mocker.patch.object(SubscriberModel, "get_connection", return_value=conn_cm)

        db = SubscriberDB()
        result = db.create_subscriber(email="test2@example.com")

        assert result is True
        assert mock_cur.execute.call_count == 1
        mock_conn.commit.assert_called_once()

    def test_existing_interests_not_deleted_on_conflict(self, mocker):
        """Merge semantics: re-subscribing shouldn't wipe out previously
        stored interests that aren't mentioned again. ON CONFLICT DO NOTHING
        only guards against duplicate rows for the same tag, it's not a
        replace. If this test breaks, that behavior changed, worth a second
        look before assuming it's an improvement, see the accumulate vs
        replace tradeoff in the PR."""
        from models import SubscriberModel
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchone.return_value = {"id": "subscriber-uuid-3"}
        mocker.patch.object(SubscriberModel, "get_connection", return_value=conn_cm)

        db = SubscriberDB()
        db.create_subscriber(email="test3@example.com", interests=["cve"])

        all_sql = [call[0][0] for call in mock_cur.execute.call_args_list]
        assert not any("DELETE" in sql for sql in all_sql)
        assert any("ON CONFLICT DO NOTHING" in sql for sql in all_sql)

    def test_returns_false_on_db_error(self, mocker):
        from models import SubscriberModel
        mocker.patch.object(SubscriberModel, "get_connection", side_effect=Exception("connection refused"))

        db = SubscriberDB()
        result = db.create_subscriber(email="test4@example.com", interests=["malware"])

        assert result is False
