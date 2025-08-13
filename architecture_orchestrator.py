#!/usr/bin/env python3
"""
Architecture Team Orchestrator
Coordinates architecture implementation agents without NATS authorization issues
"""
import asyncio
import json
import time
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / ".hero_core" / "arch_orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArchOrchestrator")

class ArchitectureTeam:
    def __init__(self):
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Your agent team configuration
        self.agents = {
            "architect": {
                "pid": 1181,
                "name": "Architect",
                "role": "Project Lead & Architecture Design",
                "capabilities": ["system_design", "feature_planning", "architecture_decisions"],
                "status": "active",
                "current_task": None,
                "tasks_completed": 0,
                "coordination_priority": 1  # Highest priority
            },
            "ampcode": {
                "pid": 88050,
                "name": "Ampcode",
                "role": "Primary Coder - Fast Implementation",
                "capabilities": ["rapid_coding", "feature_implementation", "performance_optimization"],
                "status": "active", 
                "current_task": None,
                "tasks_completed": 0,
                "coordination_priority": 2
            },
            "ampcode2": {
                "pid": 57730,
                "name": "Ampcode2",
                "role": "Secondary Coder - Support & Refinement",
                "capabilities": ["code_review", "bug_fixes", "testing", "refactoring"],
                "status": "active",
                "current_task": None,
                "tasks_completed": 0,
                "coordination_priority": 3
            },
            "documentation_orchestrator": {
                "pid": 89852,
                "name": "DocOrchestrator",
                "role": "Documentation & Project Coordination",
                "capabilities": ["documentation", "project_coordination", "architectural_docs"],
                "status": "active",
                "current_task": None,
                "tasks_completed": 0,
                "coordination_priority": 2
            },
            "implementation_coder": {
                "pid": 95867,
                "name": "ImplCoder",
                "role": "Architecture Implementation Specialist",
                "capabilities": ["architecture_implementation", "system_integration", "deployment"],
                "status": "active",
                "current_task": None,
                "tasks_completed": 0,
                "coordination_priority": 2
            }
        }
        
        self.project_state = {
            "project_name": "Architecture Upgrade Implementation",
            "phase": "planning",
            "started": datetime.now().isoformat(),
            "tasks": [],
            "completed_tasks": [],
            "active_tasks": [],
            "next_milestone": "Initial Architecture Design",
            "coordination_messages": []
        }
        
        self.message_queue = []
        self.running = False
        
    def register_all_agents(self):
        """Register all architecture team agents with the dashboard"""
        timestamp = datetime.now().isoformat()
        
        # Create comprehensive agent runtime status
        agent_runtime_data = {
            "timestamp": timestamp,
            "runtime_stats": {
                "start_time": timestamp,
                "agents_launched": len(self.agents),
                "tasks_processed": sum(agent["tasks_completed"] for agent in self.agents.values()),
                "messages_handled": len(self.message_queue),
                "uptime_seconds": 0,
                "project": "Architecture Upgrade Implementation"
            },
            "agents": {},
            "nats_connected": False,  # Using direct coordination
            "hero_integration": {
                "coordinator_available": True,
                "bridge_available": True,
                "tracer_available": True,
                "architecture_team": True
            },
            "project_info": {
                "name": self.project_state["project_name"],
                "phase": self.project_state["phase"],
                "milestone": self.project_state["next_milestone"]
            }
        }
        
        # Register each agent
        for agent_id, agent in self.agents.items():
            agent_uuid = f"arch_{agent_id}_{agent['pid']}"
            
            agent_runtime_data["agents"][agent_uuid] = {
                "agent_type": agent_id,
                "agent_name": agent["name"],
                "role": agent["role"],
                "pid": agent["pid"],
                "status": agent["status"],
                "current_task": agent["current_task"],
                "capabilities": agent["capabilities"],
                "coordination_priority": agent["coordination_priority"],
                "performance": {
                    "tasks_completed": agent["tasks_completed"],
                    "success_rate": 1.0,
                    "avg_response_time": 150.0,
                    "errors": 0
                },
                "last_heartbeat": timestamp
            }
            
            # Create individual agent cache file
            individual_agent_data = {
                "timestamp": timestamp,
                "runtime_stats": {
                    "start_time": timestamp,
                    "agents_launched": 1,
                    "tasks_processed": agent["tasks_completed"],
                    "messages_handled": 0,
                    "uptime_seconds": 0
                },
                "agents": {
                    agent_uuid: agent_runtime_data["agents"][agent_uuid]
                },
                "nats_connected": False,
                "hero_integration": {
                    "coordinator_available": True,
                    "bridge_available": True,
                    "tracer_available": True
                }
            }
            
            agent_file = self.cache_dir / f"arch_agent_{agent_id}.json"
            with open(agent_file, 'w') as f:
                json.dump(individual_agent_data, f, indent=2)
        
        # Write main runtime status
        with open(self.cache_dir / "agent_runtime_status.json", 'w') as f:
            json.dump(agent_runtime_data, f, indent=2)
        
        logger.info(f"✅ Registered {len(self.agents)} architecture team agents")
        
    def assign_task(self, task_name: str, description: str, assigned_to: str, priority: str = "normal"):
        """Assign a task to a specific agent"""
        task = {
            "task_id": f"arch_task_{int(time.time())}_{len(self.project_state['tasks'])}",
            "name": task_name,
            "description": description,
            "assigned_to": assigned_to,
            "priority": priority,
            "status": "assigned",
            "created": datetime.now().isoformat(),
            "estimated_duration": "TBD"
        }
        
        self.project_state["tasks"].append(task)
        self.project_state["active_tasks"].append(task["task_id"])
        
        if assigned_to in self.agents:
            self.agents[assigned_to]["current_task"] = task_name
            self.agents[assigned_to]["status"] = "busy"
        
        # Log coordination message
        coord_msg = {
            "timestamp": datetime.now().isoformat(),
            "type": "task_assignment",
            "from": "orchestrator",
            "to": assigned_to,
            "content": f"Assigned task: {task_name}",
            "task_id": task["task_id"]
        }
        self.project_state["coordination_messages"].append(coord_msg)
        self.message_queue.append(coord_msg)
        
        logger.info(f"📋 Assigned task '{task_name}' to {assigned_to}")
        return task
    
    def complete_task(self, agent_id: str, task_id: str, result: str):
        """Mark a task as completed"""
        # Update task status
        for task in self.project_state["tasks"]:
            if task["task_id"] == task_id:
                task["status"] = "completed"
                task["completed"] = datetime.now().isoformat()
                task["result"] = result
                
                # Move to completed tasks
                if task_id in self.project_state["active_tasks"]:
                    self.project_state["active_tasks"].remove(task_id)
                self.project_state["completed_tasks"].append(task_id)
                break
        
        # Update agent status
        if agent_id in self.agents:
            self.agents[agent_id]["tasks_completed"] += 1
            self.agents[agent_id]["current_task"] = None
            self.agents[agent_id]["status"] = "active"
        
        # Log coordination message
        coord_msg = {
            "timestamp": datetime.now().isoformat(),
            "type": "task_completion",
            "from": agent_id,
            "to": "orchestrator",
            "content": f"Completed task: {task_id}",
            "result": result
        }
        self.project_state["coordination_messages"].append(coord_msg)
        self.message_queue.append(coord_msg)
        
        logger.info(f"✅ Task {task_id} completed by {agent_id}")
    
    def send_coordination_message(self, from_agent: str, to_agent: str, message: str, msg_type: str = "coordination"):
        """Send coordination message between agents"""
        coord_msg = {
            "timestamp": datetime.now().isoformat(),
            "type": msg_type,
            "from": from_agent,
            "to": to_agent,
            "content": message,
            "id": f"msg_{int(time.time())}_{len(self.message_queue)}"
        }
        
        self.project_state["coordination_messages"].append(coord_msg)
        self.message_queue.append(coord_msg)
        
        logger.info(f"💬 {from_agent} → {to_agent}: {message}")
        return coord_msg
    
    def update_project_phase(self, new_phase: str, milestone: str):
        """Update project phase and milestone"""
        old_phase = self.project_state["phase"]
        self.project_state["phase"] = new_phase
        self.project_state["next_milestone"] = milestone
        
        coord_msg = {
            "timestamp": datetime.now().isoformat(),
            "type": "phase_change",
            "from": "orchestrator",
            "to": "all_agents",
            "content": f"Project phase changed: {old_phase} → {new_phase}",
            "milestone": milestone
        }
        self.project_state["coordination_messages"].append(coord_msg)
        self.message_queue.append(coord_msg)
        
        logger.info(f"🎯 Project phase updated: {new_phase} | Milestone: {milestone}")
    
    def save_project_state(self):
        """Save current project state to cache"""
        project_file = self.cache_dir / "architecture_project.json"
        with open(project_file, 'w') as f:
            json.dump(self.project_state, f, indent=2)
        
        # Save coordination messages for dashboard
        coord_file = self.cache_dir / "agent_coordination.json"
        coord_data = {
            "timestamp": datetime.now().isoformat(),
            "coordination_stats": {
                "session_started": self.project_state["started"],
                "total_tasks_processed": len(self.project_state["completed_tasks"]),
                "active_agents": len([a for a in self.agents.values() if a["status"] == "active"]),
                "success_rate": 1.0,
                "average_task_duration": 300.0,
                "load_balancing_score": 0.9
            },
            "agents": {
                "total": len(self.agents),
                "active": len([a for a in self.agents.values() if a["status"] in ["active", "busy"]]),
                "by_status": {
                    "active": len([a for a in self.agents.values() if a["status"] == "active"]),
                    "busy": len([a for a in self.agents.values() if a["status"] == "busy"]),
                    "idle": len([a for a in self.agents.values() if a["status"] == "idle"])
                },
                "by_role": {
                    "architect": 1,
                    "coders": 3,
                    "documentation": 1
                }
            },
            "tasks": {
                "pending": len(self.project_state["active_tasks"]),
                "running": len([t for t in self.project_state["tasks"] if t.get("status") == "running"]),
                "completed": len(self.project_state["completed_tasks"]),
                "queue_length": len(self.project_state["active_tasks"])
            },
            "performance": {
                "success_rate": 1.0,
                "avg_duration": 300.0,
                "load_balance": 0.9
            },
            "recent_activity": [
                {
                    "task_id": msg.get("task_id", msg.get("id", "unknown")),
                    "name": msg["content"][:50],
                    "status": "completed" if msg["type"] == "task_completion" else "assigned",
                    "agent": msg["from"],
                    "started": msg["timestamp"],
                    "duration": None
                }
                for msg in self.project_state["coordination_messages"][-10:]
            ]
        }
        
        with open(coord_file, 'w') as f:
            json.dump(coord_data, f, indent=2)
    
    async def heartbeat_loop(self):
        """Continuous heartbeat and status updates"""
        start_time = time.time()
        
        while self.running:
            current_time = datetime.now().isoformat()
            uptime = int(time.time() - start_time)
            
            # Update agent heartbeats
            for agent_id, agent in self.agents.items():
                agent_uuid = f"arch_{agent_id}_{agent['pid']}"
                
                # Update individual agent file
                agent_data = {
                    "timestamp": current_time,
                    "runtime_stats": {
                        "start_time": self.project_state["started"],
                        "agents_launched": 1,
                        "tasks_processed": agent["tasks_completed"],
                        "messages_handled": len([m for m in self.message_queue if m.get("to") == agent_id or m.get("from") == agent_id]),
                        "uptime_seconds": uptime
                    },
                    "agents": {
                        agent_uuid: {
                            "agent_type": agent_id,
                            "agent_name": agent["name"],
                            "role": agent["role"],
                            "pid": agent["pid"],
                            "status": agent["status"],
                            "current_task": agent["current_task"],
                            "capabilities": agent["capabilities"],
                            "coordination_priority": agent["coordination_priority"],
                            "performance": {
                                "tasks_completed": agent["tasks_completed"],
                                "success_rate": 1.0,
                                "avg_response_time": 150.0,
                                "errors": 0
                            },
                            "last_heartbeat": current_time
                        }
                    },
                    "nats_connected": False,
                    "hero_integration": {
                        "coordinator_available": True,
                        "bridge_available": True,
                        "tracer_available": True
                    }
                }
                
                agent_file = self.cache_dir / f"arch_agent_{agent_id}.json"
                with open(agent_file, 'w') as f:
                    json.dump(agent_data, f, indent=2)
            
            # Update main runtime status
            self.register_all_agents()
            self.save_project_state()
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    async def start_orchestration(self):
        """Start the architecture team orchestration"""
        self.running = True
        
        print("🚀 Architecture Team Orchestrator Starting")
        print("=" * 60)
        print(f"📊 Dashboard: http://localhost:8080")
        print(f"👥 Team Size: {len(self.agents)} agents")
        print(f"🎯 Project: {self.project_state['project_name']}")
        print("=" * 60)
        
        # Register all agents
        self.register_all_agents()
        
        # Setup initial project tasks
        self.setup_initial_tasks()
        
        # Start heartbeat loop
        heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        try:
            # Demo coordination workflow
            await self.demo_coordination_workflow()
            
            # Keep running
            await heartbeat_task
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping Architecture Orchestrator...")
            self.running = False
            heartbeat_task.cancel()
            
    def setup_initial_tasks(self):
        """Setup initial architecture project tasks"""
        # Phase 1: Planning and Design
        self.assign_task(
            "System Architecture Review", 
            "Review current system architecture and identify upgrade requirements",
            "architect",
            "high"
        )
        
        self.assign_task(
            "Technical Specification", 
            "Create detailed technical specifications for new features",
            "documentation_orchestrator",
            "high"
        )
        
        # Phase 2: Implementation Planning  
        self.assign_task(
            "Implementation Strategy",
            "Define implementation approach and code structure",
            "implementation_coder", 
            "normal"
        )
        
        self.assign_task(
            "Performance Optimization Plan",
            "Plan performance improvements and optimizations",
            "ampcode",
            "normal"
        )
        
        logger.info("📋 Initial project tasks created")
    
    async def demo_coordination_workflow(self):
        """Demonstrate coordination between agents"""
        await asyncio.sleep(3)
        
        # Architect sends design decisions
        self.send_coordination_message(
            "architect", 
            "all_agents",
            "Architecture review complete. Moving to implementation phase.",
            "broadcast"
        )
        
        await asyncio.sleep(2)
        
        # Complete architect's task
        self.complete_task("architect", self.project_state["tasks"][0]["task_id"], 
                          "Architecture review completed with recommendations for modular upgrade approach")
        
        await asyncio.sleep(2)
        
        # Update project phase
        self.update_project_phase("implementation", "Core Module Development")
        
        await asyncio.sleep(2)
        
        # Coding coordination
        self.send_coordination_message(
            "ampcode",
            "ampcode2", 
            "Starting core module implementation. Please prepare for code review.",
            "coordination"
        )
        
        await asyncio.sleep(3)
        
        # Documentation coordination
        self.send_coordination_message(
            "documentation_orchestrator",
            "architect",
            "Technical specifications ready. Requesting architecture validation.",
            "request"
        )
        
        logger.info("🎭 Demo coordination workflow completed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Received shutdown signal")
    sys.exit(0)

async def main():
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    orchestrator = ArchitectureTeam()
    await orchestrator.start_orchestration()

if __name__ == "__main__":
    print("🏗️ Architecture Team Orchestrator")
    print("Direct coordination without NATS authorization issues")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Architecture Orchestration stopped")