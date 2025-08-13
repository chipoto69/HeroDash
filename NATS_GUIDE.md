# 🚀 NATS Integration Guide - Hero Command Centre

## Overview

NATS (Neural Autonomic Transport System) serves as the messaging backbone for your Hero agent ecosystem. Here's how to control it and use it for project synchronization.

## 🔧 NATS Connection Architecture

### Current Setup
- **NATS Server**: Running on `nats://localhost:4222` (default) or `4224` (Hero custom)
- **Message Subjects**: Hierarchical topic routing for agent communication
- **JetStream**: Persistent messaging for reliable task distribution
- **Connection Pool**: Shared connection across all agents

### Subject Hierarchy
```
hero.v1.{environment}.{agent_type}.{action}

Examples:
- hero.v1.dev.orchestrator.tasks.assign
- hero.v1.dev.knowledge.tasks.complete
- hero.v1.dev.agents.heartbeat
- hero.v1.dev.coordination.sync
```

## 🎮 Taking Control of NATS

### 1. **Manual NATS Server Control**
```bash
# Start NATS server manually
nats-server -p 4222

# Start with JetStream enabled
nats-server -p 4222 -js

# Start with custom config
nats-server -c /path/to/nats.conf
```

### 2. **Environment Variables**
```bash
# Set custom NATS URL
export NATS_URL="nats://localhost:4224"

# Enable NATS debugging
export NATS_DEBUG=true

# Set connection timeout
export NATS_TIMEOUT=30
```

### 3. **Check NATS Status**
```bash
# Check if NATS is running
nats stream ls

# View server info
nats server info

# Monitor connections
nats server ping
```

## 🤝 Using NATS for Project Synchronization

### 1. **Agent Discovery & Registration**
```python
# In your agent code
import asyncio
import nats
import json
from datetime import datetime

async def register_agent():
    nc = await nats.connect("nats://localhost:4222")
    
    # Register this agent
    agent_info = {
        "agent_id": "your-unique-id",
        "agent_type": "custom_agent",
        "capabilities": ["nlp", "data_analysis"],
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "project_id": "your-project-id"
    }
    
    await nc.publish(
        "hero.v1.dev.agents.register",
        json.dumps(agent_info).encode()
    )
    
    # Listen for coordination messages
    await nc.subscribe(
        "hero.v1.dev.coordination.*",
        cb=handle_coordination_message
    )
```

### 2. **Task Coordination Protocol**
```python
async def coordinate_task(nc, task_data):
    # Announce task start
    await nc.publish(
        "hero.v1.dev.coordination.task_start",
        json.dumps({
            "task_id": task_data["id"],
            "agent_id": "your-agent-id",
            "project_id": "your-project",
            "dependencies": task_data.get("depends_on", []),
            "estimated_duration": task_data.get("duration", 60)
        }).encode()
    )
    
    # Work on task...
    result = await process_task(task_data)
    
    # Announce completion
    await nc.publish(
        "hero.v1.dev.coordination.task_complete",
        json.dumps({
            "task_id": task_data["id"],
            "agent_id": "your-agent-id",
            "result": result,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }).encode()
    )
```

### 3. **Project State Synchronization**
```python
async def sync_project_state(nc, project_state):
    # Broadcast project state update
    await nc.publish(
        "hero.v1.dev.project.state_update",
        json.dumps({
            "project_id": "your-project",
            "state": project_state,
            "version": "1.2.3",
            "updated_by": "your-agent-id",
            "timestamp": datetime.now().isoformat()
        }).encode()
    )

async def listen_for_project_updates(nc):
    async def message_handler(msg):
        data = json.loads(msg.data.decode())
        # Update local project state
        await update_local_state(data["state"])
    
    await nc.subscribe("hero.v1.dev.project.state_update", cb=message_handler)
```

## 📊 Making Your Agents Visible in Dashboard

### 1. **Agent Registration Template**
```python
#!/usr/bin/env python3
"""
Your Custom Agent - Hero Dashboard Integration
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

class CustomAgent:
    def __init__(self, agent_type="custom_agent"):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.status = "initializing"
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def register_with_dashboard(self):
        """Register this agent with Hero Dashboard"""
        agent_data = {
            "timestamp": datetime.now().isoformat(),
            "runtime_stats": {
                "start_time": datetime.now().isoformat(),
                "agents_launched": 1,
                "tasks_processed": 0,
                "messages_handled": 0,
                "uptime_seconds": 0
            },
            "agents": {
                self.agent_id: {
                    "agent_type": self.agent_type,
                    "status": "active",
                    "current_task": None,
                    "performance": {
                        "tasks_completed": 0,
                        "success_rate": 1.0,
                        "avg_response_time": 0.0,
                        "errors": 0
                    },
                    "last_heartbeat": datetime.now().isoformat()
                }
            },
            "nats_connected": True,
            "hero_integration": {
                "coordinator_available": True,
                "bridge_available": True,
                "tracer_available": True
            }
        }
        
        # Write to dashboard cache
        cache_file = self.cache_dir / f"custom_agent_{self.agent_id[:8]}.json"
        with open(cache_file, 'w') as f:
            json.dump(agent_data, f, indent=2)
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to dashboard"""
        while True:
            await self.register_with_dashboard()
            await asyncio.sleep(5)  # Heartbeat every 5 seconds

# Usage
if __name__ == "__main__":
    agent = CustomAgent("your_custom_type")
    asyncio.run(agent.send_heartbeat())
```

### 2. **Dashboard Integration Script**
```python
#!/usr/bin/env python3
"""
Multi-Agent Dashboard Integration
"""
import json
import glob
from pathlib import Path
from datetime import datetime

def aggregate_agent_data():
    """Aggregate all agent data for dashboard"""
    cache_dir = Path.home() / ".hero_core" / "cache"
    
    # Find all agent cache files
    agent_files = glob.glob(str(cache_dir / "*agent*.json"))
    
    aggregated = {
        "timestamp": datetime.now().isoformat(),
        "total_agents": 0,
        "active_agents": 0,
        "agents": {},
        "runtime_stats": {
            "start_time": datetime.now().isoformat(),
            "agents_launched": 0,
            "tasks_processed": 0,
            "messages_handled": 0,
            "uptime_seconds": 0
        }
    }
    
    for file_path in agent_files:
        try:
            with open(file_path, 'r') as f:
                agent_data = json.load(f)
            
            # Merge agent data
            if "agents" in agent_data:
                aggregated["agents"].update(agent_data["agents"])
                aggregated["total_agents"] += len(agent_data["agents"])
                
                for agent in agent_data["agents"].values():
                    if agent.get("status") == "active":
                        aggregated["active_agents"] += 1
                        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Write aggregated data
    with open(cache_dir / "agent_runtime_status.json", 'w') as f:
        json.dump(aggregated, f, indent=2)

if __name__ == "__main__":
    aggregate_agent_data()
```

### 3. **Run Aggregation Script**
```bash
# Create the script
cat > /Users/rudlord/Hero_dashboard/aggregate_agents.py << 'EOF'
[Insert script from above]
EOF

# Make it executable
chmod +x /Users/rudlord/Hero_dashboard/aggregate_agents.py

# Run periodically (add to cron or run manually)
python3 /Users/rudlord/Hero_dashboard/aggregate_agents.py
```

## 🔄 Project Synchronization Patterns

### 1. **Master-Worker Pattern**
```python
# Master agent coordinates work
async def master_coordinator():
    nc = await nats.connect()
    
    tasks = ["task1", "task2", "task3"]
    for task in tasks:
        await nc.publish("hero.v1.dev.tasks.assign", task.encode())
    
    # Wait for completions
    await nc.subscribe("hero.v1.dev.tasks.complete", cb=handle_completion)

# Worker agents process tasks
async def worker_agent():
    nc = await nats.connect()
    
    async def task_handler(msg):
        task = msg.data.decode()
        result = await process_task(task)
        await nc.publish("hero.v1.dev.tasks.complete", result.encode())
    
    await nc.subscribe("hero.v1.dev.tasks.assign", cb=task_handler)
```

### 2. **Event-Driven Synchronization**
```python
# Agent publishes state changes
async def publish_state_change(nc, state_change):
    await nc.publish(
        "hero.v1.dev.events.state_change",
        json.dumps({
            "event_type": "file_modified",
            "details": state_change,
            "timestamp": datetime.now().isoformat()
        }).encode()
    )

# Other agents react to state changes
async def state_change_listener(nc):
    async def handler(msg):
        event = json.loads(msg.data.decode())
        await react_to_state_change(event)
    
    await nc.subscribe("hero.v1.dev.events.*", cb=handler)
```

### 3. **Consensus Protocol**
```python
# Simple consensus for shared decisions
async def propose_decision(nc, proposal):
    await nc.publish(
        "hero.v1.dev.consensus.proposal",
        json.dumps({
            "proposal_id": str(uuid.uuid4()),
            "proposal": proposal,
            "proposer": "agent-id"
        }).encode()
    )

async def vote_on_proposal(nc, proposal_id, vote):
    await nc.publish(
        "hero.v1.dev.consensus.vote",
        json.dumps({
            "proposal_id": proposal_id,
            "vote": vote,  # "approve" or "reject"
            "voter": "agent-id"
        }).encode()
    )
```

## 🛠️ Quick Setup Commands

### 1. **Start NATS for Hero Project**
```bash
# Option 1: Use Hero's NATS setup
cd /Users/rudlord/q3/frontline
make nats-up

# Option 2: Start NATS manually
nats-server -p 4222 -js

# Option 3: Custom config
nats-server -c hero_nats.conf
```

### 2. **Test NATS Connection**
```bash
# Install NATS CLI
go install github.com/nats-io/natscli/nats@latest

# Test connection
nats pub hero.v1.dev.test "Hello World"
nats sub hero.v1.dev.test
```

### 3. **Monitor NATS Activity**
```bash
# View all subjects
nats stream ls

# Monitor specific subject
nats sub "hero.v1.dev.>"

# Check server stats
nats server info
```

## 📱 Integration with Your Terminal Agents

To get your terminal-spawned agents to show up in the dashboard:

1. **Copy the CustomAgent template** and modify for your agent type
2. **Run the aggregation script** periodically to merge agent data
3. **Use NATS subjects** for coordination between your agents
4. **Send heartbeats** every 5-10 seconds to keep dashboard updated

Your agents will then appear in the web dashboard at http://localhost:8080 with real-time status updates!