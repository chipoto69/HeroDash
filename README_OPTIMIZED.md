# Hero Reboot Notes for Legacy Operators

This file used to describe the optimized terminal dashboard. That is no longer the primary product story for the reboot branch.

Current reality:
- the canonical surface is the web reboot dashboard
- the canonical launcher is `./launch_web_dashboard.sh`
- the canonical APIs are `/api/status`, `/api/healthz`, and `/api/readiness`
- the canonical cards are Hermes, Telegram, GBrain, WORKFLOWS, and Alerts

## Why keep this file

A lot of legacy docs and muscle memory still point at “optimized dashboard” language. Keeping this file, but rewriting it honestly, prevents operators from assuming the old terminal/analytics stack is the supported path on `hero-reboot-phase0`.

## Reboot-first usage

```bash
./launch_web_dashboard.sh start
./launch_web_dashboard.sh status
./launch_web_dashboard.sh logs
./launch_web_dashboard.sh stop
```

Direct launch:

```bash
python3 web_dashboard.py
```

## What changed from the old optimized story

Removed as primary framing:
- terminal-first dashboard narrative
- old Graphiti/Neo4j-first worldview
- NATS-centric operator claims
- analytics-as-truth framing

Added as primary framing:
- Hermes support and runtime visibility
- Telegram topic/lane visibility
- GBrain MCP and repo health
- WORKFLOWS lane presence and recency
- explicit alert aggregation
- honest liveness vs readiness endpoints

## Endpoint summary

- `/api/status`: full five-card payload
- `/api/healthz`: dashboard process is alive
- `/api/readiness`: operator dependencies are healthy enough to trust

`/api/readiness` returns `503` when one or more primary cards are not healthy.

## Suggested verification

```bash
python3 -m py_compile web_dashboard.py
pytest -q tests/test_web_dashboard_reboot.py
curl http://127.0.0.1:8080/api/healthz
curl http://127.0.0.1:8080/api/readiness
```

## Legacy note

The old optimized terminal assets may still be useful for archaeology or migration, but they should not be read as the current Hero reboot contract.
