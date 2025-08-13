# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# NATS Inter-Agent Communication System

**Core Purpose**: Standardized communication layer for synchronizing agentic swarms with immediate memory sharing and coordination capabilities. Provides out-of-the-box infrastructure for multi-agent systems with task distribution, load balancing, and collective intelligence.

## Quick Start - Get a Swarm Running

```bash
# 1. Start NATS server (port 4224 for development)
nats-server -c nats_dev.conf

# 2. Run demo swarm (creates 4 agents, distributes 31 tasks)
python3 demo_communication_system.py

# 3. Monitor swarm activity (optional dashboard)
./hero_optimized
```

## Common Development Commands

### Running the Communication System
```bash
# Start full orchestrator with auto-scaling
python3 run_communication_system.py --nats-url nats://localhost:4224

# Run tests to verify system
python3 test_communication_layer.py --nats-url nats://localhost:4224

# Demo with custom agent count
python3 demo_communication_system.py --agents 10

# Check NATS connection
python3 test_nats_connection.py
```

### Creating Custom Agents
```bash
# Register a new custom agent type
python3 register_custom_agent.py --type "analyzer" --capabilities "nlp,sentiment"

# Launch agent workers
python3 agents/launch_agents.sh --type analyzer --count 5
```

### Dashboard Monitoring (Optional)
```bash
# Setup dashboard (one-time)
./setup_optimized_fixed.sh

# Launch dashboard
./hero_optimized

# Individual monitors
python3 monitors/agents_monitor.py
python3 monitors/nats_monitor.py
```

### Testing
```bash
# Unit tests for communication layer
python3 test_communication_layer.py

# Integration test with multiple agents
python3 agents/test_agent_integration.py

# Load test with high task volume
python3 test_communication_layer.py --load-test --tasks 1000
```

## Architecture - Communication Layer

### Core System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    NATS JetStream (Port 4224)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Streams:                                              │  │
│  │ • HERO_TASKS_DEV - Task queue (WorkQueue pattern)    │  │
│  │ • HERO_EVENTS_DEV - Event bus (pub/sub)              │  │
│  │ • HERO_SYNC_DEV - Synchronization barriers           │  │
│  │ • HERO_COORDINATION_DEV - Agent registry & heartbeat │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│         InterAgentCommunicationLayer (Orchestrator)         │
│  • Task distribution with priority queuing                  │
│  • Load balancing across agent capabilities                 │
│  • Synchronization checkpoints for coordinated actions      │
│  • Agent health monitoring & failure recovery               │
│  • Shared memory through NATS KV store                      │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Agent Swarm (BaseAgent)                  │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Agent1│  │Agent2│  │Agent3│  │Agent4│  │AgentN│  ...    │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘        │
│  Each agent:                                                │
│  • Registers capabilities on startup                        │
│  • Receives tasks based on capabilities & load              │
│  • Reports heartbeat every 5 seconds                        │
│  • Shares results to collective memory                      │
└─────────────────────────────────────────────────────────────┘
```

### Communication Patterns

1. **Agent Registration**: `agent.register()` → Updates registry with capabilities
2. **Task Distribution**: Orchestrator assigns tasks based on agent capabilities and current load
3. **Synchronization**: Agents reach checkpoints, wait for barrier completion
4. **Memory Sharing**: Results published to NATS KV store, accessible by all agents
5. **Health Monitoring**: Heartbeat system detects failures, triggers task reassignment

### Key Files

- `inter_agent_communication.py` - Core orchestration layer with task distribution, load balancing, synchronization
- `agent_coordination_utils.py` - BaseAgent class, task handlers, heartbeat system
- `run_communication_system.py` - System bootstrapper, auto-scaling, health monitoring
- `demo_communication_system.py` - Working example of multi-agent task processing
- `test_communication_layer.py` - Comprehensive test suite

## Creating a Custom Agent

```python
from agent_coordination_utils import BaseAgent, TaskResult

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="custom_worker",
            capabilities=["analysis", "processing"],
            max_concurrent_tasks=5,
            nats_url="nats://localhost:4224"
        )
    
    async def default_task_handler(self, task_data):
        # Process task based on type
        result = await self.process(task_data)
        
        # Share to collective memory
        await self.publish_to_memory("results", result)
        
        return TaskResult(success=True, data=result)

# Run agent
agent = CustomAgent()
asyncio.run(agent.run())
```

## Task Distribution Example

```python
from inter_agent_communication import InterAgentCommunicationLayer, TaskPriority

# Initialize orchestrator
comm_layer = InterAgentCommunicationLayer()
await comm_layer.initialize()

# Create high-priority task
task_id = await comm_layer.create_task(
    task_type="analysis",
    data={"content": "..."},
    priority=TaskPriority.HIGH
)

# Task automatically distributed to capable agent with lowest load
# Result available via: await comm_layer.get_task_result(task_id)
```

## Testing Patterns

```python
# Test agent coordination
async def test_multi_agent_sync():
    agents = [DemoAgent(i) for i in range(4)]
    
    # Start all agents
    await asyncio.gather(*[a.initialize() for a in agents])
    
    # Create synchronization point
    await comm_layer.create_sync_checkpoint("phase1", expected_agents=4)
    
    # All agents must reach checkpoint
    results = await asyncio.gather(*[a.reach_checkpoint("phase1") for a in agents])
    assert all(results)  # All agents synchronized
```

## Performance Optimizations

- **Command caching**: Dashboard caches expensive operations (30s TTL)
- **Batch processing**: Agents process multiple tasks in parallel
- **Connection pooling**: Reuse NATS connections across agents
- **Async operations**: All I/O is non-blocking
- **Load balancing**: Tasks distributed based on agent capacity

## Troubleshooting

```bash
# Check NATS server status
nats server info

# View task queue
nats stream view HERO_TASKS_DEV

# Monitor agent heartbeats
nats sub "hero.v1.dev.agents.heartbeat.>"

# Check communication layer logs
tail -f ~/.hero_core/communication.log

# Verify agent registration
cat ~/.hero_core/cache/communication_layer.json | jq .agents
```

## Security & Production

- **NATS Auth**: Enable authentication in production (`nats.conf`)
- **TLS**: Use `nats://tls://` URLs for encrypted communication
- **Rate limiting**: Configure max tasks per agent
- **API keys**: Store in environment variables, never in code
- **Monitoring**: Use LangSmith for production observability