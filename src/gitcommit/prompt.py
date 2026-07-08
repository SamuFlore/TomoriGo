SYSTEM_PROMPT = """你是一个专业的 commit message 生成助手。
根据用户提供的 git diff，生成一行简洁准确的 commit message。

规则：
- 使用 Conventional Commits 格式：type(scope): description
- type 从以下选择：feat, fix, refactor, docs, style, test, chore, perf, ci
- scope 根据改动的文件/模块自动推断
- 描述部分用{language}写
- 描述不超过 {max_length} 字符，简洁有力
- 如果 diff 很大，聚焦最核心的变更
- 只返回 commit message 本身，一行，不要任何解释"""


def build_prompt(diff: str, file_summary: str, language: str = "zh", max_length: int = 72) -> tuple[str, str]:
    """Build system and user prompts for the AI.

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    lang_name = {"zh": "中文", "en": "English"}.get(language, language)
    system = SYSTEM_PROMPT.format(language=lang_name, max_length=max_length)

    # Truncate diff if too long (> 8000 chars)
    if len(diff) > 8000:
        diff = diff[:8000] + "\n... (diff truncated)"

    user = f"""以下文件发生了变更：
{file_summary}

git diff:
{diff}

请生成 commit message:"""

    return system, user
