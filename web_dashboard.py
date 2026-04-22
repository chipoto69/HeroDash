#!/usr/bin/env python3
"""Hero reboot dashboard — honest five-card operator surface."""

from __future__ import annotations

import json
import logging
import re
import socket
import subprocess
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency fallback
    yaml = None

logger = logging.getLogger("hero_reboot_dashboard")
logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = ROOT / "web_templates"
HERO_HOME = Path.home() / ".hero_core"
HERO_CACHE = HERO_HOME / "cache"
HERMES_HOME = Path.home() / ".hermes"
WORKFLOWS_ROOT = Path("/Users/rudlord/ORGANIZED/ACTIVE_PROJECTS/ARSENAL/WORKFLOWS")
BRAIN_ROOT = Path("/Users/rudlord/brain")
WIKI_GROK_SYSTEM = Path("/Users/rudlord/wiki/queries/grok420system.md")
MAIN_HERMES_CONFIG = HERMES_HOME / "config.yaml"
PORT_WEBAPI = 8642
PORT_WORKSPACE = 3011
CARD_ORDER = ["hermes", "telegram", "gbrain", "workflows", "alerts"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def age_in_seconds(ts: str | None) -> int | None:
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, int((utc_now() - parsed.astimezone(timezone.utc)).total_seconds()))


def sanitize_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    host = parts.hostname or ""
    netloc = host
    if parts.port:
        netloc = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def try_load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    try:
        loaded = yaml.safe_load(path.read_text())
        return loaded if isinstance(loaded, dict) else {}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to parse YAML %s: %s", path, exc)
        return {}


def run_pgrep(pattern: str) -> list[str]:
    try:
        result = subprocess.run(
            ["pgrep", "-fal", pattern],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    noise_markers = ("hermes-snap", "hermes-cwd", "pgrep -fal")
    return [line for line in lines if not any(marker in line for marker in noise_markers)]


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def file_timestamp(path: Path | None) -> str | None:
    if not path or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def newest_timestamp(paths: list[Path]) -> str | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    newest = max(existing, key=lambda item: item.stat().st_mtime)
    return file_timestamp(newest)


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def git_branch(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    branch = result.stdout.strip()
    return branch or None


def git_recent_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "log", "-1", "--pretty=%h %s"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    commit = result.stdout.strip()
    return commit or None


def parse_topic_ownership(markdown: str) -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []
    in_topic_section = False
    for raw_line in markdown.splitlines():
        if raw_line.strip() == "### Topic ownership map":
            in_topic_section = True
            continue
        if in_topic_section and raw_line.startswith("### "):
            break
        if not in_topic_section or not raw_line.startswith("- `"):
            continue
        match = re.match(r"- `([^`]+)`(?: \(thread (\d+)\))?: (.*)", raw_line)
        if not match:
            continue
        name, thread_id, description = match.groups()
        topics.append(
            {
                "name": name,
                "thread_id": thread_id,
                "description": description,
            }
        )
    return topics


def profile_summary(profile_name: str) -> dict[str, Any]:
    config_path = HERMES_HOME / "profiles" / profile_name / "config.yaml"
    payload = try_load_yaml(config_path)
    return {
        "profile": profile_name,
        "enabled": config_path.exists(),
        "config_path": str(config_path),
        "home_channel": payload.get("TELEGRAM_HOME_CHANNEL"),
        "home_thread_id": payload.get("TELEGRAM_HOME_THREAD_ID"),
        "timestamp": file_timestamp(config_path),
    }


def make_probe(
    *,
    name: str,
    status: str,
    source: str,
    details: dict[str, Any],
    timestamp: str | None = None,
    last_error: str | None = None,
) -> dict[str, Any]:
    ts = timestamp or iso_now()
    return {
        "name": name,
        "status": status,
        "source": source,
        "timestamp": ts,
        "freshness_seconds": age_in_seconds(ts),
        "last_error": last_error,
        "details": details,
    }


def build_alerts(cards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    severity_rank = {"healthy": 0, "stale": 1, "degraded": 2, "down": 3}
    highest = "healthy"
    for key, card in cards.items():
        status = card.get("status", "down")
        if severity_rank.get(status, 3) > severity_rank[highest]:
            highest = status
        if status == "healthy":
            continue
        items.append(
            {
                "card": key,
                "status": status,
                "message": card.get("last_error") or f"{key} is {status}",
                "timestamp": card.get("timestamp"),
            }
        )
    details = {
        "count": len(items),
        "items": items,
        "summary": "All operator surfaces healthy" if not items else f"{len(items)} surfaces need attention",
    }
    return make_probe(
        name="alerts",
        status=highest,
        source="hero-aggregator",
        details=details,
        last_error=items[0]["message"] if items else None,
    )


class DashboardRuntime:
    def probe_hermes(self) -> dict[str, Any]:
        process_lines = run_pgrep("hermes")
        gateway_lines = [line for line in process_lines if "gateway run" in line]
        webapi_lines = [line for line in process_lines if "-m webapi" in line or "python -m webapi" in line]
        webapi_up = port_open(PORT_WEBAPI)
        workspace_up = port_open(PORT_WORKSPACE)
        important_profiles = [
            "focus-warden",
            "resource-ingest",
            "synthesizer",
            "observer-evolver",
            "tg-alpha",
            "tg-beta",
            "chaddin",
        ]
        available_profiles = [
            profile for profile in important_profiles if (HERMES_HOME / "profiles" / profile / "config.yaml").exists()
        ]

        if gateway_lines or webapi_up:
            status = "healthy"
            last_error = None
        elif process_lines or available_profiles:
            status = "degraded"
            last_error = "Hermes configs exist but gateway/webapi health is partial"
        else:
            status = "down"
            last_error = "No Hermes runtime or profile evidence found"

        details = {
            "gateway_processes": len(gateway_lines),
            "webapi_processes": len(webapi_lines),
            "webapi_port_up": webapi_up,
            "workspace_ui_port_up": workspace_up,
            "tracked_profiles": available_profiles,
            "sample_processes": process_lines[:6],
        }
        return make_probe(
            name="hermes",
            status=status,
            source="local-process+ports",
            details=details,
            last_error=last_error,
        )

    def probe_telegram(self) -> dict[str, Any]:
        profiles = [profile_summary(name) for name in ("tg-alpha", "tg-beta", "chaddin")]
        active_profiles = [item for item in profiles if item["enabled"]]
        markdown = WIKI_GROK_SYSTEM.read_text() if WIKI_GROK_SYSTEM.exists() else ""
        topics = parse_topic_ownership(markdown)
        gateway_running = bool([line for line in run_pgrep("hermes") if "gateway run" in line])

        if active_profiles and gateway_running:
            status = "healthy"
            last_error = None
        elif active_profiles:
            status = "degraded"
            last_error = "Telegram profiles exist but gateway process was not detected"
        else:
            status = "down"
            last_error = "No Telegram operator profiles found"

        timestamp = newest_timestamp(
            [
                HERMES_HOME / "profiles" / "tg-alpha" / "config.yaml",
                HERMES_HOME / "profiles" / "tg-beta" / "config.yaml",
                HERMES_HOME / "profiles" / "chaddin" / "config.yaml",
                WIKI_GROK_SYSTEM,
            ]
        )
        details = {
            "profiles": active_profiles,
            "topics": topics[:6],
            "gateway_running": gateway_running,
            "canon_file": str(WIKI_GROK_SYSTEM),
            "evidence_timestamp": timestamp,
        }
        return make_probe(
            name="telegram",
            status=status,
            source="profile-config+gateway-process+wiki-canon",
            details=details,
            last_error=last_error,
        )

    def probe_gbrain(self) -> dict[str, Any]:
        config = try_load_yaml(MAIN_HERMES_CONFIG)
        gbrain = config.get("mcp_servers", {}).get("gbrain", {})
        url = gbrain.get("url")
        headers = gbrain.get("headers", {}) if isinstance(gbrain.get("headers"), dict) else {}
        sanitized_url = sanitize_url(url)
        repo_exists = BRAIN_ROOT.exists()
        endpoint_reachable = False
        http_status: int | None = None
        last_error: str | None = None

        if url:
            request = Request(url, headers=headers or {}, method="GET")
            try:
                with urlopen(request, timeout=4) as response:  # nosec B310 - fixed config URL
                    endpoint_reachable = True
                    http_status = getattr(response, "status", None)
            except HTTPError as exc:
                endpoint_reachable = True
                http_status = exc.code
            except URLError as exc:
                last_error = f"GBrain endpoint unreachable: {exc.reason}"
            except Exception as exc:  # pragma: no cover - defensive
                last_error = f"GBrain probe failed: {exc}"

        if endpoint_reachable and repo_exists:
            status = "healthy"
        elif url or repo_exists:
            status = "degraded"
            last_error = last_error or "GBrain configured only partially"
        else:
            status = "down"
            last_error = last_error or "No GBrain configuration or repo found"

        details = {
            "endpoint": sanitized_url,
            "endpoint_reachable": endpoint_reachable,
            "http_status": http_status,
            "brain_repo_exists": repo_exists,
            "brain_branch": git_branch(BRAIN_ROOT),
            "brain_recent_commit": git_recent_commit(BRAIN_ROOT),
            "evidence_timestamp": newest_timestamp([MAIN_HERMES_CONFIG, BRAIN_ROOT / ".git" if (BRAIN_ROOT / ".git").exists() else BRAIN_ROOT]),
        }
        return make_probe(
            name="gbrain",
            status=status,
            source="hermes-mcp-config+brain-repo+endpoint-probe",
            details=details,
            last_error=last_error,
        )

    def probe_workflows(self) -> dict[str, Any]:
        key_paths = OrderedDict(
            {
                "content_inbox": WORKFLOWS_ROOT / "content-engine" / "inbox",
                "knowledge_inbox": WORKFLOWS_ROOT / "knowledge-router" / "inbox",
                "build_inbox": WORKFLOWS_ROOT / "build-engine" / "inbox",
                "packet_promotion_state": WORKFLOWS_ROOT / "workflow-02-packet-promotion" / "state",
                "review_gate": WORKFLOWS_ROOT / "workflow-03-opportunity-review-gate",
                "control_plane": WORKFLOWS_ROOT / "control-plane",
            }
        )
        lanes = []
        existing_count = 0
        latest_mtime = None
        for name, path in key_paths.items():
            exists = path.exists()
            if exists:
                existing_count += 1
                latest_mtime = max(latest_mtime or 0, path.stat().st_mtime)
            lanes.append(
                {
                    "name": name,
                    "path": str(path),
                    "exists": exists,
                    "files": count_files(path),
                    "timestamp": file_timestamp(path),
                }
            )

        if existing_count == len(key_paths):
            status = "healthy"
            last_error = None
        elif existing_count > 0:
            status = "degraded"
            last_error = "Some WORKFLOWS lanes are missing or incomplete"
        else:
            status = "down"
            last_error = "WORKFLOWS repo not found"

        details = {
            "root": str(WORKFLOWS_ROOT),
            "branch": git_branch(WORKFLOWS_ROOT),
            "recent_commit": git_recent_commit(WORKFLOWS_ROOT),
            "lanes": lanes,
            "evidence_timestamp": datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z") if latest_mtime else None,
        }
        return make_probe(
            name="workflows",
            status=status,
            source="repo-state+lane-counts",
            details=details,
            last_error=last_error,
        )

    def snapshot(self) -> dict[str, Any]:
        cards: OrderedDict[str, dict[str, Any]] = OrderedDict()
        cards["hermes"] = self.probe_hermes()
        cards["telegram"] = self.probe_telegram()
        cards["gbrain"] = self.probe_gbrain()
        cards["workflows"] = self.probe_workflows()
        cards["alerts"] = build_alerts(cards)
        return {
            "overview": {
                "timestamp": iso_now(),
                "environment": "local-dev",
                "mode": "production",
                "version": "hero-reboot-v1",
            },
            "cards": cards,
            "card_order": CARD_ORDER,
        }


app = FastAPI(title="Hero Reboot Dashboard", description="Honest operator surface for Hermes, Telegram, GBrain, and WORKFLOWS")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
runtime = DashboardRuntime()


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: FastAPIRequest) -> HTMLResponse:
    snapshot = runtime.snapshot()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"initial_data": snapshot},
    )


@app.get("/api/status")
async def api_status() -> JSONResponse:
    return JSONResponse(runtime.snapshot())


@app.get("/api/healthz")
async def healthz() -> JSONResponse:
    snapshot = runtime.snapshot()
    return JSONResponse(
        {
            "status": "ok",
            "dashboard": "alive",
            "overall": snapshot["cards"]["alerts"]["status"],
            "timestamp": snapshot["overview"]["timestamp"],
        },
        status_code=200,
    )


@app.get("/api/readiness")
async def readiness() -> JSONResponse:
    snapshot = runtime.snapshot()
    statuses = [snapshot["cards"][name]["status"] for name in CARD_ORDER[:-1]]
    ready = all(status == "healthy" for status in statuses)
    return JSONResponse(
        {
            "status": "ready" if ready else "degraded",
            "timestamp": snapshot["overview"]["timestamp"],
            "cards": {name: snapshot["cards"][name]["status"] for name in CARD_ORDER[:-1]},
        },
        status_code=200 if ready else 503,
    )


def main() -> None:
    logger.info("Starting Hero reboot dashboard on http://127.0.0.1:8080")
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")


if __name__ == "__main__":
    main()
