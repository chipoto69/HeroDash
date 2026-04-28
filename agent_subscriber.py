#!/usr/bin/env python3
"""
Agent NATS Subscriber - Allows agents to receive and process tasks from NATS
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import nats
from nats.js import JetStreamContext

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentSubscriber")

class AgentSubscriber:
    def __init__(self, agent_pid: int, agent_name: str):
        self.agent_pid = agent_pid
        self.agent_name = agent_name
        self.nats_url = "nats://localhost:4224"
        self.nc = None
        self.js = None
        self.subscription = None
        self.task_dir = Path.home() / ".hero_core" / "tasks" / str(agent_pid)
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = Path.home() / ".hero_core" / "cache" / f"agent_{agent_pid}_status.json"
        self.running = True
        
    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"✅ Agent {self.agent_name} (PID: {self.agent_pid}) connected to NATS")
            
            # Subscribe to agent-specific channel
            subject = f"hero.agents.{self.agent_pid}"
            self.subscription = await self.nc.subscribe(subject, cb=self.handle_task)
            logger.info(f"📡 Subscribed to {subject}")
            
            # Also subscribe to broadcast channel
            broadcast_subject = "hero.agents.broadcast"
            await self.nc.subscribe(broadcast_subject, cb=self.handle_broadcast)
            logger.info(f"📢 Subscribed to broadcast channel")
            
            # Update status
            await self.update_status("connected", "Waiting for tasks")
            
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
            
    async def handle_task(self, msg):
        """Handle incoming task from NATS"""
        try:
            # Parse task
            task_data = json.loads(msg.data.decode())
            task_id = task_data.get("task_id")
            task_type = task_data.get("type")
            description = task_data.get("description")
            
            logger.info(f"📥 Received task {task_id}: {description}")
            
            # Update status
            await self.update_status("processing", f"Working on: {description}")
            
            # Save task to file for processing
            task_file = self.task_dir / f"{task_id}.json"
            with open(task_file, 'w') as f:
                json.dump(task_data, f, indent=2)
            
            # Simulate task processing
            await self.process_task(task_data)
            
            # Send completion acknowledgment
            if msg.reply:
                response = {
                    "task_id": task_id,
                    "agent_pid": self.agent_pid,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                await self.nc.publish(msg.reply, json.dumps(response).encode())
                
            # Update status
            await self.update_status("idle", "Task completed")
            
        except Exception as e:
            logger.error(f"Error handling task: {e}")
            
    async def handle_broadcast(self, msg):
        """Handle broadcast messages"""
        try:
            message = msg.data.decode()
            logger.info(f"📢 Broadcast received: {message}")
            
            # Could trigger specific actions based on broadcast content
            if "coordination" in message.lower():
                await self.update_status("coordinating", "Participating in team coordination")
                
        except Exception as e:
            logger.error(f"Error handling broadcast: {e}")
            
    async def process_task(self, task: Dict):
        """Process the task (simulate work)"""
        task_type = task.get("type")
        
        # Simulate different processing times based on task type
        if task_type == "architecture_review":
            await asyncio.sleep(3)
        elif task_type == "implementation":
            await asyncio.sleep(5)
        elif task_type == "documentation":
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)
            
        logger.info(f"✅ Task {task['task_id']} completed")
        
    async def update_status(self, status: str, current_task: Optional[str] = None):
        """Update agent status file"""
        status_data = {
            "agent_pid": self.agent_pid,
            "agent_name": self.agent_name,
            "status": status,
            "current_task": current_task,
            "last_update": datetime.now().isoformat(),
            "nats_connected": self.nc is not None and not self.nc.is_closed
        }
        
        # Write status file
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
    async def run(self):
        """Main run loop"""
        try:
            await self.connect()
            
            logger.info(f"🚀 Agent {self.agent_name} subscriber running...")
            
            # Keep the subscriber running
            while self.running:
                await asyncio.sleep(1)
                
                # Periodic heartbeat
                if int(datetime.now().timestamp()) % 30 == 0:
                    await self.update_status("idle", "Waiting for tasks")
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if self.nc:
                await self.nc.close()
                logger.info("NATS connection closed")

# Agent configurations
AGENT_CONFIGS = {
    1181: "Chimera Lead",
    88050: "Ampcode (FE)",
    57730: "Ampcode2 (BE)",
    89852: "Documentation",
    95867: "Architecture Coder"
}

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python agent_subscriber.py <PID>")
        print(f"Available PIDs: {list(AGENT_CONFIGS.keys())}")
        sys.exit(1)
        
    try:
        agent_pid = int(sys.argv[1])
        if agent_pid not in AGENT_CONFIGS:
            print(f"Unknown PID: {agent_pid}")
            print(f"Available PIDs: {list(AGENT_CONFIGS.keys())}")
            sys.exit(1)
            
        agent_name = AGENT_CONFIGS[agent_pid]
        
        # Create and run subscriber
        subscriber = AgentSubscriber(agent_pid, agent_name)
        asyncio.run(subscriber.run())
        
    except ValueError:
        print("PID must be a number")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()