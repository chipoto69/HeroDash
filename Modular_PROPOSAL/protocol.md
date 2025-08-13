# Swarm Communication Protocol Specification

## Overview

This document defines the language-agnostic protocol for inter-agent communication. Any system that implements this protocol can participate in a swarm.

## Message Format

All messages are JSON objects with the following structure:

```json
{
  "id": "string (UUID)",
  "type": "string (see Message Types)",
  "from": "string (agent identifier)",
  "to": "string (agent identifier or '*' for broadcast)",
  "data": "object (message payload)",
  "meta": "object (optional metadata)",
  "timestamp": "string (ISO 8601 format)"
}
```

### Required Fields

- `id`: Unique message identifier (UUID v4 recommended)
- `type`: Message type from defined types
- `from`: Sending agent's identifier
- `to`: Target agent identifier or `*` for broadcast
- `data`: Message payload (can be empty object)

### Optional Fields

- `meta`: Additional metadata (priority, timeout, etc.)
- `timestamp`: Message creation time (ISO 8601)

## Message Types

### Core Types

#### TASK
Request an agent to perform work
```json
{
  "type": "task",
  "data": {
    "action": "string",
    "parameters": {}
  },
  "meta": {
    "priority": 1-4,
    "timeout": 300
  }
}
```

#### RESULT
Response to a task
```json
{
  "type": "result",
  "data": {
    "task_id": "original_task_id",
    "result": {},
    "success": true
  }
}
```

#### HEARTBEAT
Agent health status
```json
{
  "type": "heartbeat",
  "data": {
    "status": "healthy|degraded|unhealthy",
    "metrics": {
      "cpu": 45.2,
      "memory": 512,
      "tasks_completed": 42
    }
  }
}
```

#### REGISTER
Agent registration/capability announcement
```json
{
  "type": "register",
  "data": {
    "capabilities": ["nlp", "vision", "reasoning"],
    "metadata": {
      "version": "1.0",
      "model": "gpt-4"
    }
  }
}
```

#### DISCOVER
Request for agent discovery
```json
{
  "type": "discover",
  "data": {
    "filter": {
      "capabilities": ["nlp"]
    }
  }
}
```

Response:
```json
{
  "type": "discover",
  "data": {
    "agents": [
      {
        "id": "agent_123",
        "capabilities": ["nlp", "reasoning"]
      }
    ]
  }
}
```

#### SYNC
Synchronization checkpoint
```json
{
  "type": "sync",
  "data": {
    "checkpoint": "phase1_complete",
    "ready": true
  }
}
```

#### BROADCAST
Message to all agents
```json
{
  "type": "broadcast",
  "to": "*",
  "data": {
    "event": "system_update",
    "details": {}
  }
}
```

## Transport Bindings

### Topic Patterns

Messages are routed using topic patterns. Transports should map these patterns:

- `swarm.agent.{agent_id}.{message_type}` - Direct to agent
- `swarm.broadcast.{message_type}` - Broadcast messages
- `swarm.capability.{capability}.{message_type}` - Capability-based routing
- `swarm.type.{message_type}` - Type-based routing

### NATS Example
```
Subject: swarm.agent.worker1.task
Payload: {JSON message}
```

### Redis Example
```
PUBLISH swarm.broadcast.heartbeat {JSON message}
```

### HTTP Example
```
POST /swarm/agent/worker1/task
Content-Type: application/json
Body: {JSON message}
```

## Agent Lifecycle

### 1. Registration
Agent connects and announces capabilities:
```json
{
  "type": "register",
  "from": "agent_123",
  "to": "swarm",
  "data": {
    "capabilities": ["text_analysis", "summarization"]
  }
}
```

### 2. Discovery
Agent discovers other agents:
```json
{
  "type": "discover",
  "from": "agent_123",
  "to": "*"
}
```

### 3. Task Processing
Agent receives and processes tasks:
```json
// Receive
{
  "type": "task",
  "from": "coordinator",
  "to": "agent_123",
  "data": {"text": "analyze this"}
}

// Respond
{
  "type": "result",
  "from": "agent_123",
  "to": "coordinator",
  "data": {"task_id": "xxx", "result": {}}
}
```

### 4. Heartbeat
Agent sends periodic health updates:
```json
{
  "type": "heartbeat",
  "from": "agent_123",
  "to": "*",
  "data": {"status": "healthy"}
}
```

## Error Handling

### Error Response
```json
{
  "type": "result",
  "data": {
    "task_id": "xxx",
    "success": false,
    "error": {
      "code": "PROCESSING_ERROR",
      "message": "Failed to process task",
      "details": {}
    }
  }
}
```

### Standard Error Codes
- `TIMEOUT` - Task exceeded timeout
- `INVALID_REQUEST` - Malformed or invalid request
- `CAPABILITY_MISSING` - Agent lacks required capability
- `PROCESSING_ERROR` - Error during processing
- `RESOURCE_EXHAUSTED` - Agent at capacity

## Implementation Requirements

### Minimum Implementation

To participate in a swarm, an agent MUST:

1. Generate unique message IDs
2. Handle `TASK` messages and return `RESULT`
3. Respond to `DISCOVER` requests
4. Send periodic `HEARTBEAT` messages (recommended every 30s)

### Full Implementation

A complete implementation should also:

1. Support all message types
2. Implement capability-based routing
3. Handle synchronization checkpoints
4. Support broadcast messages
5. Implement error handling

## Examples

### Python
```python
import json
import uuid
from datetime import datetime

def create_message(msg_type, from_agent, to_agent, data):
    return {
        "id": str(uuid.uuid4()),
        "type": msg_type,
        "from": from_agent,
        "to": to_agent,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }

# Send task
task = create_message("task", "user", "worker", {"action": "process"})
```

### JavaScript
```javascript
function createMessage(type, from, to, data) {
  return {
    id: crypto.randomUUID(),
    type: type,
    from: from,
    to: to,
    data: data,
    timestamp: new Date().toISOString()
  };
}

// Send task
const task = createMessage("task", "user", "worker", {action: "process"});
```

### Go
```go
type Message struct {
    ID        string                 `json:"id"`
    Type      string                 `json:"type"`
    From      string                 `json:"from"`
    To        string                 `json:"to"`
    Data      map[string]interface{} `json:"data"`
    Meta      map[string]interface{} `json:"meta,omitempty"`
    Timestamp string                 `json:"timestamp"`
}

func NewMessage(msgType, from, to string, data map[string]interface{}) Message {
    return Message{
        ID:        uuid.New().String(),
        Type:      msgType,
        From:      from,
        To:        to,
        Data:      data,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
    }
}
```

## Versioning

Protocol version: 1.0.0

Future versions will maintain backward compatibility or provide migration paths.