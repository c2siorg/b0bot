from unittest.mock import MagicMock


class TestGenerateSummary:
    def test_empty_text_returns_none_without_calling_anything(self, mocker):
        from services import summarizer
        cohere_spy = mocker.patch.object(summarizer, "_summarize_with_cohere")
        local_spy = mocker.patch.object(summarizer, "_summarize_with_local")
        result = summarizer.generate_summary("")
        assert result is None
        cohere_spy.assert_not_called()
        local_spy.assert_not_called()

    def test_cohere_success_returned_directly(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "_summarize_with_cohere", return_value="a clean cohere summary")
        local_spy = mocker.patch.object(summarizer, "_summarize_with_local")
        result = summarizer.generate_summary("some article text")
        assert result == "a clean cohere summary"
        local_spy.assert_not_called()

    def test_cohere_failure_falls_back_to_local(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "_summarize_with_cohere", return_value=None)
        mocker.patch.object(summarizer, "_summarize_with_local", return_value="a local fallback summary")
        result = summarizer.generate_summary("some article text")
        assert result == "a local fallback summary"

    def test_both_fail_returns_none(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "_summarize_with_cohere", return_value=None)
        mocker.patch.object(summarizer, "_summarize_with_local", return_value=None)
        result = summarizer.generate_summary("some article text")
        assert result is None


class TestSummarizeWithCohere:
    def test_no_token_returns_none_without_calling_client(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "HF_TOKEN", None)
        client_cls = mocker.patch("huggingface_hub.InferenceClient")
        result = summarizer._summarize_with_cohere("some text")
        assert result is None
        client_cls.assert_not_called()

    def test_successful_response_stripped_and_returned(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "HF_TOKEN", "fake-token")
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "  a summary with padding  "
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = summarizer._summarize_with_cohere("some article text")
        assert result == "a summary with padding"

    def test_exception_returns_none_instead_of_raising(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("cohere is down")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = summarizer._summarize_with_cohere("some article text")
        assert result is None


class TestSummarizeWithLocal:
    def test_successful_generation_decoded_and_returned(self, mocker):
        from services import summarizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.decode.return_value = "  a local summary  "
        mock_model = MagicMock()
        mocker.patch.object(summarizer, "_get_local_summarizer", return_value=(mock_tokenizer, mock_model))
        result = summarizer._summarize_with_local("some article text")
        assert result == "a local summary"

    def test_exception_returns_none_instead_of_raising(self, mocker):
        from services import summarizer
        mocker.patch.object(summarizer, "_get_local_summarizer", side_effect=Exception("model load failed"))
        result = summarizer._summarize_with_local("some article text")
        assert result is None
