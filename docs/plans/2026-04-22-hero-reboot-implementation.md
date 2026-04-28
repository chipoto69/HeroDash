# Hero Reboot Implementation Plan

> For Hermes: implement the first honest Hero dashboard slice in the clean `hero-reboot-phase0` worktree. Do not preserve fake NATS theater.

Goal: replace the old analytics/fake-agent dashboard with a truthful operator surface for Hermes, Factory Droids, Telegram, GBrain, WORKFLOWS, and Alerts.

Architecture: keep `web_dashboard.py` as the canonical entrypoint on port 8080, but rewrite it around a small adapter layer and a normalized runtime contract. Render one simple HTML dashboard via Jinja, poll `/api/status`, and expose stale/degraded/down states honestly.

Tech stack: Python 3, FastAPI, Jinja2, stdlib probes, optional PyYAML, pytest.

---

## Task 1: Write the implementation plan artifact
Objective: leave behind the execution map in the worktree.

Files:
- Create: `docs/plans/2026-04-22-hero-reboot-implementation.md`

Verification:
- Confirm the plan file exists and is committed with the code changes.

## Task 2: Rebuild the backend around honest probes
Objective: replace fake cache aggregation with real subsystem probes.

Files:
- Modify: `web_dashboard.py`
- Create: `tests/test_web_dashboard_reboot.py`

Implementation targets:
- Add adapters/probes for:
  - Hermes runtime
  - Telegram topic surface
  - GBrain health
  - WORKFLOWS activity
  - Alerts aggregation
- Add normalized response contract with:
  - `status`
  - `source`
  - `timestamp`
  - `freshness_seconds`
  - `last_error`
- Keep `/api/status`
- Add `/api/healthz`
- Remove WebSocket dependency from the dashboard path

Verification:
- `python3 -m py_compile web_dashboard.py`
- `pytest -q tests/test_web_dashboard_reboot.py`

## Task 3: Build the new canonical-card UI
Objective: replace missing/legacy template assumptions with a simple real operator surface.

Files:
- Create: `web_templates/dashboard.html`

Implementation targets:
- Render only the canonical operator cards:
  - Hermes
  - Factory Droids
  - Telegram
  - GBrain
  - WORKFLOWS
  - Alerts
- Show status badge, freshness, source, concise details, last error
- Poll `/api/status` periodically
- Keep the design blunt and legible

Verification:
- `python3 web_dashboard.py` boots on 8080
- `curl http://127.0.0.1:8080/api/status`
- `curl http://127.0.0.1:8080/`

## Task 4: Update launcher messaging
Objective: keep the launcher aligned with the rebooted dashboard.

Files:
- Modify: `launch_web_dashboard.sh`

Implementation targets:
- Keep dependency checks intact
- Update human-facing text to reference the honest operator dashboard and the trimmed API surface

Verification:
- `bash -n launch_web_dashboard.sh`

## Task 5: Review, fix, commit, and push
Objective: finish like an adult.

Files:
- Review all modified files

Verification pipeline:
- `python3 -m py_compile web_dashboard.py`
- `pytest -q tests/test_web_dashboard_reboot.py`
- boot dashboard and curl endpoints
- independent review subagent using `requesting-code-review`
- fix findings if needed
- `git add -A && git commit ... && git push -u origin hero-reboot-phase0`
