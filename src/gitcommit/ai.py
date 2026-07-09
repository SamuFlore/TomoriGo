"""AI module: OpenAI-compatible provider with error handling."""

from openai import OpenAI, APIConnectionError, APIStatusError


class AIError(Exception):
    """Raised when an AI provider call fails."""


def generate_message(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    endpoint: str,
    model: str,
    timeout: float = 15.0,
    temperature: float = 0.3,
) -> str:
    """Call the OpenAI-compatible API to generate a commit message.

    Args:
        system_prompt: The system prompt to send.
        user_prompt: The user prompt to send.
        api_key: API key for the provider.
        endpoint: Base URL of the API endpoint.
        model: Model name to use.
        timeout: Request timeout in seconds.
        temperature: Creativity level (0.0-2.0). Default 0.3 for consistency.

    Returns:
        The generated commit message string (stripped).

    Raises:
        AIError: On missing api_key, network errors, HTTP errors,
                 or empty model response.
    """
    if not api_key:
        raise AIError("未配置 API key，请在配置文件中设置 provider.api_key")

    client = OpenAI(api_key=api_key, base_url=endpoint, timeout=timeout)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=150,
        )
    except APIConnectionError as e:
        raise AIError(f"网络连接失败：{e}") from e
    except APIStatusError as e:
        raise AIError(f"API 请求失败 (HTTP {e.status_code})：{e.message}") from e

    content = response.choices[0].message.content
    if content is None or not content.strip():
        raise AIError("AI 返回了空内容，请重试")

    return content.strip()
