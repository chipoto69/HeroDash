#!/usr/bin/env python3
"""
Advanced NATS Inter-Agentic Communication Layer for Hero Dashboard
Handles task distribution, synchronization, load balancing, and agent coordination
"""
import asyncio
import json
import time
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
import signal

try:
    import nats
    from nats.js import JetStreamContext
    from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
except ImportError:
    print("Installing NATS client library...")
    import subprocess
    subprocess.check_call(["pip3", "install", "nats-py"])
    import nats
    from nats.js import JetStreamContext
    from nats.errors import ConnectionClosedError, TimeoutError, NoServersError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".hero_core" / "communication.log")
    ]
)
logger = logging.getLogger("InterAgentCommunication")

class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class AgentStatus(Enum):
    ONLINE = "online"
    BUSY = "busy"
    IDLE = "idle"
    OFFLINE = "offline"
    DEGRADED = "degraded"

@dataclass
class Task:
    task_id: str
    task_type: str
    description: str
    data: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: str
    timeout: int
    dependencies: List[str]
    assigned_agent: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class Agent:
    agent_id: str
    agent_type: str
    name: str
    capabilities: List[str]
    status: AgentStatus
    current_tasks: List[str]
    max_concurrent_tasks: int
    last_heartbeat: str
    performance_score: float
    load_factor: float
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0

@dataclass
class SyncPoint:
    sync_id: str
    required_agents: Set[str]
    completed_agents: Set[str]
    timeout: datetime
    data: Dict[str, Any]

class InterAgentCommunicationLayer:
    """Advanced NATS-based communication layer for multi-agent coordination"""
    
    def __init__(self, nats_url: str = "nats://localhost:4224", environment: str = "dev"):
        self.nats_url = nats_url
        self.environment = environment
        self.nc = None
        self.js = None
        
        # Core state management
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.sync_points: Dict[str, SyncPoint] = {}
        self.task_queues: Dict[TaskPriority, deque] = {
            TaskPriority.CRITICAL: deque(),
            TaskPriority.HIGH: deque(),
            TaskPriority.MEDIUM: deque(),
            TaskPriority.LOW: deque()
        }
        
        # Coordination state
        self.running = False
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "tasks_distributed": 0,
            "sync_operations": 0,
            "agent_registrations": 0,
            "load_balancing_operations": 0
        }
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
    async def initialize(self) -> bool:
        """Initialize the communication layer"""
        try:
            # Connect to NATS
            self.nc = await nats.connect(
                self.nats_url,
                error_cb=self._error_callback,
                disconnected_cb=self._disconnected_callback,
                reconnected_cb=self._reconnected_callback
            )
            
            # Initialize JetStream
            self.js = self.nc.jetstream()
            
            # Setup streams
            await self._setup_streams()
            
            # Setup core subscriptions
            await self._setup_subscriptions()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.running = True
            logger.info(f"✅ Inter-agent communication layer initialized on {self.nats_url}")
            
            # Announce orchestrator online
            await self._publish_system_event("orchestrator_online", {
                "environment": self.environment,
                "capabilities": ["task_distribution", "load_balancing", "synchronization"]
            })
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize communication layer: {e}")
            return False
    
    async def _setup_streams(self):
        """Setup JetStream streams for different message types"""
        streams = [
            {
                "name": f"HERO_TASKS_{self.environment.upper()}",
                "subjects": [f"hero.v1.{self.environment}.tasks.>"],
                "retention": "WorkQueue",
                "max_msgs": 10000,
                "max_age": 24 * 60 * 60  # 24 hours in seconds
            },
            {
                "name": f"HERO_EVENTS_{self.environment.upper()}",
                "subjects": [f"hero.v1.{self.environment}.events.>"],
                "retention": "Limits",
                "max_msgs": 50000,
                "max_age": 7 * 24 * 60 * 60  # 7 days
            },
            {
                "name": f"HERO_SYNC_{self.environment.upper()}",
                "subjects": [f"hero.v1.{self.environment}.sync.>"],
                "retention": "Limits",
                "max_msgs": 5000,
                "max_age": 60 * 60  # 1 hour
            },
            {
                "name": f"HERO_COORDINATION_{self.environment.upper()}",
                "subjects": [f"hero.v1.{self.environment}.coordination.>"],
                "retention": "Limits",
                "max_msgs": 25000,
                "max_age": 2 * 24 * 60 * 60  # 2 days
            }
        ]
        
        for stream_config in streams:
            try:
                # Try to get existing stream
                try:
                    await self.js.stream_info(stream_config["name"])
                except:
                    # Create new stream
                    await self.js.add_stream(
                        name=stream_config["name"],
                        subjects=stream_config["subjects"],
                        retention=stream_config["retention"],
                        max_msgs=stream_config["max_msgs"],
                        max_age=stream_config["max_age"]
                    )
                    logger.info(f"✅ Created stream: {stream_config['name']}")
                    
            except Exception as e:
                logger.error(f"Failed to setup stream {stream_config['name']}: {e}")
    
    async def _setup_subscriptions(self):
        """Setup core message subscriptions"""
        env = self.environment
        
        # Agent management subscriptions
        await self.nc.subscribe(f"hero.v1.{env}.agents.register", cb=self._handle_agent_registration)
        await self.nc.subscribe(f"hero.v1.{env}.agents.heartbeat", cb=self._handle_agent_heartbeat)
        await self.nc.subscribe(f"hero.v1.{env}.agents.status", cb=self._handle_agent_status)
        
        # Task management subscriptions
        await self.nc.subscribe(f"hero.v1.{env}.tasks.response", cb=self._handle_task_response)
        await self.nc.subscribe(f"hero.v1.{env}.tasks.request", cb=self._handle_task_request)
        
        # Synchronization subscriptions
        await self.nc.subscribe(f"hero.v1.{env}.sync.checkpoint", cb=self._handle_sync_checkpoint)
        await self.nc.subscribe(f"hero.v1.{env}.sync.barrier", cb=self._handle_sync_barrier)
        
        # Coordination subscriptions
        await self.nc.subscribe(f"hero.v1.{env}.coordination.*", cb=self._handle_coordination_message)
        
        logger.info(f"✅ Core subscriptions established for environment: {env}")
    
    async def _start_background_tasks(self):
        """Start background coordination tasks"""
        tasks = [
            self._task_scheduler(),
            self._load_balancer(),
            self._health_monitor(),
            self._metrics_collector(),
            self._cleanup_handler()
        ]
        
        for task in tasks:
            background_task = asyncio.create_task(task)
            self._background_tasks.add(background_task)
            background_task.add_done_callback(self._background_tasks.discard)
    
    # Agent Management
    async def register_agent(self, agent: Agent) -> bool:
        """Register an agent with the communication layer"""
        try:
            # Store agent locally
            self.agents[agent.agent_id] = agent
            self.metrics["agent_registrations"] += 1
            
            # Publish registration event
            await self._publish_event("agent_registered", {
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
                "capabilities": agent.capabilities,
                "max_concurrent_tasks": agent.max_concurrent_tasks
            })
            
            logger.info(f"✅ Registered agent: {agent.name} ({agent.agent_id})")
            await self._update_dashboard_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus, data: Dict = None):
        """Update agent status"""
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].last_heartbeat = datetime.now().isoformat()
            
            await self._publish_event("agent_status_updated", {
                "agent_id": agent_id,
                "status": status.value,
                "data": data or {}
            })
    
    # Task Distribution System
    async def create_task(self, task_type: str, description: str, data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM, 
                         dependencies: List[str] = None, timeout: int = 300) -> str:
        """Create a new task for distribution"""
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            data=data,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            timeout=timeout,
            dependencies=dependencies or [],
        )
        
        # Store task
        self.tasks[task_id] = task
        
        # Queue for processing
        self.task_queues[priority].append(task_id)
        
        # Publish task created event
        await self._publish_event("task_created", {
            "task_id": task_id,
            "task_type": task_type,
            "priority": priority.value,
            "dependencies": dependencies or []
        })
        
        logger.info(f"📋 Created task {task_id}: {description}")
        self.metrics["tasks_distributed"] += 1
        
        return task_id
    
    async def assign_task(self, task_id: str, agent_id: str = None) -> bool:
        """Assign task to specific agent or best available agent"""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        
        # Find best agent if not specified
        if not agent_id:
            agent_id = await self._find_best_agent_for_task(task)
            if not agent_id:
                logger.warning(f"No suitable agent found for task {task_id}")
                return False
        
        # Check if agent exists and is available
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return False
        
        agent = self.agents[agent_id]
        if len(agent.current_tasks) >= agent.max_concurrent_tasks:
            logger.warning(f"Agent {agent_id} is at capacity")
            return False
        
        # Assign task
        task.assigned_agent = agent_id
        task.status = TaskStatus.ASSIGNED
        agent.current_tasks.append(task_id)
        
        # Send task to agent
        await self.nc.publish(
            f"hero.v1.{self.environment}.agents.{agent_id}.tasks.assign",
            json.dumps(asdict(task)).encode()
        )
        
        # Publish assignment event
        await self._publish_event("task_assigned", {
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task.task_type
        })
        
        logger.info(f"📨 Assigned task {task_id} to agent {agent.name}")
        return True
    
    async def _find_best_agent_for_task(self, task: Task) -> Optional[str]:
        """Find the best available agent for a task using load balancing"""
        suitable_agents = []
        
        for agent_id, agent in self.agents.items():
            # Check if agent is online and not at capacity
            if (agent.status in [AgentStatus.ONLINE, AgentStatus.IDLE] and 
                len(agent.current_tasks) < agent.max_concurrent_tasks):
                
                # Check if agent has required capabilities
                if any(capability in agent.capabilities for capability in [task.task_type, "general"]):
                    load_score = len(agent.current_tasks) / agent.max_concurrent_tasks
                    performance_score = agent.performance_score
                    
                    # Combined score (lower is better for load, higher is better for performance)
                    score = load_score - (performance_score * 0.3)
                    suitable_agents.append((agent_id, score))
        
        if not suitable_agents:
            return None
        
        # Return agent with best score
        suitable_agents.sort(key=lambda x: x[1])
        return suitable_agents[0][0]
    
    # Synchronization System
    async def create_sync_point(self, sync_id: str, required_agents: Set[str], 
                              timeout_seconds: int = 30, data: Dict = None) -> bool:
        """Create a synchronization point for agent coordination"""
        
        timeout_time = datetime.now() + timedelta(seconds=timeout_seconds)
        
        sync_point = SyncPoint(
            sync_id=sync_id,
            required_agents=required_agents,
            completed_agents=set(),
            timeout=timeout_time,
            data=data or {}
        )
        
        self.sync_points[sync_id] = sync_point
        
        # Notify required agents
        for agent_id in required_agents:
            await self.nc.publish(
                f"hero.v1.{self.environment}.agents.{agent_id}.sync.checkpoint",
                json.dumps({
                    "sync_id": sync_id,
                    "timeout": timeout_time.isoformat(),
                    "data": data or {}
                }).encode()
            )
        
        logger.info(f"🔄 Created sync point {sync_id} for {len(required_agents)} agents")
        self.metrics["sync_operations"] += 1
        
        return True
    
    async def agent_sync_complete(self, sync_id: str, agent_id: str, data: Dict = None) -> bool:
        """Mark agent as completed for sync point"""
        if sync_id not in self.sync_points:
            return False
        
        sync_point = self.sync_points[sync_id]
        
        if agent_id in sync_point.required_agents:
            sync_point.completed_agents.add(agent_id)
            
            # Update sync point data
            if data:
                sync_point.data[agent_id] = data
            
            # Check if all agents completed
            if sync_point.completed_agents == sync_point.required_agents:
                await self._complete_sync_point(sync_id)
                return True
        
        return False
    
    async def _complete_sync_point(self, sync_id: str):
        """Complete synchronization point"""
        sync_point = self.sync_points[sync_id]
        
        # Notify all agents sync is complete
        for agent_id in sync_point.required_agents:
            await self.nc.publish(
                f"hero.v1.{self.environment}.agents.{agent_id}.sync.complete",
                json.dumps({
                    "sync_id": sync_id,
                    "data": sync_point.data
                }).encode()
            )
        
        # Clean up
        del self.sync_points[sync_id]
        
        logger.info(f"✅ Sync point {sync_id} completed successfully")
    
    # Event Handlers
    async def _handle_agent_registration(self, msg):
        """Handle agent registration messages"""
        try:
            data = json.loads(msg.data.decode())
            
            agent = Agent(
                agent_id=data["agent_id"],
                agent_type=data["agent_type"],
                name=data.get("name", data["agent_id"]),
                capabilities=data.get("capabilities", []),
                status=AgentStatus.ONLINE,
                current_tasks=[],
                max_concurrent_tasks=data.get("max_concurrent_tasks", 5),
                last_heartbeat=datetime.now().isoformat(),
                performance_score=1.0,
                load_factor=0.0
            )
            
            await self.register_agent(agent)
            
        except Exception as e:
            logger.error(f"Error handling agent registration: {e}")
    
    async def _handle_agent_heartbeat(self, msg):
        """Handle agent heartbeat messages"""
        try:
            data = json.loads(msg.data.decode())
            agent_id = data["agent_id"]
            
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = datetime.now().isoformat()
                self.agents[agent_id].status = AgentStatus(data.get("status", "online"))
                
                # Update performance metrics if provided
                if "metrics" in data:
                    metrics = data["metrics"]
                    agent = self.agents[agent_id]
                    if "completed_tasks" in metrics:
                        agent.completed_tasks = metrics["completed_tasks"]
                    if "failed_tasks" in metrics:
                        agent.failed_tasks = metrics["failed_tasks"]
                    
                    # Calculate performance score
                    total = agent.completed_tasks + agent.failed_tasks
                    if total > 0:
                        agent.performance_score = agent.completed_tasks / total
                
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
    async def _handle_task_response(self, msg):
        """Handle task completion responses"""
        try:
            data = json.loads(msg.data.decode())
            task_id = data["task_id"]
            agent_id = data["agent_id"]
            
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus(data["status"])
                task.completed_at = datetime.now().isoformat()
                task.result = data.get("result", {})
                
                # Update agent state
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    if task_id in agent.current_tasks:
                        agent.current_tasks.remove(task_id)
                    
                    if task.status == TaskStatus.COMPLETED:
                        agent.completed_tasks += 1
                        agent.total_tasks += 1
                    elif task.status == TaskStatus.FAILED:
                        agent.failed_tasks += 1
                        agent.total_tasks += 1
                
                # Publish task completion event
                await self._publish_event("task_completed", {
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "status": task.status.value,
                    "duration": self._calculate_task_duration(task)
                })
                
                logger.info(f"✅ Task {task_id} completed by {agent_id}: {task.status.value}")
                
        except Exception as e:
            logger.error(f"Error handling task response: {e}")
    
    async def _handle_sync_checkpoint(self, msg):
        """Handle sync checkpoint messages from agents"""
        try:
            data = json.loads(msg.data.decode())
            await self.agent_sync_complete(
                data["sync_id"],
                data["agent_id"],
                data.get("data", {})
            )
        except Exception as e:
            logger.error(f"Error handling sync checkpoint: {e}")
    
    # Background Tasks
    async def _task_scheduler(self):
        """Background task scheduler"""
        while self.running:
            try:
                # Process tasks by priority
                for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
                    queue = self.task_queues[priority]
                    
                    while queue and self.running:
                        task_id = queue.popleft()
                        if task_id in self.tasks:
                            task = self.tasks[task_id]
                            
                            # Check dependencies
                            if await self._check_task_dependencies(task):
                                await self.assign_task(task_id)
                            else:
                                # Re-queue task
                                queue.append(task_id)
                                break
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in task scheduler: {e}")
                await asyncio.sleep(5)
    
    async def _load_balancer(self):
        """Background load balancing"""
        while self.running:
            try:
                # Calculate load metrics
                total_load = 0
                agent_loads = {}
                
                for agent_id, agent in self.agents.items():
                    if agent.status in [AgentStatus.ONLINE, AgentStatus.BUSY, AgentStatus.IDLE]:
                        load = len(agent.current_tasks) / agent.max_concurrent_tasks
                        agent_loads[agent_id] = load
                        total_load += load
                
                if len(agent_loads) > 1:
                    avg_load = total_load / len(agent_loads)
                    
                    # Find overloaded and underloaded agents
                    overloaded = [(aid, load) for aid, load in agent_loads.items() if load > avg_load + 0.2]
                    underloaded = [(aid, load) for aid, load in agent_loads.items() if load < avg_load - 0.2]
                    
                    # Rebalance if needed
                    if overloaded and underloaded:
                        await self._rebalance_tasks(overloaded, underloaded)
                
                self.metrics["load_balancing_operations"] += 1
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in load balancer: {e}")
                await asyncio.sleep(60)
    
    async def _health_monitor(self):
        """Background health monitoring"""
        while self.running:
            try:
                current_time = datetime.now()
                stale_agents = []
                
                for agent_id, agent in self.agents.items():
                    # Check if agent heartbeat is stale (>60 seconds)
                    last_heartbeat = datetime.fromisoformat(agent.last_heartbeat)
                    if (current_time - last_heartbeat).total_seconds() > 60:
                        stale_agents.append(agent_id)
                
                # Mark stale agents as offline
                for agent_id in stale_agents:
                    await self.update_agent_status(agent_id, AgentStatus.OFFLINE)
                    logger.warning(f"⚠️ Agent {agent_id} marked offline due to stale heartbeat")
                
                # Check for timed out sync points
                expired_syncs = []
                for sync_id, sync_point in self.sync_points.items():
                    if current_time > sync_point.timeout:
                        expired_syncs.append(sync_id)
                
                # Clean up expired sync points
                for sync_id in expired_syncs:
                    logger.warning(f"⚠️ Sync point {sync_id} timed out")
                    del self.sync_points[sync_id]
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_collector(self):
        """Background metrics collection"""
        while self.running:
            try:
                # Update dashboard cache with current state
                await self._update_dashboard_cache()
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_handler(self):
        """Background cleanup of completed tasks and old data"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Clean up completed tasks older than 1 hour
                tasks_to_remove = []
                for task_id, task in self.tasks.items():
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        if task.completed_at:
                            completed_time = datetime.fromisoformat(task.completed_at)
                            if (current_time - completed_time).total_seconds() > 3600:  # 1 hour
                                tasks_to_remove.append(task_id)
                
                # Remove old tasks
                for task_id in tasks_to_remove:
                    del self.tasks[task_id]
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup handler: {e}")
                await asyncio.sleep(600)
    
    # Utility Methods
    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish system event"""
        await self.nc.publish(
            f"hero.v1.{self.environment}.events.{event_type}",
            json.dumps({
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }).encode()
        )
        self.metrics["messages_sent"] += 1
    
    async def _publish_system_event(self, event_type: str, data: Dict[str, Any]):
        """Publish system-level events"""
        await self._publish_event(f"system.{event_type}", data)
    
    async def _check_task_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    return False
        return True
    
    async def _update_dashboard_cache(self):
        """Update dashboard cache with current communication state"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "nats_connected": self.nc is not None and not self.nc.is_closed,
            "nats_url": self.nats_url,
            "communication_layer": {
                "status": "online" if self.running else "offline",
                "total_agents": len(self.agents),
                "online_agents": len([a for a in self.agents.values() if a.status == AgentStatus.ONLINE]),
                "active_tasks": len([t for t in self.tasks.values() if t.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]]),
                "completed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]),
                "sync_points": len(self.sync_points),
                "metrics": self.metrics.copy()
            },
            "agents": {
                agent_id: {
                    "agent_id": agent.agent_id,
                    "name": agent.name,
                    "type": agent.agent_type,
                    "status": agent.status.value,
                    "capabilities": agent.capabilities,
                    "current_tasks": len(agent.current_tasks),
                    "max_concurrent_tasks": agent.max_concurrent_tasks,
                    "performance_score": agent.performance_score,
                    "load_factor": len(agent.current_tasks) / agent.max_concurrent_tasks,
                    "last_heartbeat": agent.last_heartbeat,
                    "total_tasks": agent.total_tasks,
                    "completed_tasks": agent.completed_tasks,
                    "failed_tasks": agent.failed_tasks
                } for agent_id, agent in self.agents.items()
            },
            "tasks": {
                task_id: {
                    "task_id": task.task_id,
                    "type": task.task_type,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "assigned_agent": task.assigned_agent,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "retry_count": task.retry_count
                } for task_id, task in self.tasks.items()
            }
        }
        
        # Write to cache
        cache_file = self.cache_dir / "communication_layer.json"
        with open(cache_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def _calculate_task_duration(self, task: Task) -> Optional[float]:
        """Calculate task duration in seconds"""
        if task.started_at and task.completed_at:
            start_time = datetime.fromisoformat(task.started_at)
            end_time = datetime.fromisoformat(task.completed_at)
            return (end_time - start_time).total_seconds()
        return None
    
    # Connection event handlers
    async def _error_callback(self, error):
        logger.error(f"NATS error: {error}")
    
    async def _disconnected_callback(self):
        logger.warning("NATS disconnected")
    
    async def _reconnected_callback(self):
        logger.info("NATS reconnected")
    
    # Public API Methods
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.running,
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "sync_points": len(self.sync_points),
            "metrics": self.metrics.copy()
        }
    
    async def shutdown(self):
        """Gracefully shutdown the communication layer"""
        self.running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close NATS connection
        if self.nc:
            await self.nc.close()
        
        logger.info("✅ Inter-agent communication layer shut down")

# Additional handlers and utility classes would continue here...

async def main():
    """Main entry point for testing"""
    comm_layer = InterAgentCommunicationLayer()
    
    if await comm_layer.initialize():
        logger.info("🚀 Communication layer started successfully")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            await comm_layer.shutdown()
    else:
        logger.error("Failed to start communication layer")

if __name__ == "__main__":
    asyncio.run(main())
