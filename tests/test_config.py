import tempfile
import os
from pathlib import Path
import pytest
from gitcommit.config import load_config, DEFAULT_CONFIG


def test_default_config_has_required_fields():
    """Default config must have provider and format sections."""
    assert "provider" in DEFAULT_CONFIG
    assert "format" in DEFAULT_CONFIG
    assert "endpoint" in DEFAULT_CONFIG["provider"]
    assert "model" in DEFAULT_CONFIG["provider"]
    assert "api_key" in DEFAULT_CONFIG["provider"]


def test_loads_global_config(tmp_path, monkeypatch):
    """Global config overrides defaults."""
    config_path = tmp_path / ".gitcommit.toml"
    config_path.write_text("""[provider]
api_key = "sk-global-test"
model = "gpt-4"
""")
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", config_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "nonexistent.toml")

    config = load_config()

    assert config["provider"]["api_key"] == "sk-global-test"
    assert config["provider"]["model"] == "gpt-4"
    # Default fields should still be present
    assert config["provider"]["endpoint"] == DEFAULT_CONFIG["provider"]["endpoint"]


def test_project_overrides_global(tmp_path, monkeypatch):
    """Project config overrides global config."""
    global_path = tmp_path / "global.toml"
    global_path.write_text("""[provider]
api_key = "sk-global"
model = "gpt-4"
""")
    project_path = tmp_path / "project.toml"
    project_path.write_text("""[provider]
api_key = "sk-project"
""")
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", global_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", project_path)

    config = load_config()

    assert config["provider"]["api_key"] == "sk-project"  # overridden
    assert config["provider"]["model"] == "gpt-4"  # inherited from global


def test_cli_overrides_all(tmp_path, monkeypatch):
    """CLI args override all config layers."""
    global_path = tmp_path / "global.toml"
    global_path.write_text('[provider]\napi_key = "sk-global"\nmodel = "gpt-4"\n')
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", global_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "nonexistent.toml")

    config = load_config(cli_overrides={
        "provider": {"api_key": "sk-cli"},
        "format": {"language": "en"},
    })

    assert config["provider"]["api_key"] == "sk-cli"
    assert config["provider"]["model"] == "gpt-4"
    assert config["format"]["language"] == "en"


def test_missing_config_files_no_error(tmp_path, monkeypatch):
    """Missing config files should not raise errors."""
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", tmp_path / "noexist.toml")
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "noexist2.toml")

    config = load_config()
    assert config["provider"]["endpoint"] == DEFAULT_CONFIG["provider"]["endpoint"]


def test_toml_syntax_error(tmp_path, monkeypatch):
    """Malformed TOML should raise a readable error."""
    bad_path = tmp_path / "bad.toml"
    bad_path.write_text("this is not valid toml {{{")
    monkeypatch.setattr("gitcommit.config.GLOBAL_CONFIG_PATH", bad_path)
    monkeypatch.setattr("gitcommit.config.PROJECT_CONFIG_PATH", tmp_path / "nonexistent.toml")

    with pytest.raises(SystemExit) as exc:
        load_config()
    assert exc.value.code == 1
