SYSTEM_PROMPT = """你是一个专业的 commit message 生成助手。
根据用户提供的 git diff，生成一行简洁准确的 commit message。

规则：
- 使用以下格式生成 commit message：{format_template}
- 描述部分用{language}写
- 描述不超过 {max_length} 字符，简洁有力
- 如果 diff 很大，聚焦最核心的变更
- 只返回 commit message 本身，一行，不要任何解释"""


def build_prompt(
    diff: str,
    file_summary: str,
    language: str = "zh",
    max_length: int = 72,
    template: str = "{{type}}({{scope}}): {{message}}",
) -> tuple[str, str]:
    """Build system and user prompts for the AI.

    Args:
        diff: The staged git diff text.
        file_summary: Git diff --stat output.
        language: Language for the description ('zh' or 'en').
        max_length: Max characters for the description.
        template: Format template for the commit message.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    lang_name = {"zh": "中文", "en": "English"}.get(language, language)
    # Render template to human-readable format instruction
    format_instruction = template.replace("{{type}}", "type").replace("{{scope}}", "scope").replace("{{message}}", "description").replace("{{emoji}}", "emoji")
    system = SYSTEM_PROMPT.format(
        format_template=format_instruction,
        language=lang_name,
        max_length=max_length,
    )

    # Truncate diff if too long (> 8000 chars)
    if len(diff) > 8000:
        diff = diff[:8000] + "\n... (diff truncated)"

    user = f"""以下文件发生了变更：
{file_summary}

git diff:
{diff}

请生成 commit message:"""

    return system, user
