#!/usr/bin/env python3
"""
Agent Coordinator for Hero Command Centre
Orchestrates multi-agent collaboration and task delegation
Outputs: ~/.hero_core/cache/agent_coordination.json
"""

import json
import os
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum
import sys
from dataclasses import dataclass, asdict

# Add path for Hero monitors
sys.path.append(str(Path(__file__).parent))

try:
    from langsmith_tracer import get_tracer, trace_hero_function, trace_agent_workflow
except ImportError:
    def get_tracer():
        return None
    def trace_hero_function(name=None, agent_type="coordinator"):
        def decorator(func):
            return func
        return decorator
    def trace_agent_workflow(name, agent_type, inputs=None):
        return None


class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    STARTING = "starting"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AgentInfo:
    """Information about a registered agent"""
    id: str
    name: str
    agent_type: str
    capabilities: List[str]
    status: AgentStatus
    last_heartbeat: datetime
    current_task: Optional[str] = None
    performance_score: float = 1.0
    total_tasks: int = 0
    successful_tasks: int = 0
    framework: str = "unknown"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Task:
    """Task definition for agent coordination"""
    id: str
    name: str
    description: str
    required_capabilities: List[str]
    priority: TaskPriority
    created_at: datetime
    assigned_agent: Optional[str] = None
    status: str = "pending"
    inputs: Dict[str, Any] = None
    outputs: Dict[str, Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = {}
        if self.metadata is None:
            self.metadata = {}


class AgentCoordinator:
    """Central coordinator for multi-agent collaboration"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.completed_tasks: List[str] = []
        
        # Configuration
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.coordination_file = self.cache_dir / "agent_coordination.json"
        self.agents_file = self.cache_dir / "registered_agents.json"
        
        # Performance tracking
        self.coordination_stats = {
            "session_started": datetime.now().isoformat(),
            "total_tasks_processed": 0,
            "active_agents": 0,
            "success_rate": 0.0,
            "average_task_duration": 0.0,
            "load_balancing_score": 1.0
        }
        
        # Load existing data
        self._load_persistent_data()
        
        # Initialize tracer
        self.tracer = get_tracer()
    
    @trace_hero_function("register_agent", "coordinator")
    def register_agent(self, agent_name: str, agent_type: str, 
                      capabilities: List[str], framework: str = "unknown",
                      metadata: Dict[str, Any] = None) -> str:
        """Register a new agent with the coordinator"""
        agent_id = str(uuid.uuid4())
        
        agent_info = AgentInfo(
            id=agent_id,
            name=agent_name,
            agent_type=agent_type,
            capabilities=capabilities,
            status=AgentStatus.IDLE,
            last_heartbeat=datetime.now(),
            framework=framework,
            metadata=metadata or {}
        )
        
        self.agents[agent_id] = agent_info
        self.coordination_stats["active_agents"] = len(self.agents)
        
        # Trace agent registration
        if self.tracer:
            self.tracer.add_agent_interaction(
                self.tracer.session_id,
                agent_name,
                "register",
                {"agent_type": agent_type, "capabilities": capabilities}
            )
        
        self._save_data()
        return agent_id
    
    @trace_hero_function("submit_task", "coordinator")
    def submit_task(self, task_name: str, description: str,
                   required_capabilities: List[str], 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   inputs: Dict[str, Any] = None,
                   metadata: Dict[str, Any] = None) -> str:
        """Submit a new task for agent processing"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=task_name,
            description=description,
            required_capabilities=required_capabilities,
            priority=priority,
            created_at=datetime.now(),
            inputs=inputs or {},
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task_id)
        
        # Sort queue by priority
        self.task_queue.sort(key=lambda tid: self.tasks[tid].priority.value, reverse=True)
        
        # Try immediate assignment
        self._assign_tasks()
        
        self._save_data()
        return task_id
    
    @trace_hero_function("assign_tasks", "coordinator")
    def _assign_tasks(self):
        """Assign pending tasks to available agents"""
        unassigned_tasks = [tid for tid in self.task_queue 
                          if self.tasks[tid].assigned_agent is None]
        
        for task_id in unassigned_tasks[:]:
            task = self.tasks[task_id]
            best_agent = self._find_best_agent(task.required_capabilities)
            
            if best_agent:
                # Assign task to agent
                task.assigned_agent = best_agent.id
                task.status = "assigned"
                task.started_at = datetime.now()
                
                # Update agent status
                best_agent.status = AgentStatus.BUSY
                best_agent.current_task = task_id
                best_agent.total_tasks += 1
                
                # Remove from queue
                self.task_queue.remove(task_id)
                
                # Trace task assignment
                if self.tracer:
                    with trace_agent_workflow(
                        f"task_assignment_{task.name}", 
                        "coordinator",
                        {"task_id": task_id, "agent_id": best_agent.id}
                    ) as trace_id:
                        self.tracer.add_agent_interaction(
                            trace_id,
                            best_agent.name,
                            "task_assigned",
                            {"task_name": task.name, "priority": task.priority.name}
                        )
    
    def _find_best_agent(self, required_capabilities: List[str]) -> Optional[AgentInfo]:
        """Find the best available agent for a task"""
        available_agents = [
            agent for agent in self.agents.values()
            if agent.status == AgentStatus.IDLE
            and all(cap in agent.capabilities for cap in required_capabilities)
        ]
        
        if not available_agents:
            return None
        
        # Score agents based on performance and current load
        def score_agent(agent: AgentInfo) -> float:
            performance_score = agent.performance_score
            success_rate = (agent.successful_tasks / agent.total_tasks 
                          if agent.total_tasks > 0 else 1.0)
            return performance_score * success_rate
        
        return max(available_agents, key=score_agent)
    
    @trace_hero_function("complete_task", "coordinator")
    def complete_task(self, task_id: str, outputs: Dict[str, Any] = None,
                     error: str = None):
        """Mark a task as completed"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.completed_at = datetime.now()
        task.outputs = outputs or {}
        task.error = error
        task.status = "completed" if not error else "failed"
        
        # Update agent status
        if task.assigned_agent and task.assigned_agent in self.agents:
            agent = self.agents[task.assigned_agent]
            agent.status = AgentStatus.IDLE
            agent.current_task = None
            
            if not error:
                agent.successful_tasks += 1
                # Boost performance score for successful completion
                agent.performance_score = min(2.0, agent.performance_score * 1.01)
            else:
                # Slightly reduce performance score for failures
                agent.performance_score = max(0.1, agent.performance_score * 0.99)
        
        # Move to completed tasks
        self.completed_tasks.append(task_id)
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
        
        # Update statistics
        self.coordination_stats["total_tasks_processed"] += 1
        self._update_stats()
        
        # Try to assign more tasks
        self._assign_tasks()
        
        self._save_data()
        return True
    
    @trace_hero_function("agent_heartbeat", "coordinator")
    def agent_heartbeat(self, agent_id: str, status: AgentStatus = None,
                       metadata: Dict[str, Any] = None):
        """Process agent heartbeat"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        agent.last_heartbeat = datetime.now()
        
        if status:
            agent.status = status
        
        if metadata:
            agent.metadata.update(metadata)
        
        self._save_data()
        return True
    
    def _update_stats(self):
        """Update coordination statistics"""
        completed_tasks = [self.tasks[tid] for tid in self.completed_tasks]
        successful_tasks = [t for t in completed_tasks if not t.error]
        
        # Calculate success rate
        if completed_tasks:
            self.coordination_stats["success_rate"] = len(successful_tasks) / len(completed_tasks)
        
        # Calculate average task duration
        durations = []
        for task in completed_tasks:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                durations.append(duration)
        
        if durations:
            self.coordination_stats["average_task_duration"] = sum(durations) / len(durations)
        
        # Calculate load balancing score
        agent_loads = [agent.total_tasks for agent in self.agents.values()]
        if agent_loads:
            max_load = max(agent_loads)
            min_load = min(agent_loads)
            self.coordination_stats["load_balancing_score"] = (
                1.0 - (max_load - min_load) / max(max_load, 1)
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Clean up stale agents (no heartbeat in 5 minutes)
        cutoff = datetime.now() - timedelta(minutes=5)
        stale_agents = [
            agent_id for agent_id, agent in self.agents.items()
            if agent.last_heartbeat < cutoff
        ]
        
        for agent_id in stale_agents:
            self.agents[agent_id].status = AgentStatus.OFFLINE
        
        # Current queue status
        pending_tasks = len([t for t in self.tasks.values() if t.status == "pending"])
        running_tasks = len([t for t in self.tasks.values() if t.status == "assigned"])
        
        # Agent breakdown
        agent_status_breakdown = {}
        agent_framework_breakdown = {}
        
        for agent in self.agents.values():
            status = agent.status.value
            framework = agent.framework
            
            agent_status_breakdown[status] = agent_status_breakdown.get(status, 0) + 1
            agent_framework_breakdown[framework] = agent_framework_breakdown.get(framework, 0) + 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "coordination_stats": self.coordination_stats,
            "agents": {
                "total": len(self.agents),
                "active": len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE]),
                "by_status": agent_status_breakdown,
                "by_framework": agent_framework_breakdown
            },
            "tasks": {
                "pending": pending_tasks,
                "running": running_tasks,
                "completed": len(self.completed_tasks),
                "queue_length": len(self.task_queue)
            },
            "performance": {
                "success_rate": self.coordination_stats["success_rate"],
                "avg_duration": self.coordination_stats["average_task_duration"],
                "load_balance": self.coordination_stats["load_balancing_score"]
            },
            "recent_activity": self._get_recent_activity()
        }
    
    def _get_recent_activity(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent coordination activity"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_tasks = [
            {
                "task_id": task.id,
                "name": task.name,
                "status": task.status,
                "agent": self.agents[task.assigned_agent].name if task.assigned_agent else None,
                "started": task.started_at.isoformat() if task.started_at else None,
                "duration": (
                    (task.completed_at - task.started_at).total_seconds()
                    if task.started_at and task.completed_at else None
                )
            }
            for task in self.tasks.values()
            if task.created_at >= cutoff
        ]
        
        return sorted(recent_tasks, key=lambda x: x.get("started") or "", reverse=True)
    
    def _save_data(self):
        """Save coordination data to cache files"""
        try:
            # Save coordination status
            status_data = self.get_system_status()
            with open(self.coordination_file, 'w') as f:
                json.dump(status_data, f, indent=2, default=str)
            
            # Save registered agents
            agents_data = {
                "agents": {aid: asdict(agent) for aid, agent in self.agents.items()},
                "last_updated": datetime.now().isoformat()
            }
            with open(self.agents_file, 'w') as f:
                json.dump(agents_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving coordination data: {e}")
    
    def _load_persistent_data(self):
        """Load persistent coordination data"""
        try:
            if self.agents_file.exists():
                with open(self.agents_file, 'r') as f:
                    data = json.load(f)
                    for aid, agent_data in data.get("agents", {}).items():
                        # Convert datetime strings back to objects
                        agent_data["last_heartbeat"] = datetime.fromisoformat(agent_data["last_heartbeat"])
                        # Handle status enum conversion safely
                        status_value = agent_data["status"]
                        if isinstance(status_value, str):
                            try:
                                agent_data["status"] = AgentStatus(status_value.split('.')[-1].lower())
                            except ValueError:
                                agent_data["status"] = AgentStatus.IDLE
                        self.agents[aid] = AgentInfo(**agent_data)
        except Exception as e:
            print(f"Error loading persistent data: {e}")


# Global coordinator instance
_coordinator = None

def get_coordinator() -> AgentCoordinator:
    """Get or create the global coordinator instance"""
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator


def main():
    """Main function for testing and standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hero Agent Coordinator")
    parser.add_argument("--status", action="store_true", help="Show coordination status")
    parser.add_argument("--test", action="store_true", help="Run test coordination")
    parser.add_argument("--register", nargs=3, help="Register test agent: name type capabilities")
    
    args = parser.parse_args()
    
    coordinator = get_coordinator()
    
    if args.status:
        status = coordinator.get_system_status()
        print("🤖 Agent Coordination Status:")
        print(json.dumps(status, indent=2, default=str))
    
    if args.test:
        print("Running coordination test...")
        
        # Register test agents
        agent1_id = coordinator.register_agent(
            "test_monitor", "monitor", ["system_info", "data_collection"], "hero"
        )
        agent2_id = coordinator.register_agent(
            "test_analyzer", "analyzer", ["data_analysis", "reporting"], "chimera"
        )
        
        # Submit test tasks
        task1_id = coordinator.submit_task(
            "system_scan", "Scan system resources", 
            ["system_info"], TaskPriority.HIGH
        )
        task2_id = coordinator.submit_task(
            "performance_analysis", "Analyze system performance",
            ["data_analysis"], TaskPriority.NORMAL
        )
        
        # Simulate task completion
        time.sleep(0.1)
        coordinator.complete_task(task1_id, {"cpu": 45.2, "memory": 67.8})
        coordinator.complete_task(task2_id, {"recommendation": "Optimize memory usage"})
        
        print("✅ Test coordination completed")
        
        # Show final status
        status = coordinator.get_system_status()
        print(f"Tasks completed: {status['tasks']['completed']}")
        print(f"Success rate: {status['performance']['success_rate']:.2%}")
    
    if args.register:
        name, agent_type, capabilities = args.register
        cap_list = capabilities.split(",")
        agent_id = coordinator.register_agent(name, agent_type, cap_list)
        print(f"✅ Registered agent {name} with ID: {agent_id}")
    
    if not any([args.status, args.test, args.register]):
        # Default: save current status
        coordinator._save_data()
        print("💾 Saved coordination status to cache")


if __name__ == "__main__":
    main()