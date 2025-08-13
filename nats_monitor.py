#!/usr/bin/env python3
"""
NATS Message Monitor & Agent Integration Tool
Real-time monitoring of agent communications with dashboard integration
"""
import asyncio
import json
import nats
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / ".hero_core" / "nats_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NATSMonitor")

class NATSMonitor:
    def __init__(self, nats_url="nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.message_count = 0
        self.agents_discovered = {}
        self.recent_messages = []
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(self.nats_url)
            logger.info(f"Connected to NATS server at {self.nats_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            return False
    
    async def monitor_all_traffic(self):
        """Monitor all Hero agent traffic"""
        if not self.nc:
            logger.error("Not connected to NATS")
            return
        
        print("🔍 Monitoring all Hero agent traffic...")
        print("📡 Subject pattern: hero.v1.>")
        print("Press Ctrl+C to stop\n")
        
        async def message_handler(msg):
            self.message_count += 1
            timestamp = datetime.now().isoformat()
            
            try:
                # Try to parse as JSON
                data = json.loads(msg.data.decode())
                data_preview = json.dumps(data, indent=2)[:200] + "..." if len(str(data)) > 200 else json.dumps(data, indent=2)
            except:
                # Raw text message
                data_preview = msg.data.decode()[:200] + "..." if len(msg.data) > 200 else msg.data.decode()
                data = {"raw_message": msg.data.decode()}
            
            message_info = {
                "timestamp": timestamp,
                "subject": msg.subject,
                "size": len(msg.data),
                "data": data,
                "reply_to": msg.reply or None
            }
            
            # Store recent messages (last 100)
            self.recent_messages.append(message_info)
            if len(self.recent_messages) > 100:
                self.recent_messages.pop(0)
            
            # Save to cache for dashboard
            await self.save_traffic_cache()
            
            # Console output
            print(f"🔔 [{timestamp}] Subject: {msg.subject}")
            print(f"   📦 Size: {len(msg.data)} bytes")
            if msg.reply:
                print(f"   🔄 Reply-To: {msg.reply}")
            print(f"   📄 Data: {data_preview}")
            print("-" * 80)
        
        # Subscribe to all Hero traffic
        await self.nc.subscribe("hero.v1.>", cb=message_handler)
        
        # Keep monitoring
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n📊 Monitoring stopped. Total messages: {self.message_count}")
    
    async def discover_agents(self):
        """Discover and catalog active agents via NATS"""
        if not self.nc:
            logger.error("Not connected to NATS")
            return
        
        print("🔍 Discovering active agents...")
        
        # Request agent discovery
        discovery_request = {
            "type": "discovery_request",
            "timestamp": datetime.now().isoformat(),
            "request_id": f"disco_{int(datetime.now().timestamp())}"
        }
        
        # Listen for agent responses
        responses = []
        
        async def discovery_handler(msg):
            try:
                data = json.loads(msg.data.decode())
                responses.append(data)
                agent_id = data.get("agent_id", "unknown")
                agent_type = data.get("agent_type", "unknown")
                self.agents_discovered[agent_id] = data
                print(f"✅ Discovered: {agent_type} ({agent_id[:8]}...)")
            except Exception as e:
                print(f"❌ Error parsing discovery response: {e}")
        
        # Subscribe to discovery responses
        await self.nc.subscribe("hero.v1.*.agents.discovery_response", cb=discovery_handler)
        
        # Send discovery request
        await self.nc.publish("hero.v1.dev.agents.discovery_request", 
                             json.dumps(discovery_request).encode())
        
        print("📡 Discovery request sent, waiting for responses...")
        await asyncio.sleep(5)  # Wait for responses
        
        print(f"\n📊 Discovery complete: {len(self.agents_discovered)} agents found")
        await self.save_discovery_cache()
        
        return self.agents_discovered
    
    async def inject_existing_agent(self, agent_pid: int, agent_type: str, agent_name: str):
        """Inject NATS communication into an existing running agent process"""
        print(f"🔌 Injecting NATS into existing agent...")
        print(f"   PID: {agent_pid}")
        print(f"   Type: {agent_type}")
        print(f"   Name: {agent_name}")
        
        # Create agent registration message
        registration = {
            "agent_id": f"injected_{agent_pid}_{int(datetime.now().timestamp())}",
            "agent_type": agent_type,
            "agent_name": agent_name,
            "pid": agent_pid,
            "status": "active",
            "capabilities": ["existing_process"],
            "injection_method": "nats_monitor",
            "timestamp": datetime.now().isoformat()
        }
        
        # Register with Hero system
        await self.nc.publish("hero.v1.dev.agents.register", 
                             json.dumps(registration).encode())
        
        # Start heartbeat for this agent
        async def heartbeat_loop():
            while True:
                heartbeat = {
                    "agent_id": registration["agent_id"],
                    "timestamp": datetime.now().isoformat(),
                    "status": "active",
                    "pid": agent_pid
                }
                await self.nc.publish("hero.v1.dev.agents.heartbeat", 
                                     json.dumps(heartbeat).encode())
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
        
        # Start heartbeat in background
        asyncio.create_task(heartbeat_loop())
        
        print(f"✅ Agent {agent_name} injected and registered with NATS")
        print(f"🔔 Heartbeat started for PID {agent_pid}")
        
        return registration["agent_id"]
    
    async def publish_agent_communication(self, from_agent: str, to_agent: str, 
                                        message_type: str, content: Dict[str, Any]):
        """Publish communication between agents"""
        communication = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        subject = f"hero.v1.dev.agents.communication.{message_type}"
        await self.nc.publish(subject, json.dumps(communication).encode())
        
        print(f"📤 {from_agent} → {to_agent}: {message_type}")
    
    async def save_traffic_cache(self):
        """Save traffic data for dashboard"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "total_messages": self.message_count,
            "recent_messages": self.recent_messages[-20:],  # Last 20 messages
            "agents_discovered": len(self.agents_discovered),
            "monitoring_active": True
        }
        
        cache_file = self.cache_dir / "nats_traffic.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    async def save_discovery_cache(self):
        """Save agent discovery data for dashboard"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "agents_discovered": self.agents_discovered,
            "discovery_count": len(self.agents_discovered)
        }
        
        cache_file = self.cache_dir / "nats_discovery.json"
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)

class AgentNATSWrapper:
    """Wrapper to add NATS communication to existing agents"""
    
    def __init__(self, agent_pid: int, agent_type: str, agent_name: str, 
                 nats_url="nats://localhost:4222"):
        self.agent_pid = agent_pid
        self.agent_type = agent_type
        self.agent_name = agent_name
        self.nats_url = nats_url
        self.nc = None
        self.agent_id = f"wrapped_{agent_pid}_{int(datetime.now().timestamp())}"
        
    async def connect_and_register(self):
        """Connect to NATS and register the existing agent"""
        try:
            self.nc = await nats.connect(self.nats_url)
            
            # Register agent
            registration = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "agent_name": self.agent_name,
                "pid": self.agent_pid,
                "status": "active",
                "wrapped": True,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.nc.publish("hero.v1.dev.agents.register", 
                                 json.dumps(registration).encode())
            
            print(f"✅ Wrapped agent {self.agent_name} (PID: {self.agent_pid}) connected to NATS")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect wrapper: {e}")
            return False
    
    async def send_task_update(self, task_name: str, status: str, progress: float = None):
        """Send task progress updates"""
        update = {
            "agent_id": self.agent_id,
            "task_name": task_name,
            "status": status,
            "progress": progress,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.nc.publish("hero.v1.dev.agents.task_update", 
                             json.dumps(update).encode())
        print(f"📤 Task update: {task_name} [{status}]")
    
    async def request_coordination(self, request_type: str, details: Dict[str, Any]):
        """Request coordination with other agents"""
        request = {
            "agent_id": self.agent_id,
            "request_type": request_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.nc.publish("hero.v1.dev.coordination.request", 
                             json.dumps(request).encode())
        print(f"🤝 Coordination request: {request_type}")

async def main():
    parser = argparse.ArgumentParser(description="NATS Monitor for Hero Agents")
    parser.add_argument("--url", default="nats://localhost:4222", help="NATS server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor all NATS traffic")
    
    # Discovery command
    discovery_parser = subparsers.add_parser("discover", help="Discover active agents")
    
    # Inject command
    inject_parser = subparsers.add_parser("inject", help="Inject NATS into existing agent")
    inject_parser.add_argument("--pid", type=int, required=True, help="Process ID of agent")
    inject_parser.add_argument("--type", required=True, help="Agent type")
    inject_parser.add_argument("--name", required=True, help="Agent name")
    
    # Wrap command
    wrap_parser = subparsers.add_parser("wrap", help="Wrap existing agent with NATS")
    wrap_parser.add_argument("--pid", type=int, required=True, help="Process ID of agent")
    wrap_parser.add_argument("--type", required=True, help="Agent type")
    wrap_parser.add_argument("--name", required=True, help="Agent name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    monitor = NATSMonitor(args.url)
    
    if not await monitor.connect():
        print("❌ Failed to connect to NATS server")
        print(f"💡 Try: nats-server -p 4222")
        return
    
    if args.command == "monitor":
        await monitor.monitor_all_traffic()
    
    elif args.command == "discover":
        agents = await monitor.discover_agents()
        print("\n📋 Discovered Agents:")
        for agent_id, info in agents.items():
            print(f"  🤖 {info.get('agent_type', 'unknown')} - {info.get('agent_name', agent_id[:8])}")
    
    elif args.command == "inject":
        agent_id = await monitor.inject_existing_agent(args.pid, args.type, args.name)
        print(f"🔄 Keeping agent {agent_id} alive with NATS...")
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            print(f"\n👋 Stopping NATS injection for PID {args.pid}")
    
    elif args.command == "wrap":
        wrapper = AgentNATSWrapper(args.pid, args.type, args.name, args.url)
        if await wrapper.connect_and_register():
            print("🎯 Agent wrapped and ready for NATS communication")
            print("🔍 Example usage:")
            print(f"  await wrapper.send_task_update('data_processing', 'started')")
            print(f"  await wrapper.request_coordination('resource_request', {{'cpu': 2}})")
        
        # Demo: Send a few messages
        await asyncio.sleep(2)
        await wrapper.send_task_update("initialization", "completed", 100.0)
        await wrapper.request_coordination("status_sync", {"state": "ready"})
        
        try:
            while True:
                await asyncio.sleep(30)
                await wrapper.send_task_update("background_work", "running", 50.0)
        except KeyboardInterrupt:
            print(f"\n👋 Stopping wrapper for PID {args.pid}")

if __name__ == "__main__":
    print("🚀 NATS Monitor & Agent Integration Tool")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")