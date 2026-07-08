import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # Python < 3.11

GLOBAL_CONFIG_PATH = Path.home() / ".gitcommit.toml"
PROJECT_CONFIG_PATH = Path.cwd() / ".gitcommit.toml"

DEFAULT_CONFIG: dict[str, Any] = {
    "provider": {
        "name": "openai",
        "api_key": "",
        "model": "gpt-4o-mini",
        "endpoint": "https://api.openai.com/v1",
    },
    "format": {
        "template": "{{type}}({{scope}}): {{message}}",
        "max_length": 72,
        "language": "zh",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override takes precedence."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_toml(path: Path) -> dict:
    """Load a TOML file. Returns empty dict if file doesn't exist."""
    if not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        print(f"错误：配置文件 {path} 语法错误 — {e}", file=sys.stderr)
        sys.exit(1)


def load_config(cli_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load and cascade config from defaults to global to project to CLI args.

    Args:
        cli_overrides: Dict of config sections to override, e.g.
            {"provider": {"api_key": "sk-xxx"}}

    Returns:
        Merged config dict.
    """
    config = DEFAULT_CONFIG.copy()
    config = _deep_merge(config, _load_toml(GLOBAL_CONFIG_PATH))
    config = _deep_merge(config, _load_toml(PROJECT_CONFIG_PATH))
    if cli_overrides:
        config = _deep_merge(config, cli_overrides)
    return config
