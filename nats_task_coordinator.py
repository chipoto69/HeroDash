#!/usr/bin/env python3
"""
NATS Task Coordinator with JetStream
Production-ready task distribution system using NATS JetStream for persistence and reliability
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import nats
from nats.js import JetStreamContext
from nats.errors import TimeoutError as NATSTimeoutError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NATSTaskCoordinator")

class NATSTaskCoordinator:
    def __init__(self):
        self.nats_url = "nats://localhost:4224"
        self.nc = None
        self.js = None
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent configurations
        self.agents = {
            1181: {
                "name": "Chimera Lead",
                "type": "architect",
                "subject": "hero.agents.1181",
                "queue_group": "architects",
                "capabilities": ["system_design", "feature_planning", "architecture_decisions"]
            },
            88050: {
                "name": "Ampcode (FE)",
                "type": "frontend_developer",
                "subject": "hero.agents.88050",
                "queue_group": "developers",
                "capabilities": ["rapid_coding", "feature_implementation", "performance_optimization"]
            },
            57730: {
                "name": "Ampcode2 (BE)",
                "type": "backend_developer",
                "subject": "hero.agents.57730",
                "queue_group": "developers",
                "capabilities": ["code_review", "bug_fixes", "testing", "refactoring"]
            },
            89852: {
                "name": "Documentation",
                "type": "documentation_specialist",
                "subject": "hero.agents.89852",
                "queue_group": "documentation",
                "capabilities": ["documentation", "project_coordination", "architectural_docs"]
            },
            95867: {
                "name": "Architecture Coder",
                "type": "implementation_specialist",
                "subject": "hero.agents.95867",
                "queue_group": "architects",
                "capabilities": ["architecture_implementation", "system_integration", "deployment"]
            }
        }
        
        # Task tracking
        self.active_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}
        self.task_retries = {}
        
    async def connect(self):
        """Connect to NATS and initialize JetStream"""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"✅ Connected to NATS at {self.nats_url}")
            
            # Get JetStream context
            self.js = self.nc.jetstream()
            
            # Create streams for different task types
            await self.setup_streams()
            
            # Setup consumers for task acknowledgments
            await self.setup_consumers()
            
            # Update status
            await self.update_status("connected")
            
            logger.info("🚀 NATS Task Coordinator with JetStream ready")
            
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
            
    async def setup_streams(self):
        """Setup JetStream streams for task persistence"""
        # Task stream configuration
        stream_config = {
            "name": "HERO_TASKS",
            "subjects": ["hero.tasks.>"],
            "retention": "work_queue",  # Work queue for task distribution
            "max_consumers": -1,
            "max_msgs": 10000,
            "max_age": 86400,  # 24 hours
            "storage": "file",
            "num_replicas": 1,
            "discard": "old",
            "duplicate_window": 120  # 2 minutes deduplication
        }
        
        try:
            # Try to get existing stream
            stream = await self.js.stream_info("HERO_TASKS")
            logger.info(f"Using existing stream: HERO_TASKS")
        except:
            # Create new stream
            await self.js.add_stream(**stream_config)
            logger.info(f"Created new stream: HERO_TASKS")
            
        # Create stream for task results
        result_stream_config = {
            "name": "HERO_RESULTS",
            "subjects": ["hero.results.>"],
            "retention": "limits",
            "max_msgs": 10000,
            "max_age": 3600,  # 1 hour
            "storage": "memory",
            "num_replicas": 1
        }
        
        try:
            await self.js.stream_info("HERO_RESULTS")
            logger.info(f"Using existing stream: HERO_RESULTS")
        except:
            await self.js.add_stream(**result_stream_config)
            logger.info(f"Created new stream: HERO_RESULTS")
            
    async def setup_consumers(self):
        """Setup durable consumers for task processing"""
        # Create pull consumer for task acknowledgments
        consumer_config = {
            "stream": "HERO_RESULTS",
            "durable": "task-coordinator",
            "ack_policy": "explicit",
            "max_deliver": 3,
            "ack_wait": 30,
            "filter_subject": "hero.results.ack"
        }
        
        try:
            await self.js.consumer_info("HERO_RESULTS", "task-coordinator")
            logger.info("Using existing consumer: task-coordinator")
        except:
            await self.js.add_consumer(**consumer_config)
            logger.info("Created consumer: task-coordinator")
            
        # Start consuming acknowledgments
        asyncio.create_task(self.consume_acknowledgments())
        
    async def consume_acknowledgments(self):
        """Consume task acknowledgments from agents"""
        try:
            # Create pull subscription
            psub = await self.js.pull_subscribe("hero.results.ack", "task-coordinator")
            
            while True:
                try:
                    # Fetch messages (with timeout)
                    msgs = await psub.fetch(batch=10, timeout=1)
                    
                    for msg in msgs:
                        await self.handle_acknowledgment(msg)
                        await msg.ack()
                        
                except NATSTimeoutError:
                    # No messages available, continue
                    pass
                    
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error consuming acknowledgments: {e}")
            
    async def handle_acknowledgment(self, msg):
        """Handle task acknowledgment from agent"""
        try:
            data = json.loads(msg.data.decode())
            task_id = data.get("task_id")
            status = data.get("status")
            agent_pid = data.get("agent_pid")
            
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task["status"] = status
                task["completed_at"] = datetime.now().isoformat()
                task["completed_by"] = agent_pid
                
                if status == "completed":
                    self.completed_tasks[task_id] = task
                    del self.active_tasks[task_id]
                    logger.info(f"✅ Task {task_id} completed by agent {agent_pid}")
                elif status == "failed":
                    await self.handle_task_failure(task_id, task, data.get("error"))
                    
        except Exception as e:
            logger.error(f"Error handling acknowledgment: {e}")
            
    async def handle_task_failure(self, task_id: str, task: Dict, error: str = None):
        """Handle task failure with retry logic"""
        retry_count = self.task_retries.get(task_id, 0)
        max_retries = 3
        
        if retry_count < max_retries:
            # Retry task with exponential backoff
            self.task_retries[task_id] = retry_count + 1
            delay = 2 ** retry_count  # Exponential backoff
            
            logger.warning(f"Task {task_id} failed, retrying in {delay}s (attempt {retry_count + 1}/{max_retries})")
            await asyncio.sleep(delay)
            
            # Re-publish task
            await self.republish_task(task)
        else:
            # Move to failed tasks
            task["error"] = error
            task["failed_at"] = datetime.now().isoformat()
            self.failed_tasks[task_id] = task
            del self.active_tasks[task_id]
            logger.error(f"❌ Task {task_id} failed after {max_retries} retries")
            
    async def republish_task(self, task: Dict):
        """Republish a failed task"""
        try:
            agent_pid = task["agent_pid"]
            subject = f"hero.tasks.{agent_pid}"
            
            # Publish with JetStream for persistence
            ack = await self.js.publish(subject, json.dumps(task).encode())
            logger.info(f"🔄 Republished task {task['task_id']} to {subject}")
            
        except Exception as e:
            logger.error(f"Error republishing task: {e}")
            
    async def create_task(self, agent_pid: int, task_type: str, description: str,
                         priority: str = "normal", data: Dict = None) -> str:
        """Create and publish a task with JetStream persistence"""
        if agent_pid not in self.agents:
            raise ValueError(f"Unknown agent PID: {agent_pid}")
            
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        agent = self.agents[agent_pid]
        
        task = {
            "task_id": task_id,
            "agent_pid": agent_pid,
            "agent_name": agent["name"],
            "type": task_type,
            "description": description,
            "priority": priority,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "queue_group": agent["queue_group"]
        }
        
        # Store task
        self.active_tasks[task_id] = task
        
        # Publish to JetStream
        subject = f"hero.tasks.{agent_pid}"
        
        try:
            # Publish with message ID for deduplication
            ack = await self.js.publish(
                subject,
                json.dumps(task).encode(),
                headers={
                    "Nats-Msg-Id": task_id
                }
            )
            
            logger.info(f"📨 Task {task_id} published to {agent['name']} via JetStream")
            logger.info(f"   Stream: {ack.stream}, Seq: {ack.seq}")
            
        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
            del self.active_tasks[task_id]
            raise
            
        return task_id
        
    async def broadcast_message(self, message: str, msg_type: str = "info"):
        """Broadcast message to all agents"""
        broadcast_msg = {
            "type": msg_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Publish to broadcast subject
        await self.nc.publish("hero.agents.broadcast", json.dumps(broadcast_msg).encode())
        logger.info(f"📢 Broadcast: {message}")
        
    async def request_reply(self, agent_pid: int, request: Dict, timeout: float = 5.0) -> Optional[Dict]:
        """Send request and wait for reply (request-reply pattern)"""
        if agent_pid not in self.agents:
            return None
            
        agent = self.agents[agent_pid]
        subject = agent["subject"]
        
        try:
            # Send request and wait for reply
            response = await self.nc.request(
                subject,
                json.dumps(request).encode(),
                timeout=timeout
            )
            
            return json.loads(response.data.decode())
            
        except NATSTimeoutError:
            logger.warning(f"Request to {agent['name']} timed out")
            return None
        except Exception as e:
            logger.error(f"Error in request-reply: {e}")
            return None
            
    async def get_agent_status(self, agent_pid: int) -> Optional[Dict]:
        """Get status from specific agent using request-reply"""
        request = {
            "action": "get_status",
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.request_reply(agent_pid, request)
        
    async def update_status(self, status: str):
        """Update coordinator status"""
        status_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "nats_connected": self.nc is not None and not self.nc.is_closed,
            "jetstream_enabled": self.js is not None,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "agents": list(self.agents.keys()),
            "streams": ["HERO_TASKS", "HERO_RESULTS"]
        }
        
        status_file = self.cache_dir / "nats_coordinator_status.json"
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
            
    async def get_stream_info(self):
        """Get information about JetStream streams"""
        try:
            tasks_info = await self.js.stream_info("HERO_TASKS")
            results_info = await self.js.stream_info("HERO_RESULTS")
            
            return {
                "tasks_stream": {
                    "messages": tasks_info.state.messages,
                    "bytes": tasks_info.state.bytes,
                    "consumers": tasks_info.state.consumer_count
                },
                "results_stream": {
                    "messages": results_info.state.messages,
                    "bytes": results_info.state.bytes,
                    "consumers": results_info.state.consumer_count
                }
            }
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            return None
            
    async def run(self):
        """Main run loop"""
        try:
            await self.connect()
            
            # Send initial broadcast
            await self.broadcast_message("Task Coordinator online with JetStream", "system")
            
            # Create initial tasks for testing
            logger.info("Creating initial tasks...")
            
            tasks = [
                (1181, "architecture_review", "Review system architecture for scalability", "high"),
                (88050, "frontend_implementation", "Implement new dashboard components", "normal"),
                (57730, "backend_optimization", "Optimize database queries", "normal"),
                (89852, "documentation_update", "Update API documentation", "low"),
                (95867, "deployment_preparation", "Prepare deployment scripts", "normal")
            ]
            
            for agent_pid, task_type, description, priority in tasks:
                task_id = await self.create_task(agent_pid, task_type, description, priority)
                await asyncio.sleep(0.5)  # Small delay between tasks
                
            # Monitor loop
            while True:
                # Update status periodically
                await self.update_status("running")
                
                # Get stream info
                stream_info = await self.get_stream_info()
                if stream_info:
                    logger.info(f"📊 Streams - Tasks: {stream_info['tasks_stream']['messages']} msgs, "
                              f"Results: {stream_info['results_stream']['messages']} msgs")
                
                logger.info(f"📈 Status - Active: {len(self.active_tasks)}, "
                          f"Completed: {len(self.completed_tasks)}, "
                          f"Failed: {len(self.failed_tasks)}")
                
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if self.nc:
                await self.nc.close()
                logger.info("NATS connection closed")

def main():
    """Main entry point"""
    coordinator = NATSTaskCoordinator()
    asyncio.run(coordinator.run())

if __name__ == "__main__":
    main()