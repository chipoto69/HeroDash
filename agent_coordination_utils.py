#!/usr/bin/env python3
"""
Agent Coordination Utilities for NATS Communication Layer
Provides base classes and utilities for agents to interact with the communication system
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod

from inter_agent_communication import TaskPriority, TaskStatus, AgentStatus

logger = logging.getLogger("AgentCoordination")

@dataclass
class TaskResult:
    """Result of a task execution"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """Base class for agents that participate in the communication layer"""
    
    def __init__(self, agent_id: str = None, agent_type: str = "generic", 
                 name: str = None, capabilities: List[str] = None,
                 max_concurrent_tasks: int = 5, nats_url: str = "nats://localhost:4222",
                 environment: str = "dev"):
        
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.name = name or f"{agent_type}_{self.agent_id[:6]}"
        self.capabilities = capabilities or [agent_type, "general"]
        self.max_concurrent_tasks = max_concurrent_tasks
        self.nats_url = nats_url
        self.environment = environment
        
        # NATS connection
        self.nc = None
        self.js = None
        
        # State management
        self.status = AgentStatus.OFFLINE
        self.current_tasks: Dict[str, Dict] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
        
        # Performance tracking
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = datetime.now()
        
        # Setup logging for this agent
        self.logger = logging.getLogger(f"Agent.{self.name}")
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
    
    async def initialize(self) -> bool:
        """Initialize the agent and connect to NATS"""
        try:
            import nats
            from nats.js import JetStreamContext
            
            # Connect to NATS
            self.nc = await nats.connect(self.nats_url)
            self.js = self.nc.jetstream()
            
            # Register with orchestrator
            await self._register_with_orchestrator()
            
            # Setup message subscriptions
            await self._setup_subscriptions()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self.status = AgentStatus.ONLINE
            self.running = True
            
            self.logger.info(f"✅ Agent {self.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize agent: {e}")
            return False
    
    async def _register_with_orchestrator(self):
        """Register this agent with the orchestration layer"""
        registration_data = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "name": self.name,
            "capabilities": self.capabilities,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "status": "online",
            "timestamp": datetime.now().isoformat()
        }
        
        await self.nc.publish(
            f"hero.v1.{self.environment}.agents.register",
            json.dumps(registration_data).encode()
        )
        
        self.logger.info(f"📡 Registered with orchestrator: {self.capabilities}")
    
    async def _setup_subscriptions(self):
        """Setup NATS subscriptions for this agent"""
        env = self.environment
        
        # Task assignments
        await self.nc.subscribe(
            f"hero.v1.{env}.agents.{self.agent_id}.tasks.assign",
            cb=self._handle_task_assignment
        )
        
        # Sync checkpoints
        await self.nc.subscribe(
            f"hero.v1.{env}.agents.{self.agent_id}.sync.checkpoint",
            cb=self._handle_sync_checkpoint
        )
        
        await self.nc.subscribe(
            f"hero.v1.{env}.agents.{self.agent_id}.sync.complete",
            cb=self._handle_sync_complete
        )
        
        # Coordination messages
        await self.nc.subscribe(
            f"hero.v1.{env}.coordination.broadcast",
            cb=self._handle_coordination_message
        )
        
        # Control messages
        await self.nc.subscribe(
            f"hero.v1.{env}.agents.{self.agent_id}.control.*",
            cb=self._handle_control_message
        )
    
    async def _start_background_tasks(self):
        """Start background tasks for the agent"""
        tasks = [
            self._heartbeat_sender(),
            self._task_monitor(),
            self._status_updater()
        ]
        
        for task in tasks:
            background_task = asyncio.create_task(task)
            self._background_tasks.add(background_task)
            background_task.add_done_callback(self._background_tasks.discard)
    
    async def _heartbeat_sender(self):
        """Send periodic heartbeats to the orchestrator"""
        while self.running:
            try:
                heartbeat_data = {
                    "agent_id": self.agent_id,
                    "status": self.status.value,
                    "timestamp": datetime.now().isoformat(),
                    "metrics": {
                        "current_tasks": len(self.current_tasks),
                        "completed_tasks": self.completed_tasks,
                        "failed_tasks": self.failed_tasks,
                        "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
                    }
                }
                
                await self.nc.publish(
                    f"hero.v1.{self.environment}.agents.heartbeat",
                    json.dumps(heartbeat_data).encode()
                )
                
                await asyncio.sleep(15)  # Heartbeat every 15 seconds
                
            except Exception as e:
                self.logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(30)
    
    async def _task_monitor(self):
        """Monitor and manage running tasks"""
        while self.running:
            try:
                current_time = datetime.now()
                timed_out_tasks = []
                
                for task_id, task_info in self.current_tasks.items():
                    # Check for task timeout
                    start_time = datetime.fromisoformat(task_info["started_at"])
                    timeout = task_info.get("timeout", 300)  # Default 5 minutes
                    
                    if (current_time - start_time).total_seconds() > timeout:
                        timed_out_tasks.append(task_id)
                
                # Handle timed out tasks
                for task_id in timed_out_tasks:
                    await self._handle_task_timeout(task_id)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in task monitor: {e}")
                await asyncio.sleep(30)
    
    async def _status_updater(self):
        """Update agent status based on current load"""
        while self.running:
            try:
                # Determine status based on task load
                load_factor = len(self.current_tasks) / self.max_concurrent_tasks
                
                if load_factor == 0:
                    new_status = AgentStatus.IDLE
                elif load_factor >= 0.8:
                    new_status = AgentStatus.BUSY
                else:
                    new_status = AgentStatus.ONLINE
                
                if new_status != self.status:
                    self.status = new_status
                    await self._send_status_update()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error updating status: {e}")
                await asyncio.sleep(60)
    
    # Message Handlers
    async def _handle_task_assignment(self, msg):
        """Handle task assignment from orchestrator"""
        try:
            task_data = json.loads(msg.data.decode())
            task_id = task_data["task_id"]
            
            self.logger.info(f"📋 Received task assignment: {task_id}")
            
            # Check if we can accept the task
            if len(self.current_tasks) >= self.max_concurrent_tasks:
                await self._reject_task(task_id, "Agent at capacity")
                return
            
            # Accept the task
            self.current_tasks[task_id] = {
                **task_data,
                "started_at": datetime.now().isoformat(),
                "status": "in_progress"
            }
            
            # Send acceptance
            await self._send_task_response(task_id, TaskStatus.IN_PROGRESS, {"message": "Task accepted"})
            
            # Execute the task asynchronously
            asyncio.create_task(self._execute_task(task_id, task_data))
            
        except Exception as e:
            self.logger.error(f"Error handling task assignment: {e}")
    
    async def _execute_task(self, task_id: str, task_data: Dict[str, Any]):
        """Execute a task"""
        try:
            task_type = task_data["task_type"]
            
            # Find appropriate handler
            handler = self.task_handlers.get(task_type, self.default_task_handler)
            
            # Execute task
            result = await handler(task_data)
            
            # Update local state
            if task_id in self.current_tasks:
                self.current_tasks[task_id]["status"] = "completed"
                self.current_tasks[task_id]["completed_at"] = datetime.now().isoformat()
                self.current_tasks[task_id]["result"] = result.data
            
            # Send completion response
            if result.success:
                await self._send_task_response(task_id, TaskStatus.COMPLETED, result.data)
                self.completed_tasks += 1
                self.logger.info(f"✅ Task {task_id} completed successfully")
            else:
                await self._send_task_response(task_id, TaskStatus.FAILED, {
                    "error": result.error,
                    "metadata": result.metadata
                })
                self.failed_tasks += 1
                self.logger.error(f"❌ Task {task_id} failed: {result.error}")
            
            # Clean up
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            await self._send_task_response(task_id, TaskStatus.FAILED, {"error": str(e)})
            self.failed_tasks += 1
            
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
    
    async def _handle_sync_checkpoint(self, msg):
        """Handle synchronization checkpoint"""
        try:
            data = json.loads(msg.data.decode())
            sync_id = data["sync_id"]
            
            self.logger.info(f"🔄 Sync checkpoint received: {sync_id}")
            
            # Execute sync callback if defined
            sync_data = await self.on_sync_checkpoint(sync_id, data)
            
            # Notify orchestrator of completion
            await self.nc.publish(
                f"hero.v1.{self.environment}.sync.checkpoint",
                json.dumps({
                    "sync_id": sync_id,
                    "agent_id": self.agent_id,
                    "data": sync_data or {}
                }).encode()
            )
            
        except Exception as e:
            self.logger.error(f"Error handling sync checkpoint: {e}")
    
    async def _handle_sync_complete(self, msg):
        """Handle sync completion notification"""
        try:
            data = json.loads(msg.data.decode())
            sync_id = data["sync_id"]
            
            self.logger.info(f"✅ Sync complete: {sync_id}")
            await self.on_sync_complete(sync_id, data)
            
        except Exception as e:
            self.logger.error(f"Error handling sync complete: {e}")
    
    async def _handle_coordination_message(self, msg):
        """Handle coordination broadcast messages"""
        try:
            data = json.loads(msg.data.decode())
            await self.on_coordination_message(data)
            
        except Exception as e:
            self.logger.error(f"Error handling coordination message: {e}")
    
    async def _handle_control_message(self, msg):
        """Handle control messages (pause, resume, shutdown)"""
        try:
            subject_parts = msg.subject.split('.')
            command = subject_parts[-1]
            
            data = json.loads(msg.data.decode())
            
            if command == "pause":
                self.status = AgentStatus.OFFLINE
                await self.on_pause(data)
            elif command == "resume":
                self.status = AgentStatus.ONLINE
                await self.on_resume(data)
            elif command == "shutdown":
                await self.shutdown()
            
        except Exception as e:
            self.logger.error(f"Error handling control message: {e}")
    
    # Task Response Methods
    async def _send_task_response(self, task_id: str, status: TaskStatus, data: Dict[str, Any]):
        """Send task response to orchestrator"""
        response = {
            "task_id": task_id,
            "agent_id": self.agent_id,
            "status": status.value,
            "timestamp": datetime.now().isoformat(),
            "result": data
        }
        
        await self.nc.publish(
            f"hero.v1.{self.environment}.tasks.response",
            json.dumps(response).encode()
        )
    
    async def _reject_task(self, task_id: str, reason: str):
        """Reject a task assignment"""
        await self._send_task_response(task_id, TaskStatus.FAILED, {
            "error": "Task rejected",
            "reason": reason
        })
    
    async def _handle_task_timeout(self, task_id: str):
        """Handle task timeout"""
        self.logger.warning(f"⏰ Task {task_id} timed out")
        
        await self._send_task_response(task_id, TaskStatus.TIMEOUT, {
            "error": "Task execution timed out"
        })
        
        if task_id in self.current_tasks:
            del self.current_tasks[task_id]
        
        self.failed_tasks += 1
    
    async def _send_status_update(self):
        """Send status update to orchestrator"""
        status_data = {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "timestamp": datetime.now().isoformat(),
            "current_tasks": len(self.current_tasks)
        }
        
        await self.nc.publish(
            f"hero.v1.{self.environment}.agents.status",
            json.dumps(status_data).encode()
        )
    
    # Task Registration
    def register_task_handler(self, task_type: str, handler: Callable[[Dict[str, Any]], TaskResult]):
        """Register a handler for a specific task type"""
        self.task_handlers[task_type] = handler
        if task_type not in self.capabilities:
            self.capabilities.append(task_type)
        
        self.logger.info(f"📝 Registered handler for task type: {task_type}")
    
    # Public Coordination Methods
    async def create_task(self, task_type: str, description: str, data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM, 
                         dependencies: List[str] = None) -> str:
        """Create a task for the orchestrator to distribute"""
        task_data = {
            "task_type": task_type,
            "description": description,
            "data": data,
            "priority": priority.value,
            "dependencies": dependencies or [],
            "created_by": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.nc.publish(
            f"hero.v1.{self.environment}.tasks.request",
            json.dumps(task_data).encode()
        )
        
        return task_data.get("task_id", "unknown")
    
    async def broadcast_message(self, message_type: str, data: Dict[str, Any]):
        """Broadcast a message to all agents"""
        message = {
            "message_type": message_type,
            "from_agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        await self.nc.publish(
            f"hero.v1.{self.environment}.coordination.broadcast",
            json.dumps(message).encode()
        )
    
    # Abstract Methods - Override in subclasses
    @abstractmethod
    async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
        """Default task handler - must be implemented by subclass"""
        pass
    
    async def on_sync_checkpoint(self, sync_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Called when a sync checkpoint is received - override if needed"""
        return {}
    
    async def on_sync_complete(self, sync_id: str, data: Dict[str, Any]):
        """Called when sync is complete - override if needed"""
        pass
    
    async def on_coordination_message(self, data: Dict[str, Any]):
        """Called when coordination message is received - override if needed"""
        pass
    
    async def on_pause(self, data: Dict[str, Any]):
        """Called when agent is paused - override if needed"""
        self.logger.info("Agent paused")
    
    async def on_resume(self, data: Dict[str, Any]):
        """Called when agent is resumed - override if needed"""
        self.logger.info("Agent resumed")
    
    # Lifecycle Management
    async def run(self):
        """Run the agent"""
        if not await self.initialize():
            return
        
        self.logger.info(f"🚀 Agent {self.name} started and ready")
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutdown requested")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the agent"""
        self.running = False
        self.status = AgentStatus.OFFLINE
        
        # Send final status update
        await self._send_status_update()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close NATS connection
        if self.nc:
            await self.nc.close()
        
        self.logger.info("✅ Agent shut down gracefully")

class TaskDistributionAgent(BaseAgent):
    """Specialized agent for distributing tasks to other agents"""
    
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="task_distributor",
            capabilities=["task_distribution", "coordination", "management"],
            **kwargs
        )
    
    async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
        """Handle task distribution requests"""
        try:
            # Extract sub-tasks and distribute them
            sub_tasks = task_data.get("data", {}).get("sub_tasks", [])
            
            distributed_tasks = []
            for sub_task in sub_tasks:
                task_id = await self.create_task(
                    task_type=sub_task["type"],
                    description=sub_task["description"],
                    data=sub_task.get("data", {}),
                    priority=TaskPriority(sub_task.get("priority", TaskPriority.MEDIUM.value))
                )
                distributed_tasks.append(task_id)
            
            return TaskResult(
                success=True,
                data={"distributed_tasks": distributed_tasks}
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                data={},
                error=str(e)
            )

class MonitoringAgent(BaseAgent):
    """Specialized agent for system monitoring"""
    
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="monitor",
            capabilities=["monitoring", "metrics", "health_check"],
            **kwargs
        )
        
        self.metrics_data = {}
    
    async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
        """Handle monitoring tasks"""
        try:
            monitor_type = task_data.get("data", {}).get("monitor_type", "system")
            
            if monitor_type == "system":
                metrics = await self._collect_system_metrics()
            elif monitor_type == "agent":
                metrics = await self._collect_agent_metrics()
            elif monitor_type == "network":
                metrics = await self._collect_network_metrics()
            else:
                metrics = {}
            
            # Store metrics
            self.metrics_data[monitor_type] = {
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            }
            
            return TaskResult(
                success=True,
                data={"metrics": metrics}
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                data={},
                error=str(e)
            )
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        # This would integrate with system monitoring tools
        return {
            "cpu_usage": 45.2,
            "memory_usage": 67.8,
            "disk_usage": 23.1,
            "network_io": {"rx": 1024, "tx": 2048}
        }
    
    async def _collect_agent_metrics(self) -> Dict[str, Any]:
        """Collect agent performance metrics"""
        return {
            "total_agents": 5,
            "active_agents": 4,
            "task_throughput": 15.3,
            "avg_response_time": 0.85
        }
    
    async def _collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network/NATS metrics"""
        return {
            "nats_connected": True,
            "message_rate": 125.7,
            "latency": 12.3,
            "error_rate": 0.02
        }

# Utility Functions
def create_agent_from_config(config: Dict[str, Any]) -> BaseAgent:
    """Create an agent from configuration"""
    agent_type = config.get("type", "generic")
    
    if agent_type == "task_distributor":
        return TaskDistributionAgent(**config)
    elif agent_type == "monitor":
        return MonitoringAgent(**config)
    else:
        # Create a generic agent with custom handler
        class GenericAgent(BaseAgent):
            async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
                # Simple echo task handler
                return TaskResult(
                    success=True,
                    data={"echo": task_data}
                )
        
        return GenericAgent(**config)

async def run_agent_from_config(config_file: str):
    """Run an agent from a configuration file"""
    import yaml
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    agent = create_agent_from_config(config)
    await agent.run()

if __name__ == "__main__":
    # Example usage
    class ExampleAgent(BaseAgent):
        async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
            task_type = task_data.get("task_type")
            self.logger.info(f"Processing task: {task_type}")
            
            # Simulate some work
            await asyncio.sleep(2)
            
            return TaskResult(
                success=True,
                data={"processed": task_type, "timestamp": datetime.now().isoformat()}
            )
    
    # Create and run example agent
    agent = ExampleAgent(
        agent_type="example",
        name="Example Agent",
        capabilities=["example_task", "demo"]
    )
    
    asyncio.run(agent.run())
