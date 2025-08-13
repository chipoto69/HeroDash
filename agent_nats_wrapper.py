#!/usr/bin/env python3
"""
Agent NATS Wrapper - Real integration for existing agents
Allows real agents (Claude, Amp, etc.) to receive and process tasks via NATS
"""

import asyncio
import json
import logging
import sys
import os
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Callable
import nats
from nats.js import JetStreamContext

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentWrapper")

class AgentNATSWrapper:
    def __init__(self, agent_pid: int, agent_name: str, agent_type: str):
        self.agent_pid = agent_pid
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.nats_url = "nats://localhost:4224"
        self.nc = None
        self.js = None
        self.subscription = None
        self.running = True
        
        # Directories
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.task_dir = Path.home() / ".hero_core" / "tasks" / str(agent_pid)
        self.task_dir.mkdir(parents=True, exist_ok=True)
        
        # Task processing
        self.current_task = None
        self.task_queue = asyncio.Queue()
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        # Queue group based on agent type
        self.queue_groups = {
            "architect": "architects",
            "frontend_developer": "developers",
            "backend_developer": "developers",
            "documentation_specialist": "documentation",
            "implementation_specialist": "architects"
        }
        self.queue_group = self.queue_groups.get(agent_type, "general")
        
    async def connect(self):
        """Connect to NATS and setup subscriptions"""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"✅ Agent {self.agent_name} (PID: {self.agent_pid}) connected to NATS")
            
            # Get JetStream context
            self.js = self.nc.jetstream()
            
            # Subscribe to agent-specific tasks with queue group
            await self.subscribe_to_tasks()
            
            # Subscribe to broadcast messages
            await self.nc.subscribe("hero.agents.broadcast", cb=self.handle_broadcast)
            
            # Subscribe for request-reply pattern
            await self.nc.subscribe(f"hero.agents.{self.agent_pid}", cb=self.handle_request)
            
            # Update status
            await self.update_status("connected", "Waiting for tasks")
            
            logger.info(f"📡 Agent wrapper ready - Queue group: {self.queue_group}")
            
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
            
    async def subscribe_to_tasks(self):
        """Subscribe to task stream with JetStream"""
        # Create durable consumer for this agent
        consumer_name = f"agent-{self.agent_pid}"
        
        try:
            # Try to get existing consumer
            await self.js.consumer_info("HERO_TASKS", consumer_name)
            logger.info(f"Using existing consumer: {consumer_name}")
        except:
            # Create new consumer
            consumer_config = {
                "stream": "HERO_TASKS",
                "durable": consumer_name,
                "ack_policy": "explicit",
                "max_deliver": 3,
                "ack_wait": 30,
                "filter_subject": f"hero.tasks.{self.agent_pid}"
            }
            await self.js.add_consumer(**consumer_config)
            logger.info(f"Created consumer: {consumer_name}")
            
        # Start consuming tasks
        asyncio.create_task(self.consume_tasks(consumer_name))
        
    async def consume_tasks(self, consumer_name: str):
        """Consume tasks from JetStream"""
        try:
            # Create pull subscription
            psub = await self.js.pull_subscribe(f"hero.tasks.{self.agent_pid}", consumer_name)
            
            while self.running:
                try:
                    # Fetch messages (with timeout)
                    msgs = await psub.fetch(batch=1, timeout=1)
                    
                    for msg in msgs:
                        task = json.loads(msg.data.decode())
                        await self.task_queue.put((task, msg))
                        logger.info(f"📥 Received task: {task['task_id']} - {task['description']}")
                        
                except nats.errors.TimeoutError:
                    # No messages available
                    pass
                    
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error consuming tasks: {e}")
            
    async def process_tasks(self):
        """Process tasks from queue"""
        while self.running:
            try:
                # Get task from queue
                task, msg = await asyncio.wait_for(self.task_queue.get(), timeout=1)
                
                # Update status
                self.current_task = task
                await self.update_status("processing", task['description'])
                
                # Save task to file for agent to process
                task_file = self.task_dir / f"{task['task_id']}.json"
                with open(task_file, 'w') as f:
                    json.dump(task, f, indent=2)
                
                # Simulate agent processing (in real implementation, this would trigger the actual agent)
                success = await self.execute_task(task)
                
                if success:
                    # Send acknowledgment
                    await self.send_acknowledgment(task['task_id'], "completed")
                    await msg.ack()
                    self.completed_tasks += 1
                    logger.info(f"✅ Task {task['task_id']} completed")
                else:
                    # Task failed - will be redelivered by JetStream
                    await self.send_acknowledgment(task['task_id'], "failed", "Processing failed")
                    await msg.nak()
                    self.failed_tasks += 1
                    logger.error(f"❌ Task {task['task_id']} failed")
                    
                # Clear current task
                self.current_task = None
                await self.update_status("idle", "Waiting for tasks")
                
            except asyncio.TimeoutError:
                # No tasks available
                pass
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                
    async def execute_task(self, task: Dict) -> bool:
        """Execute the actual task (placeholder for real agent integration)"""
        task_type = task.get('type')
        priority = task.get('priority', 'normal')
        
        # Simulate different processing times based on task type and priority
        if priority == "high":
            await asyncio.sleep(2)
        elif task_type in ["architecture_review", "deployment_preparation"]:
            await asyncio.sleep(5)
        elif task_type in ["frontend_implementation", "backend_optimization"]:
            await asyncio.sleep(4)
        elif task_type == "documentation_update":
            await asyncio.sleep(3)
        else:
            await asyncio.sleep(2)
            
        # Simulate 90% success rate
        import random
        return random.random() > 0.1
        
    async def send_acknowledgment(self, task_id: str, status: str, error: str = None):
        """Send task acknowledgment to coordinator"""
        ack = {
            "task_id": task_id,
            "agent_pid": self.agent_pid,
            "agent_name": self.agent_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            ack["error"] = error
            
        # Publish to results stream
        await self.js.publish("hero.results.ack", json.dumps(ack).encode())
        
    async def handle_broadcast(self, msg):
        """Handle broadcast messages"""
        try:
            data = json.loads(msg.data.decode())
            message = data.get("message", "")
            msg_type = data.get("type", "info")
            
            logger.info(f"📢 Broadcast ({msg_type}): {message}")
            
            # Could trigger specific actions based on message type
            if msg_type == "system" and "shutdown" in message.lower():
                logger.info("Received shutdown signal")
                self.running = False
                
        except Exception as e:
            logger.error(f"Error handling broadcast: {e}")
            
    async def handle_request(self, msg):
        """Handle request-reply messages"""
        try:
            data = json.loads(msg.data.decode())
            action = data.get("action")
            
            if action == "get_status":
                response = {
                    "agent_pid": self.agent_pid,
                    "agent_name": self.agent_name,
                    "status": "processing" if self.current_task else "idle",
                    "current_task": self.current_task['task_id'] if self.current_task else None,
                    "completed_tasks": self.completed_tasks,
                    "failed_tasks": self.failed_tasks,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send reply
                await self.nc.publish(msg.reply, json.dumps(response).encode())
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            
    async def update_status(self, status: str, current_task: Optional[str] = None):
        """Update agent status file"""
        status_data = {
            "agent_pid": self.agent_pid,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "status": status,
            "current_task": current_task,
            "queue_group": self.queue_group,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "last_update": datetime.now().isoformat(),
            "nats_connected": self.nc is not None and not self.nc.is_closed
        }
        
        # Write status file
        status_file = self.cache_dir / f"agent_{self.agent_pid}_wrapper_status.json"
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
    async def heartbeat(self):
        """Send periodic heartbeat"""
        while self.running:
            await self.update_status(
                "processing" if self.current_task else "idle",
                self.current_task['description'] if self.current_task else "Waiting for tasks"
            )
            await asyncio.sleep(5)
            
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down agent wrapper...")
        self.running = False
        
        # Update final status
        await self.update_status("stopped", None)
        
        # Close NATS connection
        if self.nc:
            await self.nc.close()
            logger.info("NATS connection closed")
            
    async def run(self):
        """Main run loop"""
        try:
            # Connect to NATS
            await self.connect()
            
            # Start task processor
            task_processor = asyncio.create_task(self.process_tasks())
            
            # Start heartbeat
            heartbeat_task = asyncio.create_task(self.heartbeat())
            
            logger.info(f"🚀 Agent {self.agent_name} wrapper running...")
            
            # Wait for tasks
            await asyncio.gather(task_processor, heartbeat_task)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
        finally:
            await self.shutdown()

# Agent configurations matching the real PIDs
AGENT_CONFIGS = {
    1181: ("Chimera Lead", "architect"),
    88050: ("Ampcode (FE)", "frontend_developer"),
    57730: ("Ampcode2 (BE)", "backend_developer"),
    89852: ("Documentation", "documentation_specialist"),
    95867: ("Architecture Coder", "implementation_specialist")
}

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python agent_nats_wrapper.py <PID>")
        print(f"Available PIDs: {list(AGENT_CONFIGS.keys())}")
        sys.exit(1)
        
    try:
        agent_pid = int(sys.argv[1])
        if agent_pid not in AGENT_CONFIGS:
            print(f"Unknown PID: {agent_pid}")
            print(f"Available PIDs: {list(AGENT_CONFIGS.keys())}")
            sys.exit(1)
            
        agent_name, agent_type = AGENT_CONFIGS[agent_pid]
        
        # Create and run wrapper
        wrapper = AgentNATSWrapper(agent_pid, agent_name, agent_type)
        
        # Setup signal handlers
        loop = asyncio.new_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(wrapper.shutdown()))
            
        # Run wrapper
        loop.run_until_complete(wrapper.run())
        
    except ValueError:
        print("PID must be a number")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()