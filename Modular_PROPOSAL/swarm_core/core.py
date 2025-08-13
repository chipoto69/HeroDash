#!/usr/bin/env python3
"""
Minimal Swarm Core - The heart of the inter-agent communication system
~200 lines of essential code for agent swarm coordination
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import uuid
from .agent import Agent
from .protocols import Message, MessageType, Protocol
from .transports import get_transport, Transport

@dataclass
class SwarmConfig:
    """Minimal swarm configuration"""
    transport: str = "memory"  # "memory", "nats", etc.
    transport_url: str = ""    # Connection URL if needed
    auto_discover: bool = True # Auto-discover agents
    heartbeat_interval: int = 30  # Seconds between heartbeats

class Swarm:
    """
    Minimal swarm coordinator
    Handles agent registration, message routing, and lifecycle
    """
    
    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.agents: Dict[str, Agent] = {}
        self.transport: Optional[Transport] = None
        self.running = False
        self._tasks = set()
        
    async def add_agent(self, agent: Agent) -> None:
        """Add an agent to the swarm"""
        self.agents[agent.id] = agent
        
        # Register agent if swarm is running
        if self.running:
            await self._register_agent(agent)
    
    async def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the swarm"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.stop()
            del self.agents[agent_id]
    
    async def start(self) -> None:
        """Start the swarm"""
        if self.running:
            return
            
        # Initialize transport
        self.transport = get_transport(self.config.transport)
        await self.transport.connect(self.config.transport_url)
        
        # Subscribe to broadcast messages
        await self.transport.subscribe("broadcast", self._handle_broadcast)
        await self.transport.subscribe("type.discover", self._handle_discover)
        
        # Start all agents
        for agent in self.agents.values():
            await self._register_agent(agent)
        
        # Start background tasks
        if self.config.heartbeat_interval > 0:
            self._tasks.add(
                asyncio.create_task(self._heartbeat_loop())
            )
        
        self.running = True
    
    async def stop(self) -> None:
        """Stop the swarm"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
        
        # Disconnect transport
        if self.transport:
            await self.transport.disconnect()
    
    async def send(self, message: Message) -> None:
        """Send a message through the swarm"""
        if not self.transport:
            raise RuntimeError("Swarm not started")
        await self.transport.send(message)
    
    async def broadcast(self, from_agent: str, data: Dict[str, Any]) -> None:
        """Broadcast a message to all agents"""
        message = Protocol.broadcast(from_agent, data)
        await self.send(message)
    
    async def task(self, from_agent: str, to_agent: str, 
                   task_data: Dict[str, Any], timeout: float = 30.0) -> Optional[Message]:
        """Send a task and wait for result"""
        message = Protocol.task(from_agent, to_agent, task_data)
        
        if self.config.transport == "memory":
            # Direct routing for in-memory transport
            if to_agent in self.agents:
                result = await self.agents[to_agent].process(message)
                return result
        else:
            # Use transport request/response
            return await self.transport.request(message, timeout)
    
    async def sync(self, checkpoint: str, timeout: float = 10.0) -> bool:
        """Synchronize all agents at a checkpoint"""
        ready_agents = set()
        
        # Send sync request to all agents
        sync_msg = Protocol.sync("swarm", checkpoint)
        await self.broadcast("swarm", sync_msg.data)
        
        # Wait for all agents to be ready
        start_time = asyncio.get_event_loop().time()
        while len(ready_agents) < len(self.agents):
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            
            # Check agent responses
            # In production, this would listen for sync responses
            await asyncio.sleep(0.1)
        
        return True
    
    # Private methods
    
    async def _register_agent(self, agent: Agent) -> None:
        """Register an agent with the swarm"""
        await agent.start()
        
        # Subscribe to agent-specific messages
        agent_topic = f"agent.{agent.id}"
        await self.transport.subscribe(
            agent_topic,
            lambda msg: self._route_to_agent(agent.id, msg)
        )
        
        # Subscribe to capability-based routing
        capabilities = await agent.capabilities()
        for capability in capabilities:
            await self.transport.subscribe(
                f"capability.{capability}",
                lambda msg: self._route_to_agent(agent.id, msg)
            )
    
    async def _route_to_agent(self, agent_id: str, message: Message) -> Optional[Message]:
        """Route a message to a specific agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return await agent.process(message)
        return None
    
    async def _handle_broadcast(self, message: Message) -> None:
        """Handle broadcast messages"""
        # Send to all local agents
        for agent in self.agents.values():
            asyncio.create_task(agent.process(message))
    
    async def _handle_discover(self, message: Message) -> Optional[Message]:
        """Handle discovery requests"""
        # Respond with list of local agents
        agent_list = []
        for agent in self.agents.values():
            capabilities = await agent.capabilities()
            agent_list.append({
                "id": agent.id,
                "capabilities": capabilities
            })
        
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.DISCOVER,
            from_agent="swarm",
            to_agent=message.from_agent,
            data={"agents": agent_list}
        )
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats for all agents"""
        while self.running:
            try:
                for agent in self.agents.values():
                    health = await agent.health()
                    heartbeat = Protocol.heartbeat(
                        agent.id,
                        health.get("status", "unknown"),
                        health
                    )
                    await self.send(heartbeat)
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(5)