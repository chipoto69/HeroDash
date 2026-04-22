from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web_dashboard import app, build_alerts, env_int, env_path, make_probe, parse_topic_ownership, sanitize_url


def test_parse_topic_ownership_extracts_thread_ids():
    markdown = """### Topic ownership map\n- `ops-dispatch`: triage inbox\n- `atlas-lane` (thread 13): operator commands\n- `maya-lane` (thread 14): result lane\n### Next section\n"""
    topics = parse_topic_ownership(markdown)
    assert topics[0]["name"] == "ops-dispatch"
    assert topics[0]["thread_id"] is None
    assert topics[1]["thread_id"] == "13"
    assert topics[2]["name"] == "maya-lane"


def test_sanitize_url_drops_query_and_fragment():
    assert sanitize_url("https://example.com/mcp?token=secret#frag") == "https://example.com/mcp"


def test_sanitize_url_removes_userinfo():
    assert sanitize_url("https://user:pass@example.com:443/mcp?token=secret") == "https://example.com:443/mcp"


def test_build_alerts_escalates_worst_status():
    cards = {
        "hermes": make_probe(name="hermes", status="healthy", source="x", details={}),
        "telegram": make_probe(name="telegram", status="degraded", source="x", details={}, last_error="gateway missing"),
        "gbrain": make_probe(name="gbrain", status="down", source="x", details={}, last_error="endpoint unreachable"),
        "workflows": make_probe(name="workflows", status="healthy", source="x", details={}),
    }
    alerts = build_alerts(cards)
    assert alerts["status"] == "down"
    assert alerts["details"]["count"] == 2
    assert any(item["card"] == "gbrain" for item in alerts["details"]["items"])


def test_make_probe_marks_stale_when_evidence_too_old():
    stale = make_probe(
        name="gbrain",
        status="healthy",
        source="x",
        details={"evidence_timestamp": "2026-01-01T00:00:00Z"},
    )
    assert stale["status"] == "stale"
    assert stale["last_error"]


def test_env_path_expands_tilde():
    expanded = env_path("DOES_NOT_EXIST_TEST", "~/tmp-hero-test")
    assert str(expanded).startswith(str(Path.home()))


def test_env_int_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("HERO_TEST_PORT", "nope")
    assert env_int("HERO_TEST_PORT", 1234) == 1234


def test_healthz_reports_dashboard_alive_even_if_dependencies_degraded(monkeypatch):
    client = TestClient(app)

    fake_snapshot = {
        "overview": {"timestamp": "2026-04-22T00:00:00Z"},
        "cards": {
            "hermes": {"status": "healthy"},
            "telegram": {"status": "degraded"},
            "gbrain": {"status": "healthy"},
            "workflows": {"status": "healthy"},
            "alerts": {"status": "degraded"},
        },
    }

    from web_dashboard import runtime
    monkeypatch.setattr(runtime, "snapshot", lambda: fake_snapshot)

    health = client.get("/api/healthz")
    ready = client.get("/api/readiness")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert ready.status_code == 503
    assert ready.json()["status"] == "degraded"
