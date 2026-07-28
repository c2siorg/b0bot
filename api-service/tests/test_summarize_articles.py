from unittest.mock import MagicMock


def make_conn_mock():
    """Build a mock get_connection() context manager returning a mock cursor,
    same helper shape as tests/test_subscriber_model.py."""
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


class TestRunOnce:
    def test_no_pending_articles_logs_and_returns(self, mocker):
        from jobs import summarize_articles
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = []
        mocker.patch.object(summarize_articles, "get_connection", return_value=conn_cm)
        gen_spy = mocker.patch.object(summarize_articles, "generate_summary")

        summarize_articles.run_once()

        gen_spy.assert_not_called()

    def test_successful_summary_saved_and_committed(self, mocker):
        from jobs import summarize_articles
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"id": "article-1", "content": "some article text"}]
        mocker.patch.object(summarize_articles, "get_connection", return_value=conn_cm)
        mocker.patch.object(summarize_articles, "generate_summary", return_value="a clean summary")

        summarize_articles.run_once()

        update_calls = [c for c in mock_cur.execute.call_args_list if "UPDATE articles" in c[0][0]]
        assert len(update_calls) == 1
        assert update_calls[0][0][1] == {"summary": "a clean summary", "article_id": "article-1"}
        mock_conn.commit.assert_called_once()

    def test_no_summary_produced_skips_save_without_raising(self, mocker):
        from jobs import summarize_articles
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [{"id": "article-1", "content": "some article text"}]
        mocker.patch.object(summarize_articles, "get_connection", return_value=conn_cm)
        mocker.patch.object(summarize_articles, "generate_summary", return_value=None)

        summarize_articles.run_once()

        update_calls = [c for c in mock_cur.execute.call_args_list if "UPDATE articles" in c[0][0]]
        assert len(update_calls) == 0
        mock_conn.commit.assert_not_called()

    def test_one_article_failing_does_not_stop_the_batch(self, mocker):
        from jobs import summarize_articles
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = [
            {"id": "article-1", "content": "bad article"},
            {"id": "article-2", "content": "good article"},
        ]
        mocker.patch.object(summarize_articles, "get_connection", return_value=conn_cm)
        mocker.patch.object(
            summarize_articles,
            "generate_summary",
            side_effect=[Exception("boom"), "a clean summary"],
        )

        summarize_articles.run_once()

        update_calls = [c for c in mock_cur.execute.call_args_list if "UPDATE articles" in c[0][0]]
        assert len(update_calls) == 1
        assert update_calls[0][0][1]["article_id"] == "article-2"
        mock_conn.rollback.assert_called_once()

    def test_batch_size_env_var_passed_as_query_limit(self, mocker):
        from jobs import summarize_articles
        conn_cm, mock_conn, mock_cur = make_conn_mock()
        mock_cur.fetchall.return_value = []
        mocker.patch.object(summarize_articles, "get_connection", return_value=conn_cm)
        mocker.patch.object(summarize_articles, "BATCH_SIZE", 5)
        mocker.patch.object(summarize_articles, "generate_summary")

        summarize_articles.run_once()

        select_call = mock_cur.execute.call_args_list[0]
        assert select_call[0][1] == {"limit": 5}
