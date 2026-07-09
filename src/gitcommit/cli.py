# src/gitcommit/cli.py
import argparse
import json
import sys

import questionary

from gitcommit.config import load_config
from gitcommit.git import (
    has_staged_changes,
    get_staged_diff,
    get_staged_stats,
    commit,
    GitError,
)
from gitcommit.prompt import build_prompt, build_nonsense_prompt
from gitcommit.ai import generate_message, AIError
from gitcommit.tui import (
    Action,
    show_diff_summary,
    review_message,
    show_success,
    show_cancelled,
    show_error,
)

from pathlib import Path

def _get_version() -> str:
    """Get version from pyproject.toml"""
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # Python < 3.11
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TomoriGo，让 Tomori 帮你写 Commit Message！",
        prog="tmrgo",
    )
    parser.add_argument(
        "-p", "--provider",
        help="AI provider 名称（覆盖配置文件）",
    )
    parser.add_argument(
        "-m", "--model",
        help="模型名称（覆盖配置文件）",
    )
    parser.add_argument(
        "-f", "--format",
        help="自定义 message 格式模板",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="只生成和展示 message，不执行 git commit",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="显示当前生效的配置",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"TomoriGo {_get_version()}",
        help="显示版本信息",
    )
    parser.add_argument(
        "-l", "--language",
        choices = ["zh", "en"],
        help="Commit message 语言（覆盖配置文件）",
    )
    args = parser.parse_args()

    # Build CLI overrides from args
    cli_overrides: dict = {}
    provider_override = {}
    if args.provider:
        provider_override["name"] = args.provider
    if args.model:
        provider_override["model"] = args.model
    if provider_override:
        cli_overrides["provider"] = provider_override
    format_override = {}
    if args.format:
        format_override["template"] = args.format
    if args.language:
        format_override["language"] = args.language
    if format_override:
        cli_overrides["format"] = format_override

    # Load config
    try:
        config = load_config(cli_overrides if cli_overrides else None)
    except SystemExit:
        return  # config.load already printed error

    # --config flag: show config and exit
    if args.config:
        # Mask API key for safety
        safe_config = json.loads(json.dumps(config, ensure_ascii=False))
        key = safe_config.get("provider", {}).get("api_key", "")
        if key and len(key) > 8:
            safe_config["provider"]["api_key"] = key[:4] + "****" + key[-4:]
        print(json.dumps(safe_config, indent=2, ensure_ascii=False))
        return

    # Check for staged changes
    try:
        if not has_staged_changes():
            show_error("没有暂存的变更", "请先使用 git add 暂存要提交的文件。")
            sys.exit(1)
    except GitError as e:
        show_error("Git 错误", str(e))
        sys.exit(1)

    # Get diff and stats
    try:
        diff = get_staged_diff()
        stats = get_staged_stats()
    except GitError as e:
        show_error("Git 错误", str(e))
        sys.exit(1)

    # Show diff summary
    show_diff_summary(stats)

    # Build prompts
    provider_cfg = config["provider"]
    format_cfg = config["format"]

    def _make_prompts():
        return build_prompt(
            diff=diff,
            file_summary=stats,
            language=format_cfg.get("language", "zh"),
            max_length=format_cfg.get("max_length", 72),
            template=format_cfg.get("template", "{{type}}({{scope}}): {{message}}"),
        )

    def _make_nonsense_prompts():
        return build_nonsense_prompt(
            diff=diff,
            file_summary=stats,
            language=format_cfg.get("language", "zh"),
            max_length=format_cfg.get("max_length", 72),
        )

    system_prompt, user_prompt = _make_prompts()
    temperature = 0.3

    # Interactive loop: generate → review → commit or regenerate
    while True:
        try:
            message = generate_message(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                api_key=provider_cfg.get("api_key", ""),
                endpoint=provider_cfg.get("endpoint", "https://api.openai.com/v1"),
                model=provider_cfg.get("model", "gpt-4o-mini"),
                temperature=temperature,
            )
        except AIError as e:
            show_error("AI 调用失败", str(e))
            retry = questionary.confirm("是否重试？", default=True).ask()
            if retry:
                continue
            else:
                sys.exit(1)

        action, final_message = review_message(message)

        if action == Action.CANCEL:
            show_cancelled()
            return
        elif action == Action.REGENERATE:
            continue
        elif action == Action.NONSENSE:
            system_prompt, user_prompt = _make_nonsense_prompts()
            temperature = 1.2  # 更高温度 = 更有创意（搞笑需要随机性）
            continue
        elif action == Action.COMMIT:
            if args.dry_run:
                show_success(f"[DRY RUN] {final_message}")
                return
            try:
                commit(final_message)
                show_success(final_message)
                return
            except GitError as e:
                show_error("提交失败", str(e))
                sys.exit(1)


if __name__ == "__main__":
    main()
