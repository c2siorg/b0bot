from unittest.mock import MagicMock


def _mock_response(content):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    return mock_response


class TestClassifyIntent:
    def test_no_token_returns_none_without_calling_client(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", None)
        result = chat_llm.classify_intent("hi")
        assert result is None

    def test_empty_input_returns_none(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        result = chat_llm.classify_intent("   ")
        assert result is None

    def test_valid_json_response_parsed(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response(
            '{"intent": "search", "keywords": ["ransomware"]}'
        )
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.classify_intent("show me ransomware news")
        assert result == {"intent": "search", "keywords": ["ransomware"]}

    def test_markdown_fenced_json_stripped(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response(
            '```json\n{"intent": "chitchat", "keywords": []}\n```'
        )
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.classify_intent("hi")
        assert result["intent"] == "chitchat"

    def test_invalid_intent_value_returns_none(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response(
            '{"intent": "made_up_intent", "keywords": []}'
        )
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.classify_intent("hi")
        assert result is None

    def test_malformed_json_returns_none_instead_of_raising(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response("not json at all")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.classify_intent("hi")
        assert result is None

    def test_exception_returns_none_instead_of_raising(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("cohere is down")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.classify_intent("hi")
        assert result is None

    def test_missing_optional_fields_default_safely(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response('{"intent": "chitchat"}')
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.classify_intent("hi")
        assert result == {"intent": "chitchat", "keywords": []}


class TestAnswerGrounded:
    def test_no_token_returns_none(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", None)
        result = chat_llm.answer_grounded({"title": "t"}, "what happened?")
        assert result is None

    def test_no_article_returns_none(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        result = chat_llm.answer_grounded(None, "what happened?")
        assert result is None

    def test_successful_answer_returned(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response("  the article describes a critical RCE  ")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.answer_grounded(
            {"title": "Critical RCE Found", "source_name": "Krebs", "summary": "a summary"},
            "what happened?",
        )
        assert result == "the article describes a critical RCE"

    def test_prefers_content_over_summary(self, mocker):
        """Regression test: grounding must use the article's real content
        when present, not the short LLM-generated summary."""
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response("answer")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        chat_llm.answer_grounded(
            {"title": "t", "source_name": "s", "content": "the real full article body", "summary": "a short summary"},
            "what happened?",
        )
        prompt = mock_client.chat.completions.create.call_args[1]["messages"][0]["content"]
        assert "the real full article body" in prompt
        assert "a short summary" not in prompt

    def test_falls_back_to_summary_when_content_missing(self, mocker):
        """If content hasn't been backfilled/ingested yet, fall back to
        summary rather than sending an empty string to the prompt."""
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response("answer")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        chat_llm.answer_grounded(
            {"title": "t", "source_name": "s", "summary": "a short summary"},
            "what happened?",
        )
        prompt = mock_client.chat.completions.create.call_args[1]["messages"][0]["content"]
        assert "a short summary" in prompt

    def test_content_truncated_to_max_input_chars(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_response("answer")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        long_content = "x" * (chat_llm.MAX_INPUT_CHARS + 500)
        chat_llm.answer_grounded(
            {"title": "t", "source_name": "s", "content": long_content},
            "what happened?",
        )
        prompt = mock_client.chat.completions.create.call_args[1]["messages"][0]["content"]
        assert "x" * chat_llm.MAX_INPUT_CHARS in prompt
        assert "x" * (chat_llm.MAX_INPUT_CHARS + 1) not in prompt

    def test_exception_returns_none_instead_of_raising(self, mocker):
        from services import chat_llm
        mocker.patch.object(chat_llm, "HF_TOKEN", "fake-token")
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("cohere is down")
        mocker.patch("huggingface_hub.InferenceClient", return_value=mock_client)
        result = chat_llm.answer_grounded({"title": "t"}, "what happened?")
        assert result is None

