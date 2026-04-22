# Hero Reboot Thin Slice

## Objective

Ship the first honest operator surface fast.

Not comprehensive. Honest.

## Scope

Replace the current mono dashboard data model with five cards only:

1. Hermes
2. Telegram
3. GBrain
4. WORKFLOWS
5. Alerts

## Why this slice

Because these are the real current system pillars.
Everything else in Hero is either legacy, optional, or bullshit until proven otherwise.

## Adapter plan

### Hermes adapter
Checks:
- gateway/routing process alive
- active profile count if retrievable
- latest session/update timestamp
- last known error

### Telegram adapter
Checks:
- gateway connected to the operator supergroup/topics
- lane/topic heartbeat or recent message metadata
- failures like missing thread targets or send errors

### GBrain adapter
Checks:
- MCP/tool reachability
- recent write/read success
- optional query latency

### WORKFLOWS adapter
Checks:
- repo exists and is readable
- key lane directories present
- recent file activity in lane/state/output docs
- packet counts or queue artifact counts

### Alerts adapter
Aggregates:
- any subsystem in `degraded`, `stale`, or `down`
- freshness breaches
- last error summaries

## UI behavior

Every card must show:
- status badge
- source name
- last update
- freshness age
- concise detail line
- last error if present

## Explicitly not in thin slice

- fake NATS swarm topology
- mock Claude usage
- fake GitHub graph
- command-center playground panels
- synthetic agent registry visuals

## Suggested implementation order

1. add adapter base contract
2. add Hermes adapter
3. add GBrain adapter
4. add WORKFLOWS adapter
5. add Telegram adapter
6. add Alerts aggregator
7. rewire `/api/status`
8. trim `dashboard_mono.html` to five cards

## Done means

A dashboard can load with:
- no fake data
- visible stale/error states
- a truthful summary of the current stack

That is enough to call Hero alive again.
