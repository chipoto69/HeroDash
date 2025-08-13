#!/usr/bin/env python3
"""
Complete NATS Inter-Agentic Communication System Runner
Orchestrates the communication layer, agents, and monitoring
"""
import asyncio
import json
import subprocess
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import argparse
import yaml
from contextlib import asynccontextmanager

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from inter_agent_communication import InterAgentCommunicationLayer, TaskPriority
from agent_coordination_utils import BaseAgent, TaskResult, MonitoringAgent, TaskDistributionAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / ".hero_core" / "communication_system.log")
    ]
)
logger = logging.getLogger("CommunicationSystem")

class CommunicationSystemOrchestrator:
    """Main orchestrator for the communication system"""
    
    def __init__(self, config_file: Optional[str] = None, nats_url: str = "nats://localhost:4224"):
        self.nats_url = nats_url
        self.config = self._load_config(config_file)
        
        # Core components
        self.communication_layer: Optional[InterAgentCommunicationLayer] = None
        self.system_agents: List[BaseAgent] = []
        self.user_agents: List[BaseAgent] = []
        
        # System state
        self.running = False
        self.nats_server_process = None
        self.dashboard_process = None
        
        # Metrics and monitoring
        self.start_time = datetime.now()
        self.system_metrics = {
            "system_start_time": self.start_time.isoformat(),
            "nats_restarts": 0,
            "agent_failures": 0,
            "tasks_processed": 0,
            "uptime_seconds": 0
        }
        
        # Background tasks
        self._background_tasks = set()
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load system configuration"""
        default_config = {
            "environment": "dev",
            "nats": {
                "url": self.nats_url,
                "streams": {
                    "tasks": {"retention": "WorkQueue", "max_msgs": 10000},
                    "events": {"retention": "Limits", "max_msgs": 50000},
                    "coordination": {"retention": "Limits", "max_msgs": 25000}
                }
            },
            "agents": {
                "system_agents": [
                    {
                        "type": "task_distributor",
                        "name": "Primary Task Distributor",
                        "capabilities": ["task_distribution", "coordination"],
                        "max_concurrent_tasks": 20
                    },
                    {
                        "type": "monitor",
                        "name": "System Monitor",
                        "capabilities": ["monitoring", "health_check", "metrics"],
                        "max_concurrent_tasks": 10
                    }
                ],
                "auto_scale": {
                    "enabled": True,
                    "min_agents": 2,
                    "max_agents": 10,
                    "scale_threshold": 0.8
                }
            },
            "monitoring": {
                "metrics_interval": 30,
                "health_check_interval": 60,
                "cleanup_interval": 300
            },
            "dashboard": {
                "enabled": True,
                "port": 8080,
                "auto_launch": False
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)
                
                # Merge configs (user config overrides defaults)
                def merge_dicts(base, override):
                    result = base.copy()
                    for key, value in override.items():
                        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                            result[key] = merge_dicts(result[key], value)
                        else:
                            result[key] = value
                    return result
                
                return merge_dicts(default_config, user_config)
                
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
                logger.info("Using default configuration")
        
        return default_config
    
    async def initialize(self) -> bool:
        """Initialize the complete communication system"""
        logger.info("🚀 Initializing NATS Inter-Agentic Communication System...")
        
        try:
            # Ensure NATS server is running
            if not await self._ensure_nats_server():
                return False
            
            # Initialize communication layer
            self.communication_layer = InterAgentCommunicationLayer(
                nats_url=self.nats_url,
                environment=self.config.get("environment", "dev")
            )
            
            if not await self.communication_layer.initialize():
                logger.error("Failed to initialize communication layer")
                return False
            
            # Create system agents
            await self._create_system_agents()
            
            # Start monitoring and maintenance tasks
            await self._start_background_tasks()
            
            # Start dashboard if enabled
            if self.config.get("dashboard", {}).get("enabled", True):
                await self._start_dashboard()
            
            self.running = True
            logger.info("✅ Communication system initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize communication system: {e}")
            return False
    
    async def _ensure_nats_server(self) -> bool:
        """Ensure NATS server is running, start if needed"""
        logger.info("🔍 Checking NATS server status...")
        
        # Check if NATS is already running
        try:
            import nats
            nc = await nats.connect(self.nats_url, connect_timeout=2)
            await nc.close()
            logger.info(f"✅ NATS server already running at {self.nats_url}")
            return True
        except:
            pass
        
        # Try to start NATS server
        logger.info("🔄 Starting NATS server...")
        
        try:
            # Check if nats-server is available
            result = subprocess.run(["which", "nats-server"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("nats-server not found. Please install NATS server.")
                return False
            
            # Start NATS server with JetStream
            port = self.nats_url.split(":")[-1]
            self.nats_server_process = subprocess.Popen([
                "nats-server", 
                "-p", port,
                "-js",  # Enable JetStream
                "-D"    # Enable debug mode
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Verify it's running
            try:
                nc = await nats.connect(self.nats_url, connect_timeout=5)
                await nc.close()
                logger.info(f"✅ NATS server started successfully at {self.nats_url}")
                return True
            except Exception as e:
                logger.error(f"NATS server failed to start properly: {e}")
                if self.nats_server_process:
                    self.nats_server_process.terminate()
                return False
                
        except Exception as e:
            logger.error(f"Failed to start NATS server: {e}")
            return False
    
    async def _create_system_agents(self):
        """Create core system agents"""
        logger.info("👥 Creating system agents...")
        
        system_agents_config = self.config.get("agents", {}).get("system_agents", [])
        
        for agent_config in system_agents_config:
            try:
                agent_type = agent_config.get("type", "generic")
                
                if agent_type == "task_distributor":
                    agent = TaskDistributionAgent(
                        name=agent_config.get("name", "Task Distributor"),
                        capabilities=agent_config.get("capabilities", ["task_distribution"]),
                        max_concurrent_tasks=agent_config.get("max_concurrent_tasks", 10),
                        nats_url=self.nats_url,
                        environment=self.config.get("environment", "dev")
                    )
                elif agent_type == "monitor":
                    agent = MonitoringAgent(
                        name=agent_config.get("name", "System Monitor"),
                        capabilities=agent_config.get("capabilities", ["monitoring"]),
                        max_concurrent_tasks=agent_config.get("max_concurrent_tasks", 10),
                        nats_url=self.nats_url,
                        environment=self.config.get("environment", "dev")
                    )
                else:
                    continue  # Skip unknown agent types
                
                if await agent.initialize():
                    self.system_agents.append(agent)
                    logger.info(f"✅ Created system agent: {agent.name}")
                else:
                    logger.error(f"❌ Failed to create system agent: {agent_config.get('name')}")
                    
            except Exception as e:
                logger.error(f"Error creating system agent: {e}")
    
    async def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        tasks = [
            self._system_health_monitor(),
            self._metrics_collector(),
            self._auto_scaler(),
            self._cleanup_manager()
        ]
        
        for task in tasks:
            background_task = asyncio.create_task(task)
            self._background_tasks.add(background_task)
            background_task.add_done_callback(self._background_tasks.discard)
    
    async def _system_health_monitor(self):
        """Monitor overall system health"""
        while self.running:
            try:
                # Check NATS connectivity
                if self.communication_layer and self.communication_layer.nc:
                    if self.communication_layer.nc.is_closed:
                        logger.warning("⚠️ NATS connection lost - attempting reconnect")
                        await self.communication_layer.initialize()
                
                # Check agent health
                failed_agents = []
                for agent in self.system_agents + self.user_agents:
                    if not agent.running or agent.nc.is_closed:
                        failed_agents.append(agent.agent_id)
                        self.system_metrics["agent_failures"] += 1
                
                # Remove failed agents
                if failed_agents:
                    self.system_agents = [a for a in self.system_agents if a.agent_id not in failed_agents]
                    self.user_agents = [a for a in self.user_agents if a.agent_id not in failed_agents]
                    logger.warning(f"⚠️ Removed {len(failed_agents)} failed agents")
                
                await asyncio.sleep(self.config.get("monitoring", {}).get("health_check_interval", 60))
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)
    
    async def _metrics_collector(self):
        """Collect and update system metrics"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Update basic metrics
                self.system_metrics.update({
                    "uptime_seconds": (current_time - self.start_time).total_seconds(),
                    "total_agents": len(self.system_agents) + len(self.user_agents),
                    "system_agents": len(self.system_agents),
                    "user_agents": len(self.user_agents),
                    "timestamp": current_time.isoformat()
                })
                
                # Get communication layer metrics
                if self.communication_layer:
                    comm_status = await self.communication_layer.get_system_status()
                    self.system_metrics.update({
                        "communication_layer": comm_status
                    })
                
                # Save metrics to dashboard cache
                cache_file = Path.home() / ".hero_core" / "cache" / "system_metrics.json"
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(cache_file, 'w') as f:
                    json.dump(self.system_metrics, f, indent=2)
                
                await asyncio.sleep(self.config.get("monitoring", {}).get("metrics_interval", 30))
                
            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")
                await asyncio.sleep(30)
    
    async def _auto_scaler(self):
        """Auto-scale agents based on load"""
        auto_scale_config = self.config.get("agents", {}).get("auto_scale", {})
        if not auto_scale_config.get("enabled", False):
            return
        
        while self.running:
            try:
                if self.communication_layer:
                    # Get current system load
                    total_agents = len(self.system_agents) + len(self.user_agents)
                    min_agents = auto_scale_config.get("min_agents", 2)
                    max_agents = auto_scale_config.get("max_agents", 10)
                    scale_threshold = auto_scale_config.get("scale_threshold", 0.8)
                    
                    # Calculate average load across agents
                    total_load = 0
                    active_agents = 0
                    
                    for agent_id, agent_data in self.communication_layer.agents.items():
                        if agent_data.status.value in ["online", "busy"]:
                            load = len(agent_data.current_tasks) / agent_data.max_concurrent_tasks
                            total_load += load
                            active_agents += 1
                    
                    avg_load = total_load / active_agents if active_agents > 0 else 0
                    
                    # Scale up if needed
                    if avg_load > scale_threshold and total_agents < max_agents:
                        logger.info(f"🔺 Auto-scaling up: avg load {avg_load:.2f} > {scale_threshold}")
                        await self._create_dynamic_agent()
                    
                    # Scale down if needed (basic implementation)
                    elif avg_load < 0.3 and total_agents > min_agents:
                        logger.info(f"🔻 Auto-scaling down: avg load {avg_load:.2f} < 0.3")
                        # Could implement scale-down logic here
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in auto-scaler: {e}")
                await asyncio.sleep(60)
    
    async def _create_dynamic_agent(self):
        """Create a dynamic agent for scaling"""
        try:
            from agent_coordination_utils import BaseAgent, TaskResult
            
            class DynamicAgent(BaseAgent):
                async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
                    # Simple general purpose handler
                    task_type = task_data.get("task_type", "unknown")
                    await asyncio.sleep(1)  # Simulate processing
                    
                    return TaskResult(
                        success=True,
                        data={
                            "processed_by": self.agent_id,
                            "task_type": task_type,
                            "result": "Dynamic agent processed task successfully"
                        }
                    )
            
            agent = DynamicAgent(
                agent_type="dynamic_worker",
                name=f"Dynamic Agent {len(self.user_agents) + 1}",
                capabilities=["general", "dynamic_scaling"],
                max_concurrent_tasks=5,
                nats_url=self.nats_url,
                environment=self.config.get("environment", "dev")
            )
            
            if await agent.initialize():
                self.user_agents.append(agent)
                logger.info(f"✅ Created dynamic agent: {agent.name}")
            
        except Exception as e:
            logger.error(f"Failed to create dynamic agent: {e}")
    
    async def _cleanup_manager(self):
        """Manage system cleanup and maintenance"""
        while self.running:
            try:
                # Clean up old log files, cache files, etc.
                log_dir = Path.home() / ".hero_core"
                if log_dir.exists():
                    # Remove log files older than 7 days
                    cutoff_time = time.time() - (7 * 24 * 60 * 60)
                    for log_file in log_dir.glob("*.log"):
                        if log_file.stat().st_mtime < cutoff_time:
                            log_file.unlink()
                
                await asyncio.sleep(self.config.get("monitoring", {}).get("cleanup_interval", 300))
                
            except Exception as e:
                logger.error(f"Error in cleanup manager: {e}")
                await asyncio.sleep(300)
    
    async def _start_dashboard(self):
        """Start the web dashboard if configured"""
        dashboard_config = self.config.get("dashboard", {})
        
        if dashboard_config.get("auto_launch", False):
            try:
                dashboard_script = Path(__file__).parent / "web_dashboard.py"
                if dashboard_script.exists():
                    port = dashboard_config.get("port", 8080)
                    self.dashboard_process = subprocess.Popen([
                        sys.executable, str(dashboard_script), "--port", str(port)
                    ])
                    logger.info(f"🌐 Started web dashboard on port {port}")
                    
            except Exception as e:
                logger.error(f"Failed to start dashboard: {e}")
    
    # Public API Methods
    async def create_task(self, task_type: str, description: str, data: Dict[str, Any],
                         priority: TaskPriority = TaskPriority.MEDIUM) -> Optional[str]:
        """Create a task for processing"""
        if self.communication_layer:
            return await self.communication_layer.create_task(
                task_type=task_type,
                description=description,
                data=data,
                priority=priority
            )
        return None
    
    async def register_user_agent(self, agent: BaseAgent) -> bool:
        """Register a user-created agent"""
        try:
            if await agent.initialize():
                self.user_agents.append(agent)
                logger.info(f"✅ Registered user agent: {agent.name}")
                return True
        except Exception as e:
            logger.error(f"Failed to register user agent: {e}")
        return False
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "system": {
                "running": self.running,
                "uptime": (datetime.now() - self.start_time).total_seconds(),
                "environment": self.config.get("environment", "dev")
            },
            "agents": {
                "total": len(self.system_agents) + len(self.user_agents),
                "system_agents": len(self.system_agents),
                "user_agents": len(self.user_agents)
            },
            "nats": {
                "url": self.nats_url,
                "connected": self.communication_layer and not self.communication_layer.nc.is_closed if self.communication_layer else False
            },
            "metrics": self.system_metrics
        }
        
        if self.communication_layer:
            comm_status = await self.communication_layer.get_system_status()
            status["communication_layer"] = comm_status
        
        return status
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def run_forever(self):
        """Run the system indefinitely"""
        logger.info("🏃 Communication system running...")
        logger.info("Press Ctrl+C to shutdown gracefully")
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown the entire system"""
        logger.info("🛑 Shutting down communication system...")
        self.running = False
        
        # Shutdown user agents
        for agent in self.user_agents:
            try:
                await agent.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down user agent: {e}")
        
        # Shutdown system agents
        for agent in self.system_agents:
            try:
                await agent.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down system agent: {e}")
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Shutdown communication layer
        if self.communication_layer:
            await self.communication_layer.shutdown()
        
        # Shutdown external processes
        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process.wait(timeout=5)
        
        if self.nats_server_process:
            self.nats_server_process.terminate()
            self.nats_server_process.wait(timeout=5)
        
        logger.info("✅ Communication system shutdown complete")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="NATS Inter-Agentic Communication System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--nats-url", default="nats://localhost:4222", help="NATS server URL")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--demo", action="store_true", help="Run demo scenario")
    args = parser.parse_args()
    
    # Create and initialize orchestrator
    orchestrator = CommunicationSystemOrchestrator(
        config_file=args.config,
        nats_url=args.nats_url
    )
    
    if not await orchestrator.initialize():
        logger.error("Failed to initialize communication system")
        return 1
    
    try:
        if args.test:
            # Run test mode
            logger.info("🧪 Running in test mode...")
            
            # Create some test tasks
            test_tasks = [
                ("data_processing", "Process dataset A", {"dataset": "A"}),
                ("analysis", "Analyze results", {"type": "statistical"}),
                ("reporting", "Generate report", {"format": "PDF"}),
                ("monitoring", "System health check", {"check_type": "comprehensive"})
            ]
            
            for task_type, description, data in test_tasks:
                await orchestrator.create_task(task_type, description, data)
                await asyncio.sleep(1)
            
            # Run for 60 seconds then shutdown
            await asyncio.sleep(60)
            
        elif args.demo:
            # Run demo scenario
            logger.info("🎭 Running demo scenario...")
            
            # Create demo agents and tasks
            demo_tasks = []
            for i in range(20):
                task_id = await orchestrator.create_task(
                    task_type="demo_task",
                    description=f"Demo task {i+1}",
                    data={"demo_index": i, "complexity": "medium"},
                    priority=TaskPriority.MEDIUM
                )
                demo_tasks.append(task_id)
                
                if i % 5 == 0:  # Add some variety
                    await asyncio.sleep(2)
            
            logger.info(f"Created {len(demo_tasks)} demo tasks")
            
            # Run demo for 5 minutes
            await asyncio.sleep(300)
            
        else:
            # Run normally
            await orchestrator.run_forever()
        
        return 0
        
    except Exception as e:
        logger.error(f"System error: {e}")
        return 1
    finally:
        await orchestrator.shutdown()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
