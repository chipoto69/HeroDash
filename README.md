# Hero Reboot Dashboard

Hero is now an honest web operator surface for the current stack, not a fake swarm demo.

It serves the operator-critical cards only:
- Hermes
- Factory Droids
- Telegram
- GBrain
- WORKFLOWS
- Alerts

Primary entrypoints:
- UI: `http://127.0.0.1:8080/`
- Status API: `http://127.0.0.1:8080/api/status`
- Liveness: `http://127.0.0.1:8080/api/healthz`
- Readiness: `http://127.0.0.1:8080/api/readiness`

## What it actually does

The rebooted dashboard probes real local evidence instead of replaying old cache theater.

- Hermes: checks local Hermes process activity, gateway/webapi ports, and known profile configs
- Telegram: checks Telegram-facing Hermes profiles plus canon/topic metadata
- GBrain: checks Hermes MCP config, sanitized endpoint reachability, and local brain repo state
- WORKFLOWS: checks the WORKFLOWS repo, key lane directories, file counts, and recent commit state
- Alerts: aggregates any degraded, stale, or down subsystem into one operator-facing surface

If a subsystem is old, partial, or missing, Hero should say so plainly.

## What it does not do anymore

The reboot path does not present these as current operator truth:
- fake NATS swarm topology
- synthetic agent registries
- Graphiti-first/Neo4j-first control-plane mythology
- analytics dashboards pretending to be runtime health
- random fallback data for tokens, GitHub, or agents

Legacy files remain in the repo, but they are not the canonical reboot path.

## Run it

### Hermes-aware defaults

By default, the reboot expects local Rudy-style paths:
- `~/.hermes/config.yaml`
- `~/brain`
- `~/wiki/queries/grok420system.md`
- `~/ORGANIZED/ACTIVE_PROJECTS/ARSENAL/WORKFLOWS`

You can override those with env vars:

```bash
export HERO_HERMES_CONFIG=~/.hermes/config.yaml
export HERO_BRAIN_ROOT=~/brain
export HERO_TELEGRAM_CANON=~/wiki/queries/grok420system.md
export HERO_WORKFLOWS_ROOT=~/ORGANIZED/ACTIVE_PROJECTS/ARSENAL/WORKFLOWS
export HERO_WEBAPI_PORT=8642
export HERO_WORKSPACE_PORT=3011
export HERO_DROID_BRIDGE_PORT=8645
export HERO_FACTORY_SETTINGS=~/.factory/settings.json
```

Requirements:
- Python 3
- `fastapi`
- `uvicorn`
- `jinja2`
- `PyYAML`
- optional but useful local assets:
  - `~/.hermes/config.yaml`
  - `~/.hermes/profiles/`
  - `~/.factory/settings.json`
  - `~/.local/bin/droid`
  - `~/brain`
  - `~/ORGANIZED/ACTIVE_PROJECTS/ARSENAL/WORKFLOWS`
  - `~/wiki/queries/grok420system.md`

Start the dashboard:

```bash
./launch_web_dashboard.sh start
```

Other useful commands:

```bash
./launch_web_dashboard.sh status
./launch_web_dashboard.sh logs
./launch_web_dashboard.sh stop
```

You can also run the app directly:

```bash
python3 web_dashboard.py
```

## API contract

Current contract shape:

```json
{
  "overview": {
    "timestamp": "2026-04-22T00:00:00Z",
    "environment": "local-dev",
    "mode": "production",
    "version": "hero-reboot-v1"
  },
  "cards": {
    "hermes": {"status": "healthy", "source": "...", "timestamp": "...", "freshness_seconds": 0, "last_error": null, "details": {}},
    "droids": {"status": "healthy", "source": "...", "timestamp": "...", "freshness_seconds": 0, "last_error": null, "details": {}},
    "telegram": {"status": "healthy", "source": "...", "timestamp": "...", "freshness_seconds": 0, "last_error": null, "details": {}},
    "gbrain": {"status": "healthy", "source": "...", "timestamp": "...", "freshness_seconds": 0, "last_error": null, "details": {}},
    "workflows": {"status": "healthy", "source": "...", "timestamp": "...", "freshness_seconds": 0, "last_error": null, "details": {}},
    "alerts": {"status": "healthy", "source": "hero-aggregator", "timestamp": "...", "freshness_seconds": 0, "last_error": null, "details": {"items": []}}
  },
  "card_order": ["hermes", "droids", "telegram", "gbrain", "workflows", "alerts"]
}
```

Status semantics:
- `healthy`: probe succeeded and freshness is acceptable
- `degraded`: partial evidence or partial failure
- `stale`: evidence exists but is too old
- `down`: probe failed and no usable current evidence exists

## Docs worth reading

- `docs/plans/2026-04-22-hero-reboot-implementation.md`
- `docs/dashboard-runtime-contract.md`
- `docs/dashboard-producers-audit.md`
- `docs/hero-reboot-thin-slice.md`

## Validation

```bash
python3 -m py_compile web_dashboard.py
pytest -q tests/test_web_dashboard_reboot.py
bash -n launch_web_dashboard.sh
```

## Current reality check

This repo still contains a lot of legacy NATS/analytics/terminal-dashboard material. The rebooted dashboard path is only:
- `web_dashboard.py`
- `web_templates/dashboard.html`
- `launch_web_dashboard.sh`
- `tests/test_web_dashboard_reboot.py`
- the reboot docs in `docs/`

High-noise legacy docs that are now explicitly marked as historical context:
- `ANALYTICS_GUIDE.md`
- `NATS_GUIDE.md`
- `README_UPDATED.md`
- `cli_agent_briefing.md`
- `CLAUDE.md`

If documentation elsewhere disagrees with those files, trust the reboot path first.
