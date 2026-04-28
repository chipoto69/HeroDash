from io import BytesIO
from pathlib import Path
import sys
from urllib.error import HTTPError

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web_dashboard import (
    ACTION_REGISTRY,
    DashboardRuntime,
    app,
    build_alerts,
    build_labyrinth,
    env_int,
    env_path,
    execute_action,
    list_actions,
    make_probe,
    parse_topic_ownership,
    preview_lines,
    read_action_events,
    sanitize_url,
    summarize_factory_models,
    redact_process_line,
    redact_text,
)


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
            "droids": {"status": "healthy"},
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


def test_probe_hermes_requires_gateway_and_ports_for_healthy(monkeypatch):
    runtime = DashboardRuntime()
    monkeypatch.setattr("web_dashboard.run_pgrep", lambda pattern: ["123 hermes gateway run --replace"])

    def fake_port_open(port, host="127.0.0.1", timeout=0.35):
        return False

    monkeypatch.setattr("web_dashboard.port_open", fake_port_open)
    probe = runtime.probe_hermes()

    assert probe["status"] == "degraded"
    assert "webapi port" in probe["last_error"]
    assert "workspace port" in probe["last_error"]


def test_probe_gbrain_marks_http_500_as_degraded(monkeypatch):
    runtime = DashboardRuntime()
    monkeypatch.setattr("web_dashboard.try_load_yaml", lambda path: {"mcp_servers": {"gbrain": {"url": "https://example.com/mcp", "headers": {}}}})
    monkeypatch.setattr("web_dashboard.BRAIN_ROOT", Path.home())

    def fake_urlopen(request, timeout=4):
        raise HTTPError(request.full_url, 500, "boom", hdrs=None, fp=BytesIO(b"fail"))

    monkeypatch.setattr("web_dashboard.urlopen", fake_urlopen)
    probe = runtime.probe_gbrain()

    assert probe["status"] == "degraded"
    assert probe["details"]["http_status"] == 500
    assert "HTTP 500" in probe["last_error"]


def test_summarize_factory_models_filters_to_hermes_without_secrets():
    models = summarize_factory_models(
        {
            "customModels": [
                {
                    "id": "custom:Hermes-Codex-[Local]-0",
                    "displayName": "Hermes -> Codex [Local]",
                    "model": "factory-codex",
                    "baseUrl": "http://user:secret@127.0.0.1:8645/v1?token=secret",
                    "apiKey": "do-not-return",
                },
                {
                    "id": "custom:Other-0",
                    "displayName": "Other",
                    "model": "other",
                    "baseUrl": "https://example.com/v1",
                },
            ]
        }
    )

    assert len(models) == 1
    assert models[0]["id"] == "custom:Hermes-Codex-[Local]-0"
    assert models[0]["base_url"] == "http://127.0.0.1:8645/v1"
    assert "apiKey" not in models[0]


def test_redact_process_line_removes_arguments_and_env_values():
    redacted = redact_process_line("1234 /usr/bin/droid exec --api-key secret --url http://token@example.com")

    assert redacted == "1234 droid-exec+droid"
    assert "secret" not in redacted
    assert "example.com" not in redacted


def test_probe_droids_degraded_when_bridge_missing(monkeypatch, tmp_path):
    runtime = DashboardRuntime()
    droid_bin = tmp_path / "droid"
    droid_bin.write_text("#!/bin/sh\n")

    monkeypatch.setenv("HERO_DROID_BIN", str(droid_bin))
    monkeypatch.setattr("web_dashboard.FACTORY_SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr("web_dashboard.load_factory_settings", lambda path=None: {"customModels": []})
    monkeypatch.setattr("web_dashboard.run_command", lambda args, timeout=2.0: (0, "droid 0.105.1", ""))
    monkeypatch.setattr("web_dashboard.port_open", lambda port, host="127.0.0.1", timeout=0.35: False)
    monkeypatch.setattr("web_dashboard.run_pgrep", lambda pattern: [])

    probe = runtime.probe_droids()

    assert probe["status"] == "degraded"
    assert probe["details"]["droid_binary_exists"] is True
    assert "droid_processes" not in probe["details"]
    assert "factory_processes" not in probe["details"]
    assert "Hermes Factory model" in probe["last_error"]


def test_action_registry_is_public_and_allowlisted():
    actions = list_actions()
    ids = {action["id"] for action in actions}

    assert {"refresh_status", "compile_dashboard", "run_reboot_tests", "launcher_status", "tail_logs"}.issubset(ids)
    assert all("args" not in action for action in actions)
    assert ACTION_REGISTRY["compile_dashboard"]["args"] == ["python3", "-m", "py_compile", "web_dashboard.py", "config.py"]


def test_redact_text_scrubs_common_secret_shapes():
    raw = "token=supersecret Authorization: Bearer abcdefghijklmnop https://user:pass@example.com/path?api_key=hidden"
    redacted = redact_text(raw)

    assert "supersecret" not in redacted
    assert "abcdefghijklmnop" not in redacted
    assert "user:pass" not in redacted
    assert "hidden" not in redacted


def test_preview_lines_keeps_tail_and_redacts():
    preview = preview_lines("one\ntwo\npassword=secret\nthree", max_lines=2)

    assert "one" not in preview
    assert "secret" not in preview
    assert "password=[redacted]" in preview


def test_read_action_events_ignores_bad_lines(monkeypatch, tmp_path):
    import web_dashboard

    action_log = tmp_path / "actions.jsonl"
    action_log.write_text('not-json\n{"id": "ok", "status": "succeeded"}\n')
    monkeypatch.setattr(web_dashboard, "HERO_ACTION_LOG", action_log)

    assert read_action_events() == [{"id": "ok", "status": "succeeded"}]


def test_execute_action_records_redacted_command_output(monkeypatch, tmp_path):
    import subprocess
    import web_dashboard

    monkeypatch.setattr(web_dashboard, "HERO_HOME", tmp_path)
    monkeypatch.setattr(web_dashboard, "HERO_ACTION_LOG", tmp_path / "actions.jsonl")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="api_key=secret-token", stderr="")

    monkeypatch.setattr(web_dashboard.subprocess, "run", fake_run)

    event = execute_action("compile_dashboard")

    assert event["status"] == "succeeded"
    assert "secret-token" not in event["stdout_preview"]
    assert (tmp_path / "actions.jsonl").exists()


def test_api_actions_and_unknown_action(monkeypatch):
    import web_dashboard

    client = TestClient(app)
    monkeypatch.setattr(web_dashboard, "read_action_events", lambda limit=20: [])

    actions = client.get("/api/actions")
    missing = client.post("/api/actions/not-real")

    assert actions.status_code == 200
    assert any(action["id"] == "compile_dashboard" for action in actions.json()["actions"])
    assert missing.status_code == 404


def test_api_run_action_uses_allowlisted_executor(monkeypatch):
    import web_dashboard

    client = TestClient(app)
    monkeypatch.setattr(
        web_dashboard,
        "execute_action",
        lambda action_id: {
            "id": "action-test",
            "action_id": action_id,
            "label": "Compile Dashboard",
            "status": "succeeded",
            "exit_code": 0,
            "duration_ms": 4,
            "stdout_preview": "ok",
            "stderr_preview": "",
        },
    )

    response = client.post("/api/actions/compile_dashboard")

    assert response.status_code == 200
    assert response.json()["action_id"] == "compile_dashboard"


def test_build_labyrinth_includes_probe_crossings_and_failed_action(monkeypatch):
    import web_dashboard

    snapshot = {
        "overview": {"timestamp": "2026-04-28T00:00:00Z"},
        "card_order": ["hermes", "droids", "telegram", "gbrain", "workflows", "alerts"],
        "cards": {
            "hermes": make_probe(name="hermes", status="healthy", source="test", details={}),
            "droids": make_probe(name="droids", status="degraded", source="test", details={}, last_error="bridge missing"),
            "telegram": make_probe(name="telegram", status="healthy", source="test", details={}),
            "gbrain": make_probe(name="gbrain", status="healthy", source="test", details={}),
            "workflows": make_probe(name="workflows", status="healthy", source="test", details={}),
            "alerts": make_probe(name="alerts", status="degraded", source="test", details={"summary": "1 alert"}, last_error="bridge missing"),
        },
    }
    monkeypatch.setattr(
        web_dashboard,
        "read_action_events",
        lambda limit=25: [
            {
                "id": "action-1",
                "action_id": "compile_dashboard",
                "label": "Compile Dashboard",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 10,
                "started_at": "2026-04-28T00:00:01Z",
                "completed_at": "2026-04-28T00:00:02Z",
                "stderr_preview": "password=[redacted]",
                "stdout_preview": "",
                "command": ["python3"],
                "cwd": "/tmp",
            }
        ],
    )
    monkeypatch.setattr(web_dashboard, "discover_skill_inventory", lambda limit=60: [{"name": "taste", "namespace": "agents"}])
    monkeypatch.setattr(web_dashboard, "cron_gate_snapshot", lambda: [{"name": "cron.yaml", "status": "missing"}])

    payload = build_labyrinth(snapshot)

    assert payload["journeys"][0]["id"] == "journey-current-dashboard"
    assert any(crossing["id"] == "crossing-probe-droids" for crossing in payload["crossings"])
    assert any(guidepost["title"] == "Compile Dashboard failed" for guidepost in payload["guideposts"])
    assert "password=[redacted]" in str(payload)
