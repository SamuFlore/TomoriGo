"""Tests for the AI module: OpenAI-compatible provider with error handling."""

import pytest
from unittest.mock import patch, MagicMock


class TestGenerateMessage:
    """Tests for generate_message() — the core AI call."""

    @pytest.fixture
    def sample_system_prompt(self):
        return "You are a commit message generator."

    @pytest.fixture
    def sample_user_prompt(self):
        return "Generate a commit message for:\n--- a/foo.py\n+++ b/foo.py\n+print('hello')"

    @pytest.fixture
    def sample_api_key(self):
        return "sk-test-key"

    @pytest.fixture
    def sample_endpoint(self):
        return "https://api.openai.com/v1"

    @pytest.fixture
    def sample_model(self):
        return "gpt-4o-mini"

    # --- Test 1: correct params passed to OpenAI ---
    def test_passes_correct_params_to_openai(
        self, sample_system_prompt, sample_user_prompt,
        sample_api_key, sample_endpoint, sample_model,
    ):
        """Verify api_key, base_url, timeout, model & messages are forwarded correctly."""
        from gitcommit.ai import generate_message

        mock_client = MagicMock()
        mock_create = MagicMock()
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="feat(foo): add print"))]
        )
        mock_client.chat.completions.create = mock_create

        with patch("gitcommit.ai.OpenAI", return_value=mock_client) as mock_openai_cls:
            generate_message(
                system_prompt=sample_system_prompt,
                user_prompt=sample_user_prompt,
                api_key=sample_api_key,
                endpoint=sample_endpoint,
                model=sample_model,
            )

            # Client was constructed with the right args (including timeout)
            mock_openai_cls.assert_called_once_with(
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1",
                timeout=15.0,
            )

            # chat.completions.create was called with right model, temp, max_tokens
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4o-mini"
            assert call_kwargs["temperature"] == 0.3
            assert call_kwargs["max_tokens"] == 150

            # messages is a list of two dicts (system + user)
            messages = call_kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == sample_system_prompt
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == sample_user_prompt

    # --- Test 2: stripped return ---
    def test_returns_stripped_content(
        self, sample_system_prompt, sample_user_prompt,
        sample_api_key, sample_endpoint, sample_model,
    ):
        """The returned message content should be whitespace-stripped."""
        from gitcommit.ai import generate_message

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="  feat(foo): add print  \n"))]
        )

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            result = generate_message(
                system_prompt=sample_system_prompt,
                user_prompt=sample_user_prompt,
                api_key=sample_api_key,
                endpoint=sample_endpoint,
                model=sample_model,
            )

        assert result == "feat(foo): add print"
        assert result == result.strip()

    # --- Test 3: empty api_key raises ---
    def test_empty_api_key_raises_aierror(
        self, sample_system_prompt, sample_user_prompt,
        sample_endpoint, sample_model,
    ):
        """Missing api_key should raise AIError immediately."""
        from gitcommit.ai import generate_message, AIError

        with pytest.raises(AIError):
            generate_message(
                system_prompt=sample_system_prompt,
                user_prompt=sample_user_prompt,
                api_key="",
                endpoint=sample_endpoint,
                model=sample_model,
            )

    # --- Test 4: network error raises ---
    def test_network_error_raises_aierror(
        self, sample_system_prompt, sample_user_prompt,
        sample_api_key, sample_endpoint, sample_model,
    ):
        """Connection / network errors should be caught and re-raised as AIError."""
        from gitcommit.ai import generate_message, AIError
        import openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APIConnectionError(
            request=None
        )

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            with pytest.raises(AIError) as exc_info:
                generate_message(
                    system_prompt=sample_system_prompt,
                    user_prompt=sample_user_prompt,
                    api_key=sample_api_key,
                    endpoint=sample_endpoint,
                    model=sample_model,
                )

            assert "连接" in str(exc_info.value) or "网络" in str(exc_info.value)

    # --- Test 5: HTTP error shows status ---
    def test_http_error_shows_status_code(
        self, sample_system_prompt, sample_user_prompt,
        sample_api_key, sample_endpoint, sample_model,
    ):
        """HTTP errors should include the HTTP status code in the AIError message."""
        from gitcommit.ai import generate_message, AIError
        import openai

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APIStatusError(
            "Rate limit", response=mock_response, body=None
        )

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            with pytest.raises(AIError) as exc_info:
                generate_message(
                    system_prompt=sample_system_prompt,
                    user_prompt=sample_user_prompt,
                    api_key=sample_api_key,
                    endpoint=sample_endpoint,
                    model=sample_model,
                )

            assert "429" in str(exc_info.value)

    # --- Test 6: empty response raises ---
    def test_empty_response_raises_aierror(
        self, sample_system_prompt, sample_user_prompt,
        sample_api_key, sample_endpoint, sample_model,
    ):
        """An empty / None content from the model should raise AIError."""
        from gitcommit.ai import generate_message, AIError

        # Case A: content is None
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=None))]
        )

        with patch("gitcommit.ai.OpenAI", return_value=mock_client):
            with pytest.raises(AIError):
                generate_message(
                    system_prompt=sample_system_prompt,
                    user_prompt=sample_user_prompt,
                    api_key=sample_api_key,
                    endpoint=sample_endpoint,
                    model=sample_model,
                )

        # Case B: content is empty string after strip
        mock_client2 = MagicMock()
        mock_client2.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="   "))]
        )

        with patch("gitcommit.ai.OpenAI", return_value=mock_client2):
            with pytest.raises(AIError):
                generate_message(
                    system_prompt=sample_system_prompt,
                    user_prompt=sample_user_prompt,
                    api_key=sample_api_key,
                    endpoint=sample_endpoint,
                    model=sample_model,
                )
