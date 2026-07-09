SYSTEM_PROMPT = """你是一个专业的 commit message 生成助手。
根据用户提供的 git diff，生成一行简洁准确的 commit message。

规则：
- 使用以下格式生成 commit message：{format_template}
- 描述部分用{language}写
- 描述不超过 {max_length} 字符，简洁有力
- 如果 diff 很大，聚焦最核心的变更
- 只返回 commit message 本身，一行，不要任何解释"""


NONSENSE_SYSTEM_PROMPT = """你是一个有幽默感的程序员，专门生成搞笑风格的 git commit message。
根据用户提供的 git diff，生成一行看起来像 Conventional Commits 格式但内容非常幽默的消息。

规则：
- 严格遵循格式：type(scope): description
- type 使用这些有趣的词之一：chaos, meow, cope, vibe, yeet, noodle, galaxybrain, oops
- scope 根据改动的文件来编一个夸张好笑的描述
- description 用{language}写，要玩编程梗和程序员笑话
- description 不超过 {max_length} 字符
- 语言要生动有趣但不能冒犯
- 只返回 commit message 本身，一行，不要任何解释"""


def build_prompt(
    diff: str,
    file_summary: str,
    language: str = "zh",
    max_length: int = 72,
    template: str = "{{type}}({{scope}}): {{message}}",
) -> tuple[str, str]:
    """Build system and user prompts for the AI."""

    lang_name = {"zh": "中文", "en": "English"}.get(language, language)
    format_instruction = template.replace("{{type}}", "type").replace("{{scope}}", "scope").replace("{{message}}", "description").replace("{{emoji}}", "emoji")
    system = SYSTEM_PROMPT.format(
        format_template=format_instruction,
        language=lang_name,
        max_length=max_length,
    )

    if len(diff) > 8000:
        diff = diff[:8000] + "\n... (diff truncated)"

    user = f"""以下文件发生了变更：
{file_summary}

git diff:
{diff}

请生成 commit message:"""

    return system, user


def build_nonsense_prompt(
    diff: str,
    file_summary: str,
    language: str = "zh",
    max_length: int = 72,
) -> tuple[str, str]:
    """Build prompts for a nonsense/humorous commit message."""

    lang_name = {"zh": "中文", "en": "English"}.get(language, language)
    system = NONSENSE_SYSTEM_PROMPT.format(language=lang_name, max_length=max_length)

    if len(diff) > 8000:
        diff = diff[:8000] + "\n... (diff truncated)"

    user = f"""以下文件发生了变更：
{file_summary}

git diff:
{diff}

来，给我整一个最离谱的 commit message:"""

    return system, user
