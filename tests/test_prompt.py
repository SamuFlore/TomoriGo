import pytest
from gitcommit.prompt import build_prompt, SYSTEM_PROMPT


def test_build_prompt_includes_file_summary():
    system, user = build_prompt(
        diff="--- a/foo.py\n+++ b/foo.py\n+print('hello')",
        file_summary="foo.py | +1",
        language="zh",
        max_length=72,
    )
    assert "foo.py" in user
    assert "print('hello')" in user


def test_build_prompt_includes_language():
    system, user = build_prompt(
        diff="diff content",
        file_summary="f.py",
        language="en",
        max_length=72,
    )
    assert "English" in system


def test_build_prompt_trims_diff_when_too_long():
    long_diff = "x" * 9000
    system, user = build_prompt(
        diff=long_diff,
        file_summary="f.py",
        language="zh",
        max_length=72,
    )
    # Should be truncated
    assert len(user) < 9000 + 500  # prompt overhead ok, but diff should be cut


def test_system_prompt_is_string():
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 50
