from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "launch_web_dashboard.sh"


def _case_body(command: str) -> str:
    text = LAUNCHER.read_text()
    pattern = rf"\n\s*{re.escape(command)}\)\n(?P<body>.*?)(?=\n\s*[a-zA-Z_|-]+\)|\n\s*\*\))"
    match = re.search(pattern, text, flags=re.DOTALL)
    assert match, f"missing {command}) case in launcher"
    return match.group("body")


def test_launcher_start_returns_after_daemonizing_dashboard():
    body = _case_body("start")

    assert "start_web_dashboard" in body
    assert "wait" not in body, "start must return so status/logs/stop and smoke curls can run"


def test_launcher_foreground_keeps_process_attached_for_interactive_use():
    body = _case_body("foreground")

    assert "start_web_dashboard true" in body
    assert "wait" in body
    assert "Press Ctrl+C" in body


def test_launcher_only_prints_ctrl_c_hint_for_attached_runs():
    text = LAUNCHER.read_text()

    assert "local attached=" in text
    assert "if [[ \"$attached\" == \"true\" ]]" in text
    assert "start_web_dashboard true" in _case_body("foreground")
    assert "start_web_dashboard true" in _case_body("full")
    assert "start_web_dashboard true" not in _case_body("start")


def test_launcher_full_keeps_process_attached_after_starting_analytics():
    body = _case_body("full")

    assert "start_analytics" in body
    assert "start_web_dashboard true" in body
    assert "open_browser" in body
    assert "wait" in body
