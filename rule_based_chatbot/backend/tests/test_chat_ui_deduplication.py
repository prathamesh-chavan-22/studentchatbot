import re
from pathlib import Path


def _read_static_file(name: str) -> str:
    static_dir = Path(__file__).resolve().parents[1] / "static"
    return (static_dir / name).read_text(encoding="utf-8")


def test_widget_suggestion_click_does_not_readd_same_user_text():
    source = _read_static_file("widget.js")
    assert "function isSameAsLastUserMessage" in source
    assert re.search(
        r"if\s*\(\s*!isSameAsLastUserMessage\(item\.question\)\s*\)\s*\{\s*addMessage\(item\.question,\s*'user-msg'\);",
        source,
        re.DOTALL,
    )


def test_basic_chat_suggestion_click_does_not_readd_same_user_text():
    source = _read_static_file("chat.js")
    assert "function isSameAsLastUserMessage" in source
    assert re.search(
        r"if\s*\(\s*!isSameAsLastUserMessage\(item\.question\)\s*\)\s*\{\s*addMessage\(item\.question,\s*\"user\"\);",
        source,
        re.DOTALL,
    )
