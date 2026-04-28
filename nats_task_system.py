#!/usr/bin/env python3
"""
Real NATS-based Task Distribution System for Hero Command Centre
Uses NATS messaging to distribute tasks to actual agents
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# NATS client library
try:
    import nats
    from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
except ImportError:
    print("Installing NATS client library...")
    import subprocess
    subprocess.check_call(["pip3", "install", "nats-py"])
    import nats
    from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NATSTaskSystem")

class NATSTaskManager:
    def __init__(self, nats_url: str = "nats://localhost:4224"):
        self.nats_url = nats_url
        self.nc = None  # NATS connection
        self.js = None  # JetStream context
        
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Real agent configuration
        self.agents = {
            "agent_1181": {
                "pid": 1181,
                "name": "Chimera Lead",
                "role": "Project Lead & Architecture",
                "subject": "hero.agents.1181",
                "capabilities": ["system_design", "architecture", "leadership"]
            },
            "agent_88050": {
                "pid": 88050,
                "name": "Ampcode (FE)",
                "role": "Frontend Development",
                "subject": "hero.agents.88050",
                "capabilities": ["frontend", "react", "ui"]
            },
            "agent_57730": {
                "pid": 57730,
                "name": "Ampcode2 (BE)",
                "role": "Backend Development",
                "subject": "hero.agents.57730",
                "capabilities": ["backend", "api", "database"]
            },
            "agent_89852": {
                "pid": 89852,
                "name": "Documentation",
                "role": "Documentation & Coordination",
                "subject": "hero.agents.89852",
                "capabilities": ["documentation", "coordination"]
            },
            "agent_95867": {
                "pid": 95867,
                "name": "Architecture Coder",
                "role": "Implementation Specialist",
                "subject": "hero.agents.95867",
                "capabilities": ["implementation", "integration"]
            }
        }
        
        self.active_tasks = {}
        self.completed_tasks = []
        
    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"✅ Connected to NATS at {self.nats_url}")
            
            # Try to get JetStream context (may not be available)
            try:
                self.js = self.nc.jetstream()
                logger.info("✅ JetStream available")
            except:
                logger.info("⚠️ JetStream not available, using core NATS")
            
            # Subscribe to task responses
            await self.nc.subscribe("hero.tasks.response", cb=self.handle_task_response)
            await self.nc.subscribe("hero.agents.heartbeat", cb=self.handle_heartbeat)
            
            # Announce presence
            await self.nc.publish("hero.orchestrator.online", 
                                json.dumps({"status": "online", "timestamp": datetime.now().isoformat()}).encode())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to NATS: {e}")
            return False
    
    async def create_task(self, agent_id: str, task_type: str, 
                         description: str, data: Dict = None) -> str:
        """Create and send a task to an agent via NATS"""
        if not self.nc:
            logger.error("Not connected to NATS")
            return None
            
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        
        task = {
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "description": description,
            "data": data or {},
            "status": "pending",
            "created": timestamp,
            "timeout": 300  # 5 minute timeout
        }
        
        # Send task to agent's subject
        agent = self.agents.get(agent_id)
        if not agent:
            logger.error(f"Unknown agent: {agent_id}")
            return None
            
        try:
            # Publish task to agent's channel
            await self.nc.publish(agent["subject"], json.dumps(task).encode())
            
            # Also broadcast to general task channel
            await self.nc.publish("hero.tasks.created", json.dumps({
                "task_id": task_id,
                "agent_id": agent_id,
                "description": description,
                "timestamp": timestamp
            }).encode())
            
            self.active_tasks[task_id] = task
            logger.info(f"📨 Sent task {task_id} to {agent['name']} via NATS")
            
            # Update dashboard cache
            await self.update_dashboard()
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to send task: {e}")
            return None
    
    async def handle_task_response(self, msg):
        """Handle task completion responses from agents"""
        try:
            response = json.loads(msg.data.decode())
            task_id = response.get("task_id")
            
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task["status"] = response.get("status", "completed")
                task["result"] = response.get("result", {})
                task["completed"] = datetime.now().isoformat()
                
                # Move to completed
                self.completed_tasks.append(task)
                del self.active_tasks[task_id]
                
                logger.info(f"✅ Task {task_id} completed: {response.get('status')}")
                
                # Update dashboard
                await self.update_dashboard()
                
        except Exception as e:
            logger.error(f"Error handling task response: {e}")
    
    async def handle_heartbeat(self, msg):
        """Handle agent heartbeats"""
        try:
            heartbeat = json.loads(msg.data.decode())
            agent_id = heartbeat.get("agent_id")
            
            if agent_id in self.agents:
                self.agents[agent_id]["last_heartbeat"] = datetime.now().isoformat()
                self.agents[agent_id]["status"] = heartbeat.get("status", "active")
                
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
    async def broadcast_coordination_message(self, message: str):
        """Broadcast a coordination message to all agents"""
        if not self.nc:
            return
            
        try:
            await self.nc.publish("hero.coordination", json.dumps({
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "from": "orchestrator"
            }).encode())
            
            logger.info(f"📢 Broadcast: {message}")
            
        except Exception as e:
            logger.error(f"Failed to broadcast: {e}")
    
    async def update_dashboard(self):
        """Update dashboard cache with real NATS status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "nats_connected": self.nc is not None and not self.nc.is_closed,
            "nats_url": self.nats_url,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "agents": {}
        }
        
        for agent_id, agent in self.agents.items():
            status["agents"][agent_id] = {
                "pid": agent["pid"],
                "name": agent["name"],
                "role": agent["role"],
                "subject": agent["subject"],
                "status": agent.get("status", "unknown"),
                "last_heartbeat": agent.get("last_heartbeat", "never")
            }
        
        # Write to cache
        cache_file = self.cache_dir / "nats_status.json"
        with open(cache_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    async def run_demo(self):
        """Run a demo showing real NATS task distribution"""
        # Connect to NATS
        if not await self.connect():
            logger.error("Could not connect to NATS")
            return
            
        logger.info("🚀 NATS Task System Online")
        logger.info(f"📡 Connected to {self.nats_url}")
        logger.info(f"👥 Managing {len(self.agents)} agents")
        
        # Send initial coordination message
        await self.broadcast_coordination_message("Task system online. Ready for coordination.")
        
        # Create some real tasks
        tasks = [
            ("agent_1181", "architecture_review", "Review system architecture for Chimera project"),
            ("agent_88050", "frontend_development", "Build React components for dashboard"),
            ("agent_57730", "backend_api", "Create REST API endpoints"),
            ("agent_89852", "documentation", "Document the new architecture"),
            ("agent_95867", "integration", "Integrate all components")
        ]
        
        for agent_id, task_type, description in tasks:
            task_id = await self.create_task(agent_id, task_type, description)
            if task_id:
                logger.info(f"Created task: {task_id}")
            await asyncio.sleep(1)
        
        # Monitor for 30 seconds
        logger.info("\n📊 Monitoring task execution...")
        for i in range(6):
            await asyncio.sleep(5)
            logger.info(f"Status: {len(self.active_tasks)} active, {len(self.completed_tasks)} completed")
        
        # Cleanup
        await self.nc.close()
        logger.info("✅ NATS connection closed")

async def main():
    """Main entry point"""
    manager = NATSTaskManager()
    await manager.run_demo()

if __name__ == "__main__":
    asyncio.run(main())