# Hero Cache Producers Audit

Status: Phase 0 audit
Worktree: `hero-reboot-phase0`

## Summary

The dashboard stack currently mixes three classes of producers:

1. real-or-salvageable probes
2. stale-but-salvageable components
3. fake/demo writers that should not drive operator truth

That mix is why Hero renders a convincing dashboard while lying about actual system state.

## Current conclusion

The reboot should treat these as the only durable truth lanes:
- Hermes runtime / gateway
- Telegram operator lanes/topics
- GBrain memory health
- WORKFLOWS repo activity
- alert/incidence surface

Everything else is legacy until proven useful.

## Findings by class

### A. Fake/demo producers — remove from production path

These files currently synthesize or embellish state, hardcode health, or exist as sandbox/demo machinery.

#### `dynamic_agent_registry.py`
- writes: `dynamic_agents.json`, `communication_layer_status.json`
- issue: writes synthetic registry payloads and hardcodes healthy-looking NATS state
- verdict: demo-only, remove from production dashboard path

#### `real_working_system.py`
- writes: `communication_layer_status.json`
- issue: despite the name, it fabricates a “real” dashboard payload for local toy agents
- verdict: demo-only, archive or quarantine behind explicit dev mode

#### `register_custom_agent.py`
- writes: `custom_agent_*.json`, `agent_runtime_status.json`
- issue: custom agent self-registration can pollute canonical runtime state
- verdict: keep only as dev adapter/example, not operator truth

#### `clean_nats_system.py`
- writes: `communication_layer_status.json` and related state
- issue: cleanup/reset helper but still emits dashboard-shaped state
- verdict: utility only, not a production source

#### `agent_nats_wrapper.py`
- writes per-agent task/status payloads
- issue: wrapper/demo plumbing around old NATS-centered model
- verdict: quarantine from reboot path

#### `agent_subscriber.py`
- writes local task/status payloads
- issue: looks like sandbox subscriber plumbing, not canonical runtime truth
- verdict: demo/dev only

#### `nats_task_system.py`
- writes: `nats_status.json`
- issue: old architecture center-of-gravity; not aligned with current Hermes stack
- verdict: legacy integration at best, not dashboard foundation

#### `task_manager.py`
- writes: `real_agent_status.json`, `real_agent_coordination.json`
- issue: “real” naming hides local synthetic orchestration logic
- verdict: archive or dev-only

#### `Modular_PROPOSAL/examples/your_setup.py`
- issue: example code, not runtime truth
- verdict: ignore for production audit

### B. Real-or-salvageable producers — candidates for adapter layer

These at least probe something real or consume measurable system state.

#### `monitors/token_session_monitor.py`
- writes: `token_session_data.json`
- source: `ccusage session --json`
- value: real session/cost/reset signal when `ccusage` is available
- verdict: salvageable adapter, but must expose freshness and probe failures honestly

#### `monitors/conversation_stream_monitor.py`
- writes: `conversation_stream.json`
- source: local runtime/session stream
- value: potentially useful for recent activity / alerts
- verdict: salvageable, probably alerts-side input not primary card

#### `nats_monitor.py`
- writes: `nats_traffic.json`, `nats_discovery.json`
- source: NATS traffic/discovery probes
- value: only useful if NATS remains a real subsystem under reboot
- verdict: optional legacy adapter, not primary card

#### `inter_agent_communication.py`
- writes: `communication_layer.json`
- source: communication layer runtime
- value: legacy subsystem data; maybe useful for compatibility only
- verdict: salvage only if a real runtime still depends on it

#### `nats_task_coordinator.py`
- writes coordinator status
- source: actual NATS connection and queue work
- verdict: salvageable only as optional legacy signal

#### `monitors/graphiti_monitor.py`
- writes graphiti stats
- source: Graphiti/Neo4j probe path
- verdict: legacy knowledge-system probe; not first-slice priority now that GBrain is canonical

#### `monitors/langsmith_tracer.py`
- writes traces/stats caches
- source: LangSmith
- verdict: optional observability adapter if still used in live stack

#### `run_communication_system.py`
- writes: `system_metrics.json`
- source: runtime-managed metrics
- verdict: legacy/optional; salvage only if still genuinely run

### C. Stale-but-salvageable components — keep logic, replace source model

#### `web_dashboard.py`
- current Phase 0 reboot base
- good: FastAPI/Jinja surface, normalized probes, `/api/status`, `/api/healthz`, and `/api/readiness`
- bad: still shares the repo with several legacy dashboard paths, so launch docs must stay explicit
- verdict: canonical web reboot path

#### `tui_dashboard.py`
- reads multiple cache files but does not solve truth-layer issues
- verdict: legacy side surface only

#### `simple_cli_dashboard.py`
- same story: reader, not source of truth
- verdict: legacy

#### `architecture_orchestrator.py`
- writes runtime/coordination state
- issue: project-specific orchestration snapshot, not general operator truth
- verdict: stale-but-salvageable logic at most

## Monitors that are actively dishonest today

#### `monitors/claude_usage_monitor_optimized.py`
- writes: `claude_usage.json`
- issue: falls back to random mock token/session data
- verdict: blocked from production use until mocks are removed

#### `monitors/github_activity_monitor_optimized.py`
- writes: `github_activity.json`
- issue: falls back to random contribution graph data
- verdict: blocked from production use until fake fallback is removed

The non-optimized variants have the same disease.

## Immediate production exclusions

The following should be excluded from the first honest Hero slice:
- `dynamic_agent_registry.py`
- `real_working_system.py`
- `register_custom_agent.py`
- `clean_nats_system.py`
- `agent_nats_wrapper.py`
- `agent_subscriber.py`
- `nats_task_system.py`
- `task_manager.py`
- `monitors/claude_usage_monitor*.py`
- `monitors/github_activity_monitor*.py`

## First-slice data plan

### Card 1 — Hermes
Source should be a real runtime/process adapter, not any old cache file.

### Card 2 — Telegram
Source should be topic/lane health from the live operator surface.

### Card 3 — GBrain
Source should be GBrain/MCP reachability plus recent write/query metadata.

### Card 4 — WORKFLOWS
Source should be repo-backed lane state and artifact recency.

### Card 5 — Alerts
Source should be aggregated failures/stale states from the other adapters.

## Recommended repo moves

### Quarantine / archive
- old NATS demo/control-center writers
- mock-based monitors
- synthetic registry writers

### Keep and rewire
- `web_dashboard.py`
- `web_templates/dashboard.html`
- any genuinely useful probe logic from token/session, LangSmith, Graphiti, and local process monitors

### Build next
Create a new adapter layer instead of teaching templates about random cache files:
- `adapters/hermes_runtime.py`
- `adapters/telegram_surface.py`
- `adapters/gbrain_health.py`
- `adapters/workflows_status.py`
- `adapters/alerts.py`
- `adapters/base.py`

## Thin-slice recommendation

Do not start by fixing every legacy producer.

Start by making `web_dashboard.py` ignore them.
Then feed it one normalized payload built from the new adapters.
That gets Hero honest fast instead of preserving the whole haunted house.
