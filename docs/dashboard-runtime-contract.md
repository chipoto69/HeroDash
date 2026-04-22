# Hero Dashboard Runtime Contract v2

Status: draft for Hero reboot Phase 0

## Goal

Stop the dashboard from rendering fantasy health.

Every card must read from a real source, carry freshness metadata, and surface failure honestly.

## Core principles

1. No mock or random data in production mode.
2. No silent fallback from real to fake.
3. Every subsystem returns:
   - `status`
   - `source`
   - `timestamp`
   - `freshness_seconds`
   - `last_error`
4. Stale data must render as stale, not healthy.
5. Dashboard code should aggregate a normalized model, not read thirty unrelated cache shapes directly.
6. Telegram, Hermes, GBrain, and WORKFLOWS are first-class sources. Old NATS toy state is not.

## Canonical top-level shape

```json
{
  "overview": {
    "timestamp": "2026-04-22T00:00:00Z",
    "environment": "local-dev",
    "mode": "production",
    "version": "hero-v2"
  },
  "system": {
    "status": "healthy|degraded|down|stale",
    "source": "local-probes",
    "timestamp": "...",
    "freshness_seconds": 4,
    "last_error": null
  },
  "gateway": {
    "status": "healthy|degraded|down|stale",
    "source": "hermes-runtime",
    "timestamp": "...",
    "freshness_seconds": 8,
    "last_error": null,
    "profiles": [],
    "sessions": []
  },
  "telegram": {
    "status": "healthy|degraded|down|stale",
    "source": "telegram-gateway",
    "timestamp": "...",
    "freshness_seconds": 12,
    "last_error": null,
    "topics": [],
    "lane_activity": []
  },
  "memory": {
    "status": "healthy|degraded|down|stale",
    "source": "gbrain-mcp",
    "timestamp": "...",
    "freshness_seconds": 15,
    "last_error": null,
    "recent_writes": [],
    "query_latency_ms": null
  },
  "workflows": {
    "status": "healthy|degraded|down|stale",
    "source": "workflows-repo",
    "timestamp": "...",
    "freshness_seconds": 20,
    "last_error": null,
    "lanes": [],
    "packets": {},
    "runs": []
  },
  "alerts": {
    "status": "healthy|degraded|down|stale",
    "source": "hero-aggregator",
    "timestamp": "...",
    "freshness_seconds": 3,
    "last_error": null,
    "items": []
  }
}
```

## Status rules

### healthy
- source probe succeeded
- freshness is within threshold
- no active blocking error

### degraded
- source reachable but partial
- recent probe failures or missing optional fields
- high latency or lagging updates

### stale
- last known payload exists but exceeds freshness threshold
- UI may still show data, but badge must be stale

### down
- probe failed and no usable current payload exists

## Freshness thresholds

- system: 15s
- gateway: 30s
- telegram: 60s
- memory: 120s
- workflows: 120s
- alerts: 15s

These are defaults, not religion.

## Required adapter behavior

Each adapter should expose one normalized probe result:

```json
{
  "status": "healthy",
  "source": "adapter-name",
  "timestamp": "...",
  "freshness_seconds": 0,
  "last_error": null,
  "data": {}
}
```

The aggregator composes these into the top-level dashboard object.

## Source-of-truth priorities

1. Hermes runtime / gateway
2. Telegram operator surface
3. GBrain / Supabase-backed memory layer
4. WORKFLOWS repo artifacts
5. local process and scheduler state

Legacy cache files are transitional inputs only. They are not the long-term contract.

## Transitional compatibility rule

During reboot, old cache readers are allowed only behind explicit adapters.

Bad:
- template reads `agent_runtime_status.json` directly
- UI assumes `nats_connected: true`

Good:
- adapter reads legacy file
- adapter computes freshness
- adapter emits normalized contract

## Explicitly banned in production mode

- random contribution data
- random token/session data
- demo agent registries claiming live health
- hardcoded `nats_connected: true`
- hardcoded `system_status: operational` without probes
- fallback from real probe failure to fake success payload

## First honest slice

The first reboot slice should only expose five cards:

1. Hermes
2. Telegram
3. GBrain
4. WORKFLOWS
5. Alerts

Everything else can come back only if it proves it is real.
