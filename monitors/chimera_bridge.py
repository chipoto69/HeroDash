#!/usr/bin/env python3
"""
Chimera Bridge for Hero Command Centre
Bridges Hero Dashboard with Frontline/Chimera AI agent framework
Outputs: ~/.hero_core/cache/chimera_integration.json
"""

import json
import os
import time
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import sys
from dataclasses import dataclass, asdict

# Add path for Hero monitors
sys.path.append(str(Path(__file__).parent))

try:
    from langsmith_tracer import get_tracer, trace_hero_function, trace_agent_workflow
    from agent_coordinator import get_coordinator, TaskPriority
except ImportError:
    def get_tracer():
        return None
    def trace_hero_function(name=None, agent_type="chimera-bridge"):
        def decorator(func):
            return func
        return decorator
    def trace_agent_workflow(name, agent_type, inputs=None):
        return None
    def get_coordinator():
        return None
    class TaskPriority:
        LOW = 1
        NORMAL = 2
        HIGH = 3

# Try to import NATS and other Chimera dependencies
try:
    import nats
    from nats.js import JetStreamContext
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    print("Warning: NATS not available. Install with: pip install nats-py")

try:
    import asyncio
    import aiofiles
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False


@dataclass
class ChimeraAgent:
    """Information about a Chimera agent"""
    name: str
    type: str
    status: str
    last_seen: datetime
    capabilities: List[str]
    performance_metrics: Dict[str, Any]
    nats_subject: str
    framework: str = "chimera"


class ChimeraBridge:
    """Bridge between Hero Dashboard and Chimera framework"""
    
    def __init__(self, chimera_base: str = "/Users/rudlord/q3/frontline"):
        self.chimera_base = Path(chimera_base)
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.integration_file = self.cache_dir / "chimera_integration.json"
        
        # NATS configuration
        self.nats_url = "nats://localhost:4222"
        self.nats_client = None
        self.jetstream = None
        
        # Agent tracking
        self.chimera_agents: Dict[str, ChimeraAgent] = {}
        self.nats_streams = {}
        self.last_sync = datetime.now()
        
        # Integration status
        self.integration_status = {
            "nats_connected": False,
            "chimera_detected": False,
            "agents_discovered": 0,
            "last_activity": None,
            "error_count": 0
        }
        
        # Initialize components
        self.tracer = get_tracer()
        self.coordinator = get_coordinator()
    
    async def _initialize_async(self):
        """Initialize async components"""
        try:
            await self._discover_chimera_environment()
            if NATS_AVAILABLE:
                await self._connect_nats()
            await self._register_chimera_agents()
        except Exception as e:
            print(f"Error initializing Chimera bridge: {e}")
    
    @trace_hero_function("discover_chimera_environment", "chimera-bridge")
    async def _discover_chimera_environment(self):
        """Discover Chimera environment and components"""
        try:
            # Check if Chimera base directory exists
            if not self.chimera_base.exists():
                print(f"Warning: Chimera base directory not found: {self.chimera_base}")
                return
            
            self.integration_status["chimera_detected"] = True
            
            # Look for key Chimera files
            chimera_files = [
                "chimera-knowledge-extraction",
                "chimera-ui",
                "libs/python/chimera_nats",
                "libs/python/chimera_langgraph",
                "docker-compose.yml"
            ]
            
            discovered = []
            for file_path in chimera_files:
                full_path = self.chimera_base / file_path
                if full_path.exists():
                    discovered.append(file_path)
            
            # Check for running services
            running_services = await self._check_running_services()
            
            # Update integration status
            self.integration_status.update({
                "discovered_components": discovered,
                "running_services": running_services,
                "last_discovery": datetime.now().isoformat()
            })
            
            print(f"✅ Discovered {len(discovered)} Chimera components")
            
        except Exception as e:
            print(f"Error discovering Chimera environment: {e}")
            self.integration_status["error_count"] += 1
    
    async def _check_running_services(self) -> List[str]:
        """Check for running Chimera services"""
        services = []
        
        # Check for common Chimera processes
        chimera_processes = [
            "nats-server",
            "langgraph",
            "chimera",
            "embedder",
            "retriever",
            "orchestrator"
        ]
        
        for process in chimera_processes:
            try:
                result = await asyncio.create_subprocess_exec(
                    "pgrep", "-f", process,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await result.communicate()
                
                if stdout.decode().strip():
                    services.append(process)
                    
            except Exception:
                pass
        
        return services
    
    @trace_hero_function("connect_nats", "chimera-bridge")
    async def _connect_nats(self):
        """Connect to NATS JetStream"""
        if not NATS_AVAILABLE:
            return
        
        try:
            self.nats_client = await nats.connect(self.nats_url)
            self.jetstream = self.nats_client.jetstream()
            
            self.integration_status["nats_connected"] = True
            print("✅ Connected to NATS JetStream")
            
            # Subscribe to agent activity streams
            await self._subscribe_to_agent_streams()
            
        except Exception as e:
            print(f"Warning: Could not connect to NATS: {e}")
            self.integration_status["nats_connected"] = False
    
    async def _subscribe_to_agent_streams(self):
        """Subscribe to NATS streams for agent monitoring"""
        if not self.jetstream:
            return
        
        try:
            # Subscribe to Chimera agent subjects
            subjects = [
                "chimera.v1.*.*.agents.>",
                "chi.v1.*.*.tasks.>",
                "hero.v1.*.*.status.>"
            ]
            
            for subject in subjects:
                await self.nats_client.subscribe(
                    subject,
                    cb=self._handle_nats_message
                )
                
        except Exception as e:
            print(f"Error subscribing to NATS streams: {e}")
    
    async def _handle_nats_message(self, msg):
        """Handle incoming NATS messages"""
        try:
            data = json.loads(msg.data.decode())
            subject_parts = msg.subject.split(".")
            
            # Extract agent information from message
            if "agents" in subject_parts:
                await self._process_agent_message(data, msg.subject)
            elif "tasks" in subject_parts:
                await self._process_task_message(data, msg.subject)
            
            self.integration_status["last_activity"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"Error processing NATS message: {e}")
            self.integration_status["error_count"] += 1
    
    async def _process_agent_message(self, data: Dict[str, Any], subject: str):
        """Process agent-related NATS messages"""
        try:
            agent_name = data.get("agent_name", "unknown")
            agent_type = data.get("agent_type", "generic")
            
            # Update or create agent record
            if agent_name not in self.chimera_agents:
                self.chimera_agents[agent_name] = ChimeraAgent(
                    name=agent_name,
                    type=agent_type,
                    status="active",
                    last_seen=datetime.now(),
                    capabilities=data.get("capabilities", []),
                    performance_metrics={},
                    nats_subject=subject
                )
            else:
                self.chimera_agents[agent_name].last_seen = datetime.now()
                self.chimera_agents[agent_name].status = data.get("status", "active")
            
            # Register with Hero coordinator if available
            if self.coordinator:
                self.coordinator.register_agent(
                    agent_name,
                    agent_type,
                    data.get("capabilities", []),
                    "chimera",
                    {"nats_subject": subject}
                )
            
        except Exception as e:
            print(f"Error processing agent message: {e}")
    
    async def _process_task_message(self, data: Dict[str, Any], subject: str):
        """Process task-related NATS messages"""
        try:
            task_name = data.get("task_name", "chimera_task")
            description = data.get("description", "")
            capabilities = data.get("required_capabilities", [])
            
            # Submit to Hero coordinator if available
            if self.coordinator:
                self.coordinator.submit_task(
                    task_name,
                    description,
                    capabilities,
                    TaskPriority.NORMAL,
                    data.get("inputs", {}),
                    {"source": "chimera", "nats_subject": subject}
                )
            
        except Exception as e:
            print(f"Error processing task message: {e}")
    
    @trace_hero_function("register_chimera_agents", "chimera-bridge")
    async def _register_chimera_agents(self):
        """Register discovered Chimera agents with Hero coordinator"""
        if not self.coordinator:
            return
        
        # Define known Chimera agent types and their capabilities
        known_agents = {
            "embedder": {
                "type": "knowledge_processor",
                "capabilities": ["text_embedding", "vector_search", "semantic_analysis"]
            },
            "retriever": {
                "type": "knowledge_retriever", 
                "capabilities": ["document_search", "context_retrieval", "relevance_ranking"]
            },
            "memory": {
                "type": "knowledge_manager",
                "capabilities": ["knowledge_storage", "memory_consolidation", "fact_extraction"]
            },
            "orchestrator": {
                "type": "workflow_coordinator",
                "capabilities": ["task_orchestration", "agent_coordination", "workflow_management"]
            },
            "ui_agent": {
                "type": "interface_agent",
                "capabilities": ["user_interaction", "visualization", "feedback_processing"]
            }
        }
        
        # Register known agents
        for agent_name, config in known_agents.items():
            try:
                agent_id = self.coordinator.register_agent(
                    f"chimera_{agent_name}",
                    config["type"],
                    config["capabilities"],
                    "chimera",
                    {"auto_discovered": True, "source": "chimera_bridge"}
                )
                
                # Create Chimera agent record
                self.chimera_agents[agent_name] = ChimeraAgent(
                    name=f"chimera_{agent_name}",
                    type=config["type"],
                    status="discovered",
                    last_seen=datetime.now(),
                    capabilities=config["capabilities"],
                    performance_metrics={},
                    nats_subject=f"chimera.v1.dev.hero.agents.{agent_name}.status"
                )
                
            except Exception as e:
                print(f"Error registering agent {agent_name}: {e}")
        
        self.integration_status["agents_discovered"] = len(self.chimera_agents)
    
    @trace_hero_function("send_hero_message", "chimera-bridge")
    async def send_hero_message_to_chimera(self, agent_name: str, message_type: str, 
                                         data: Dict[str, Any]):
        """Send message from Hero to Chimera agents via NATS"""
        if not self.nats_client:
            return False
        
        try:
            subject = f"hero.v1.dev.chimera.agents.{agent_name}.{message_type}"
            message = {
                "timestamp": datetime.now().isoformat(),
                "source": "hero_dashboard",
                "agent_name": agent_name,
                "message_type": message_type,
                "data": data
            }
            
            await self.nats_client.publish(
                subject,
                json.dumps(message).encode()
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending message to Chimera: {e}")
            return False
    
    @trace_hero_function("get_chimera_status", "chimera-bridge")
    def get_chimera_status(self) -> Dict[str, Any]:
        """Get comprehensive Chimera integration status"""
        # Clean up stale agents
        cutoff = datetime.now() - timedelta(minutes=10)
        active_agents = {
            name: agent for name, agent in self.chimera_agents.items()
            if agent.last_seen >= cutoff
        }
        
        # Calculate performance metrics
        total_agents = len(self.chimera_agents)
        active_count = len(active_agents)
        
        # Recent activity summary
        recent_activity = []
        for agent in list(self.chimera_agents.values())[-5:]:
            recent_activity.append({
                "agent": agent.name,
                "type": agent.type,
                "status": agent.status,
                "last_seen": agent.last_seen.isoformat()
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "integration_status": self.integration_status,
            "chimera_agents": {
                "total": total_agents,
                "active": active_count,
                "by_type": self._get_agent_type_breakdown(),
                "by_framework": {"chimera": total_agents}
            },
            "nats_integration": {
                "connected": self.integration_status["nats_connected"],
                "streams_monitored": len(self.nats_streams),
                "last_message": self.integration_status.get("last_activity")
            },
            "performance": {
                "discovery_rate": active_count / total_agents if total_agents > 0 else 0,
                "error_rate": self.integration_status["error_count"],
                "sync_frequency": "real-time" if self.nats_client else "polling"
            },
            "recent_activity": recent_activity,
            "hero_coordination": {
                "coordinator_available": self.coordinator is not None,
                "registered_with_hero": active_count,
                "tracing_enabled": self.tracer is not None
            }
        }
    
    def _get_agent_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of agents by type"""
        breakdown = {}
        for agent in self.chimera_agents.values():
            agent_type = agent.type
            breakdown[agent_type] = breakdown.get(agent_type, 0) + 1
        return breakdown
    
    @trace_hero_function("sync_with_chimera", "chimera-bridge")
    async def sync_with_chimera(self):
        """Manually sync with Chimera framework"""
        try:
            # Re-discover environment
            await self._discover_chimera_environment()
            
            # Reconnect NATS if needed
            if not self.integration_status["nats_connected"] and NATS_AVAILABLE:
                await self._connect_nats()
            
            # Update agent registrations
            await self._register_chimera_agents()
            
            self.last_sync = datetime.now()
            
        except Exception as e:
            print(f"Error during Chimera sync: {e}")
            self.integration_status["error_count"] += 1
    
    def save_status(self):
        """Save integration status to cache file"""
        try:
            status_data = self.get_chimera_status()
            with open(self.integration_file, 'w') as f:
                json.dump(status_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving Chimera status: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.nats_client:
            await self.nats_client.close()


# Global bridge instance
_bridge = None

def get_bridge() -> ChimeraBridge:
    """Get or create the global bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = ChimeraBridge()
    return _bridge


async def main_async():
    """Async main function"""
    bridge = get_bridge()
    
    # Run sync operation
    await bridge.sync_with_chimera()
    
    # Save status
    bridge.save_status()
    
    return bridge.get_chimera_status()


def main():
    """Main function for testing and standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hero Chimera Bridge")
    parser.add_argument("--status", action="store_true", help="Show integration status")
    parser.add_argument("--sync", action="store_true", help="Sync with Chimera framework")
    parser.add_argument("--test", action="store_true", help="Run integration test")
    parser.add_argument("--nats-test", action="store_true", help="Test NATS connection")
    
    args = parser.parse_args()
    
    if args.nats_test and NATS_AVAILABLE:
        async def test_nats():
            try:
                nc = await nats.connect("nats://localhost:4222")
                print("✅ NATS connection successful")
                await nc.close()
            except Exception as e:
                print(f"❌ NATS connection failed: {e}")
        
        asyncio.run(test_nats())
        return
    
    bridge = get_bridge()
    
    if args.status:
        status = bridge.get_chimera_status()
        print("🌉 Chimera Bridge Status:")
        print(json.dumps(status, indent=2, default=str))
    
    if args.sync:
        print("Syncing with Chimera framework...")
        if ASYNC_AVAILABLE:
            status = asyncio.run(main_async())
            print("✅ Sync completed")
            print(f"Discovered {status['chimera_agents']['total']} agents")
        else:
            print("❌ Async support not available")
    
    if args.test:
        print("Running Chimera integration test...")
        
        # Test basic functionality
        status = bridge.get_chimera_status()
        print(f"Integration detected: {status['integration_status']['chimera_detected']}")
        print(f"NATS connected: {status['integration_status']['nats_connected']}")
        print(f"Agents discovered: {status['chimera_agents']['total']}")
        
        # Test coordinator integration
        if bridge.coordinator:
            print("✅ Hero coordinator available")
        else:
            print("❌ Hero coordinator not available")
        
        print("✅ Integration test completed")
    
    if not any([args.status, args.sync, args.test, args.nats_test]):
        # Default: save current status
        bridge.save_status()
        print("💾 Saved Chimera integration status to cache")


if __name__ == "__main__":
    main()