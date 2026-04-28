#!/usr/bin/env python3
"""
Custom Agent Registration Template for Hero Dashboard
Use this template to make your terminal-spawned agents visible in the dashboard
"""
import asyncio
import json
import uuid
import sys
import argparse
from datetime import datetime
from pathlib import Path

class CustomAgent:
    def __init__(self, agent_type="custom_agent", agent_name=None):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.agent_name = agent_name or f"{agent_type}_{self.agent_id[:8]}"
        self.status = "active"
        self.start_time = datetime.now()
        self.tasks_completed = 0
        self.errors = 0
        
        # Cache directory setup
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Initialized {self.agent_type} agent: {self.agent_name}")
        print(f"🆔 Agent ID: {self.agent_id}")
        
    def update_task_status(self, task_name=None, status="active"):
        """Update current task status"""
        self.current_task = task_name
        self.status = status
        print(f"📋 Task updated: {task_name} [{status}]")
        
    def complete_task(self, success=True):
        """Mark a task as completed"""
        self.tasks_completed += 1
        if not success:
            self.errors += 1
        self.current_task = None
        self.status = "idle"
        print(f"✅ Task completed. Total: {self.tasks_completed}, Errors: {self.errors}")
        
    async def register_with_dashboard(self):
        """Register this agent with Hero Dashboard"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        success_rate = (self.tasks_completed - self.errors) / max(1, self.tasks_completed)
        
        agent_data = {
            "timestamp": datetime.now().isoformat(),
            "runtime_stats": {
                "start_time": self.start_time.isoformat(),
                "agents_launched": 1,
                "tasks_processed": self.tasks_completed,
                "messages_handled": 0,
                "uptime_seconds": int(uptime)
            },
            "agents": {
                self.agent_id: {
                    "agent_type": self.agent_type,
                    "agent_name": self.agent_name,
                    "status": self.status,
                    "current_task": getattr(self, 'current_task', None),
                    "performance": {
                        "tasks_completed": self.tasks_completed,
                        "success_rate": success_rate,
                        "avg_response_time": 250.0,  # Default value
                        "errors": self.errors
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
        
        # Write individual agent cache file
        agent_cache_file = self.cache_dir / f"custom_agent_{self.agent_id[:8]}.json"
        with open(agent_cache_file, 'w') as f:
            json.dump(agent_data, f, indent=2)
            
    async def send_heartbeat_loop(self, interval=5):
        """Send periodic heartbeat to dashboard"""
        print(f"💓 Starting heartbeat loop (every {interval}s)")
        print(f"📊 Dashboard: http://localhost:8080")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                await self.register_with_dashboard()
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping {self.agent_name}")
            # Clean up cache file
            try:
                agent_cache_file = self.cache_dir / f"custom_agent_{self.agent_id[:8]}.json"
                agent_cache_file.unlink(missing_ok=True)
                print(f"🧹 Cleaned up cache file")
            except Exception as e:
                print(f"⚠️ Error cleaning up: {e}")
    
    async def simulate_work(self):
        """Simulate agent doing work with tasks"""
        task_names = [
            "data_analysis", "nlp_processing", "model_training", 
            "api_request", "file_processing", "computation"
        ]
        
        while True:
            # Pick a random task
            import random
            task = random.choice(task_names)
            duration = random.uniform(5, 20)  # 5-20 seconds
            
            # Start task
            self.update_task_status(task, "busy")
            await self.register_with_dashboard()
            
            print(f"🔄 Working on {task} for {duration:.1f}s...")
            await asyncio.sleep(duration)
            
            # Complete task (95% success rate)
            success = random.random() > 0.05
            self.complete_task(success)
            await self.register_with_dashboard()
            
            # Idle time
            idle_time = random.uniform(2, 8)
            print(f"😴 Idle for {idle_time:.1f}s...")
            await asyncio.sleep(idle_time)

def aggregate_all_agents():
    """Aggregate all custom agent data into main runtime status"""
    cache_dir = Path.home() / ".hero_core" / "cache"
    
    # Read existing runtime status
    runtime_file = cache_dir / "agent_runtime_status.json"
    try:
        with open(runtime_file, 'r') as f:
            runtime_data = json.load(f)
    except FileNotFoundError:
        runtime_data = {
            "timestamp": datetime.now().isoformat(),
            "runtime_stats": {
                "start_time": datetime.now().isoformat(),
                "agents_launched": 0,
                "tasks_processed": 0,
                "messages_handled": 0,
                "uptime_seconds": 0
            },
            "agents": {},
            "nats_connected": True,
            "hero_integration": {
                "coordinator_available": True,
                "bridge_available": True,
                "tracer_available": True
            }
        }
    
    # Find all custom agent files
    custom_agent_files = list(cache_dir.glob("custom_agent_*.json"))
    
    # Merge custom agents into runtime data
    total_tasks = runtime_data["runtime_stats"]["tasks_processed"]
    
    for agent_file in custom_agent_files:
        try:
            with open(agent_file, 'r') as f:
                agent_data = json.load(f)
            
            # Merge agents
            if "agents" in agent_data:
                runtime_data["agents"].update(agent_data["agents"])
                
                # Update runtime stats
                for agent_info in agent_data["agents"].values():
                    total_tasks += agent_info["performance"]["tasks_completed"]
                    
        except Exception as e:
            print(f"Error processing {agent_file}: {e}")
    
    # Update aggregated stats
    runtime_data["timestamp"] = datetime.now().isoformat()
    runtime_data["runtime_stats"]["agents_launched"] = len(runtime_data["agents"])
    runtime_data["runtime_stats"]["tasks_processed"] = total_tasks
    
    # Write back to runtime status
    with open(runtime_file, 'w') as f:
        json.dump(runtime_data, f, indent=2)
    
    print(f"📊 Aggregated {len(custom_agent_files)} custom agents into dashboard")

async def main():
    parser = argparse.ArgumentParser(description="Register custom agent with Hero Dashboard")
    parser.add_argument("--type", default="custom_agent", help="Agent type identifier")
    parser.add_argument("--name", help="Agent name (optional)")
    parser.add_argument("--simulate", action="store_true", help="Simulate agent work")
    parser.add_argument("--aggregate", action="store_true", help="Just aggregate existing agents")
    
    args = parser.parse_args()
    
    if args.aggregate:
        aggregate_all_agents()
        return
    
    # Create and register agent
    agent = CustomAgent(args.type, args.name)
    
    if args.simulate:
        # Run heartbeat and simulation concurrently
        await asyncio.gather(
            agent.send_heartbeat_loop(),
            agent.simulate_work()
        )
    else:
        # Just run heartbeat
        await agent.send_heartbeat_loop()

if __name__ == "__main__":
    print("🚀 Hero Custom Agent Registration")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")