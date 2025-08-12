#!/usr/bin/env python3
"""
Agent Runtime System for Hero Command Centre
Brings AI agents to life using system prompts and integrates with Hero Dashboard
"""

import json
import os
import sys
import asyncio
import logging
import signal
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid

# Add Hero monitors to path
sys.path.append(str(Path(__file__).parent.parent / "monitors"))

try:
    from agent_coordinator import get_coordinator, TaskPriority, AgentStatus
    from chimera_bridge import get_bridge
    from langsmith_tracer import get_tracer, trace_hero_function
    HERO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Hero framework not fully available: {e}")
    HERO_AVAILABLE = False

# Try to import NATS
try:
    import nats
    from nats.js import JetStreamContext
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    print("Warning: NATS not available. Install with: pip install nats-py")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / ".hero_core" / "agents.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentRuntime")

@dataclass
class AgentInstance:
    """Runtime instance of an AI agent"""
    agent_id: str
    agent_type: str
    system_prompt: str
    capabilities: List[str]
    nats_client: Optional[Any] = None
    status: str = "starting"
    current_task: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    last_heartbeat: datetime = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {
                "tasks_completed": 0,
                "success_rate": 1.0,
                "avg_response_time": 0.0,
                "errors": 0
            }
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now()

class AgentRuntime:
    """Main runtime system for managing AI agents"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInstance] = {}
        self.running = False
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self.agents_dir = Path(__file__).parent
        self.load_configurations()
        
        # Initialize Hero components
        self.coordinator = None
        self.bridge = None
        self.tracer = None
        if HERO_AVAILABLE:
            self.coordinator = get_coordinator()
            self.bridge = get_bridge()
            self.tracer = get_tracer()
        
        # NATS connection
        self.nats_client = None
        self.jetstream = None
        
        # Runtime stats
        self.runtime_stats = {
            "start_time": datetime.now(),
            "agents_launched": 0,
            "tasks_processed": 0,
            "messages_handled": 0,
            "uptime_seconds": 0
        }
        
        logger.info("Agent Runtime System initialized")
    
    def load_configurations(self):
        """Load agent configurations from YAML files"""
        try:
            # Load agent capabilities
            with open(self.agents_dir / "configs" / "agent_capabilities.yaml", 'r') as f:
                self.capabilities_config = yaml.safe_load(f)
            
            # Load NATS subjects
            with open(self.agents_dir / "configs" / "nats_subjects.yaml", 'r') as f:
                self.nats_config = yaml.safe_load(f)
            
            # Load LangSmith config
            with open(self.agents_dir / "configs" / "langsmith_config.yaml", 'r') as f:
                self.langsmith_config = yaml.safe_load(f)
            
            logger.info("Configuration files loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            raise
    
    def load_system_prompt(self, agent_type: str) -> str:
        """Load system prompt for specific agent type"""
        prompt_file = self.agents_dir / "sysprompts" / f"{agent_type}_sysprompt.md"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"System prompt not found: {prompt_file}")
        
        with open(prompt_file, 'r') as f:
            content = f.read()
        
        logger.info(f"Loaded system prompt for {agent_type} ({len(content)} characters)")
        return content
    
    async def initialize_nats_connection(self):
        """Initialize NATS connection for agent communication"""
        if not NATS_AVAILABLE:
            logger.warning("NATS not available - agents will run in standalone mode")
            return
        
        try:
            nats_url = os.getenv('NATS_URL', 'nats://localhost:4222')
            self.nats_client = await nats.connect(nats_url)
            self.jetstream = self.nats_client.jetstream()
            
            logger.info(f"Connected to NATS at {nats_url}")
            
            # Subscribe to agent management subjects
            await self._setup_nats_subscriptions()
            
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self.nats_client = None
            self.jetstream = None
    
    async def _setup_nats_subscriptions(self):
        """Setup NATS message subscriptions for agents"""
        if not self.nats_client:
            return
        
        try:
            # Subscribe to task assignments
            await self.nats_client.subscribe(
                "hero.v1.*.orchestrator.tasks.assign",
                cb=self._handle_task_assignment
            )
            
            # Subscribe to workflow controls
            await self.nats_client.subscribe(
                "hero.v1.*.orchestrator.workflow.*",
                cb=self._handle_workflow_control
            )
            
            # Subscribe to knowledge queries
            await self.nats_client.subscribe(
                "hero.v1.*.knowledge.query",
                cb=self._handle_knowledge_query
            )
            
            logger.info("NATS subscriptions established")
            
        except Exception as e:
            logger.error(f"Error setting up NATS subscriptions: {e}")
    
    async def create_agent_instance(self, agent_type: str) -> str:
        """Create and initialize a new agent instance"""
        try:
            # Load system prompt
            system_prompt = self.load_system_prompt(agent_type)
            
            # Get agent configuration
            if agent_type not in self.capabilities_config.get("agents", {}):
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            agent_config = self.capabilities_config["agents"][agent_type]
            
            # Create agent instance
            agent_id = str(uuid.uuid4())
            agent_instance = AgentInstance(
                agent_id=agent_id,
                agent_type=agent_type,
                system_prompt=system_prompt,
                capabilities=agent_config["capabilities"],
                nats_client=self.nats_client
            )
            
            # Register with Hero coordinator
            if self.coordinator:
                coordinator_agent_id = self.coordinator.register_agent(
                    f"runtime_{agent_type}",
                    agent_config["type"],
                    agent_config["capabilities"],
                    "hero-command-centre",
                    {"runtime_managed": True, "agent_id": agent_id}
                )
                logger.info(f"Registered {agent_type} with coordinator: {coordinator_agent_id}")
            
            # Store agent instance
            self.agents[agent_id] = agent_instance
            self.runtime_stats["agents_launched"] += 1
            
            # Start agent message processing loop
            asyncio.create_task(self._agent_processing_loop(agent_id))
            
            logger.info(f"Created agent instance: {agent_type} (ID: {agent_id})")
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent instance for {agent_type}: {e}")
            raise
    
    async def _agent_processing_loop(self, agent_id: str):
        """Main processing loop for an agent instance"""
        agent = self.agents[agent_id]
        
        try:
            agent.status = "active"
            logger.info(f"Starting processing loop for agent {agent_id} ({agent.agent_type})")
            
            while self.running:
                # Update heartbeat
                agent.last_heartbeat = datetime.now()
                
                # Send heartbeat to coordinator
                if self.coordinator:
                    self.coordinator.agent_heartbeat(
                        agent_id, 
                        AgentStatus.IDLE if not agent.current_task else AgentStatus.BUSY,
                        {"performance": agent.performance_metrics}
                    )
                
                # Process any pending messages (placeholder for actual LLM integration)
                await self._process_agent_messages(agent_id)
                
                # Save agent status
                await self._save_agent_status(agent_id)
                
                # Wait before next iteration
                await asyncio.sleep(1.0)
                
        except Exception as e:
            logger.error(f"Error in agent processing loop {agent_id}: {e}")
            agent.status = "error"
        
        finally:
            agent.status = "stopped"
            logger.info(f"Agent processing loop stopped: {agent_id}")
    
    async def _process_agent_messages(self, agent_id: str):
        """Process messages for a specific agent (placeholder for LLM integration)"""
        agent = self.agents[agent_id]
        
        # This is where the actual LLM integration would happen
        # For now, we'll simulate agent activity
        
        if agent.current_task:
            # Simulate task processing
            await asyncio.sleep(0.1)
            
            # Update performance metrics
            agent.performance_metrics["tasks_completed"] += 1
            
            # Complete the task (simulation)
            if self.coordinator:
                self.coordinator.complete_task(
                    agent.current_task,
                    {
                        "result": f"Task completed by {agent.agent_type}",
                        "agent_id": agent_id,
                        "completion_time": datetime.now().isoformat()
                    }
                )
            
            agent.current_task = None
            self.runtime_stats["tasks_processed"] += 1
    
    async def _handle_task_assignment(self, msg):
        """Handle task assignment messages from NATS"""
        try:
            data = json.loads(msg.data.decode())
            task_id = data.get("task_id")
            required_capabilities = data.get("required_capabilities", [])
            
            # Find suitable agent
            suitable_agent = None
            for agent_id, agent in self.agents.items():
                if (agent.status == "active" and 
                    not agent.current_task and
                    all(cap in agent.capabilities for cap in required_capabilities)):
                    suitable_agent = agent
                    break
            
            if suitable_agent:
                suitable_agent.current_task = task_id
                logger.info(f"Assigned task {task_id} to agent {suitable_agent.agent_id}")
                
                # Send acknowledgment
                if self.nats_client:
                    response = {
                        "task_id": task_id,
                        "agent_id": suitable_agent.agent_id,
                        "status": "accepted",
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.nats_client.publish(
                        f"hero.v1.dev.agents.{suitable_agent.agent_id}.task.accepted",
                        json.dumps(response).encode()
                    )
            else:
                logger.warning(f"No suitable agent found for task {task_id}")
            
            self.runtime_stats["messages_handled"] += 1
            
        except Exception as e:
            logger.error(f"Error handling task assignment: {e}")
    
    async def _handle_workflow_control(self, msg):
        """Handle workflow control messages"""
        try:
            data = json.loads(msg.data.decode())
            action = data.get("action")
            workflow_id = data.get("workflow_id")
            
            logger.info(f"Received workflow control: {action} for {workflow_id}")
            
            # Process workflow control commands
            if action == "start":
                await self._start_workflow(data)
            elif action == "pause":
                await self._pause_workflow(workflow_id)
            elif action == "resume":
                await self._resume_workflow(workflow_id)
            elif action == "abort":
                await self._abort_workflow(workflow_id)
            
            self.runtime_stats["messages_handled"] += 1
            
        except Exception as e:
            logger.error(f"Error handling workflow control: {e}")
    
    async def _handle_knowledge_query(self, msg):
        """Handle knowledge query messages"""
        try:
            data = json.loads(msg.data.decode())
            query = data.get("query")
            requester = data.get("requester")
            
            # Find knowledge integration agent
            knowledge_agent = None
            for agent in self.agents.values():
                if agent.agent_type == "knowledge_integration" and agent.status == "active":
                    knowledge_agent = agent
                    break
            
            if knowledge_agent:
                logger.info(f"Processing knowledge query from {requester}: {query}")
                
                # Simulate knowledge processing
                response = {
                    "query": query,
                    "requester": requester,
                    "response": "Knowledge query processed by knowledge integration agent",
                    "agent_id": knowledge_agent.agent_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send response
                if self.nats_client:
                    await self.nats_client.publish(
                        f"hero.v1.dev.knowledge.response.{requester}",
                        json.dumps(response).encode()
                    )
            
            self.runtime_stats["messages_handled"] += 1
            
        except Exception as e:
            logger.error(f"Error handling knowledge query: {e}")
    
    async def _start_workflow(self, workflow_data):
        """Start a new workflow"""
        workflow_id = workflow_data.get("workflow_id")
        steps = workflow_data.get("steps", [])
        
        logger.info(f"Starting workflow {workflow_id} with {len(steps)} steps")
        
        # Process workflow steps (simplified implementation)
        for step in steps:
            task_id = str(uuid.uuid4())
            
            # Submit task through coordinator
            if self.coordinator:
                self.coordinator.submit_task(
                    step.get("name", f"workflow_step_{task_id}"),
                    step.get("description", "Workflow step"),
                    step.get("required_capabilities", []),
                    TaskPriority.NORMAL,
                    {"workflow_id": workflow_id, "step_data": step}
                )
    
    async def _pause_workflow(self, workflow_id):
        """Pause a workflow"""
        logger.info(f"Pausing workflow {workflow_id}")
        # Implementation would pause all tasks related to this workflow
    
    async def _resume_workflow(self, workflow_id):
        """Resume a workflow"""
        logger.info(f"Resuming workflow {workflow_id}")
        # Implementation would resume paused tasks
    
    async def _abort_workflow(self, workflow_id):
        """Abort a workflow"""
        logger.info(f"Aborting workflow {workflow_id}")
        # Implementation would cancel all tasks related to this workflow
    
    async def _save_agent_status(self, agent_id: str):
        """Save agent status to cache for Hero Dashboard"""
        agent = self.agents[agent_id]
        
        status_data = {
            "agent_id": agent_id,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "capabilities": agent.capabilities,
            "current_task": agent.current_task,
            "performance_metrics": agent.performance_metrics,
            "last_heartbeat": agent.last_heartbeat.isoformat(),
            "system_prompt_length": len(agent.system_prompt)
        }
        
        # Save individual agent status
        agent_file = self.cache_dir / f"agent_{agent_id}_status.json"
        with open(agent_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    async def save_runtime_status(self):
        """Save overall runtime status to cache"""
        try:
            # Update runtime stats
            self.runtime_stats["uptime_seconds"] = int(
                (datetime.now() - self.runtime_stats["start_time"]).total_seconds()
            )
            
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "runtime_stats": self.runtime_stats,
                "agents": {
                    agent_id: {
                        "agent_type": agent.agent_type,
                        "status": agent.status,
                        "current_task": agent.current_task,
                        "performance": agent.performance_metrics
                    }
                    for agent_id, agent in self.agents.items()
                },
                "nats_connected": self.nats_client is not None,
                "hero_integration": {
                    "coordinator_available": self.coordinator is not None,
                    "bridge_available": self.bridge is not None,
                    "tracer_available": self.tracer is not None
                }
            }
            
            # Save to cache for Hero Dashboard
            runtime_file = self.cache_dir / "agent_runtime_status.json"
            with open(runtime_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving runtime status: {e}")
    
    async def start_runtime(self):
        """Start the agent runtime system"""
        logger.info("Starting Agent Runtime System...")
        self.running = True
        
        try:
            # Initialize NATS connection
            await self.initialize_nats_connection()
            
            # Create default agent instances
            agents_to_create = ["task_orchestrator", "knowledge_integration"]
            
            for agent_type in agents_to_create:
                try:
                    agent_id = await self.create_agent_instance(agent_type)
                    logger.info(f"Successfully created {agent_type} agent: {agent_id}")
                except Exception as e:
                    logger.error(f"Failed to create {agent_type} agent: {e}")
            
            # Start status monitoring loop
            asyncio.create_task(self._status_monitoring_loop())
            
            logger.info(f"Agent Runtime System started with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to start agent runtime: {e}")
            raise
    
    async def _status_monitoring_loop(self):
        """Regular status monitoring and reporting"""
        while self.running:
            try:
                await self.save_runtime_status()
                
                # Log system status periodically
                active_agents = len([a for a in self.agents.values() if a.status == "active"])
                logger.info(f"Runtime Status: {active_agents}/{len(self.agents)} agents active, "
                          f"{self.runtime_stats['tasks_processed']} tasks processed")
                
                await asyncio.sleep(10.0)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in status monitoring loop: {e}")
                await asyncio.sleep(10.0)
    
    async def stop_runtime(self):
        """Stop the agent runtime system"""
        logger.info("Stopping Agent Runtime System...")
        self.running = False
        
        # Close NATS connection
        if self.nats_client:
            await self.nats_client.close()
        
        # Save final status
        await self.save_runtime_status()
        
        logger.info("Agent Runtime System stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.stop_runtime())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

# Global runtime instance
_runtime = None

def get_runtime() -> AgentRuntime:
    """Get or create the global runtime instance"""
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime()
    return _runtime

async def main():
    """Main entry point for agent runtime"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hero Agent Runtime System")
    parser.add_argument("--agents", nargs="+", 
                       choices=["task_orchestrator", "knowledge_integration"],
                       help="Specific agents to launch")
    parser.add_argument("--standalone", action="store_true", 
                       help="Run without NATS connection")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start runtime
    runtime = get_runtime()
    runtime.setup_signal_handlers()
    
    try:
        await runtime.start_runtime()
        
        # Keep running until interrupted
        while runtime.running:
            await asyncio.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Runtime error: {e}")
    finally:
        await runtime.stop_runtime()

if __name__ == "__main__":
    asyncio.run(main())