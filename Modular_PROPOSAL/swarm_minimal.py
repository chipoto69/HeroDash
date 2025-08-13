#!/usr/bin/env python3
"""
Swarm Minimal - Complete agent swarm system in a single file
Zero dependencies except asyncio (NATS optional)

Usage:
    from swarm_minimal import Swarm, Agent
    
    class MyAgent(Agent):
        async def process(self, message):
            return {"result": "processed"}
    
    swarm = Swarm()
    swarm.add_agent(MyAgent())
    asyncio.run(swarm.start())
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Callable

# === PROTOCOLS ===

class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    SYNC = "sync"
    HEARTBEAT = "heartbeat"
    REGISTER = "register"
    DISCOVER = "discover"
    BROADCAST = "broadcast"

@dataclass
class Message:
    """Standard message format"""
    id: str
    type: MessageType
    from_agent: str
    to_agent: str
    data: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        self.id = self.id or str(uuid.uuid4())
        self.timestamp = self.timestamp or datetime.utcnow().isoformat()
        self.meta = self.meta or {}

# === AGENT ===

class Agent(ABC):
    """Minimal agent - just implement process()"""
    
    def __init__(self, agent_id: Optional[str] = None):
        self.id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self._running = False
    
    @abstractmethod
    async def process(self, message: Message) -> Optional[Message]:
        """Process a message - the only required method"""
        pass
    
    async def capabilities(self) -> List[str]:
        return ["general"]
    
    async def health(self) -> Dict[str, Any]:
        return {"status": "healthy", "agent_id": self.id}
    
    async def start(self):
        self._running = True
    
    async def stop(self):
        self._running = False

# === TRANSPORT ===

class MemoryTransport:
    """In-memory transport for single-process swarms"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.queue = asyncio.Queue()
        self.running = False
        
    async def start(self):
        self.running = True
        asyncio.create_task(self._process_messages())
    
    async def stop(self):
        self.running = False
    
    async def send(self, message: Message):
        await self.queue.put(message)
    
    async def subscribe(self, topic: str, handler: Callable):
        self.subscribers[topic].append(handler)
    
    async def _process_messages(self):
        while self.running:
            try:
                message = await asyncio.wait_for(self.queue.get(), 0.1)
                
                # Route to subscribers
                if message.to_agent == "*":
                    topics = ["broadcast", f"type.{message.type.value}"]
                else:
                    topics = [f"agent.{message.to_agent}", f"type.{message.type.value}"]
                
                for topic in topics:
                    for handler in self.subscribers.get(topic, []):
                        asyncio.create_task(handler(message))
                        
            except asyncio.TimeoutError:
                continue

# === SWARM ===

class Swarm:
    """Minimal swarm coordinator"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.transport = MemoryTransport()
        self.running = False
    
    def add_agent(self, agent: Agent):
        """Add an agent to the swarm"""
        self.agents[agent.id] = agent
        return self
    
    async def start(self):
        """Start the swarm"""
        if self.running:
            return
        
        # Start transport
        await self.transport.start()
        
        # Register agents
        for agent in self.agents.values():
            await agent.start()
            
            # Subscribe to agent messages
            await self.transport.subscribe(
                f"agent.{agent.id}",
                lambda msg, a=agent: a.process(msg)
            )
        
        # Subscribe to broadcasts
        await self.transport.subscribe(
            "broadcast",
            self._handle_broadcast
        )
        
        self.running = True
        
        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """Stop the swarm"""
        self.running = False
        
        for agent in self.agents.values():
            await agent.stop()
        
        await self.transport.stop()
    
    async def send(self, message: Message):
        """Send a message"""
        await self.transport.send(message)
    
    async def task(self, from_agent: str, to_agent: str, data: Dict[str, Any]) -> Optional[Message]:
        """Send task to agent"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.TASK,
            from_agent=from_agent,
            to_agent=to_agent,
            data=data
        )
        
        # Direct execution for in-memory
        if to_agent in self.agents:
            return await self.agents[to_agent].process(message)
        
        await self.send(message)
        return None
    
    async def broadcast(self, from_agent: str, data: Dict[str, Any]):
        """Broadcast to all agents"""
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.BROADCAST,
            from_agent=from_agent,
            to_agent="*",
            data=data
        )
        await self.send(message)
    
    async def _handle_broadcast(self, message: Message):
        """Handle broadcast messages"""
        for agent in self.agents.values():
            asyncio.create_task(agent.process(message))

# === HELPERS ===

class SimpleAgent(Agent):
    """Simple functional agent"""
    
    def __init__(self, agent_id: Optional[str] = None, handler: Optional[Callable] = None):
        super().__init__(agent_id)
        self.handler = handler or self._default_handler
    
    async def process(self, message: Message) -> Optional[Message]:
        if message.type == MessageType.TASK:
            try:
                result = await self.handler(message.data)
                return Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.RESULT,
                    from_agent=self.id,
                    to_agent=message.from_agent,
                    data={"task_id": message.id, "result": result}
                )
            except Exception as e:
                return Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.RESULT,
                    from_agent=self.id,
                    to_agent=message.from_agent,
                    data={"task_id": message.id, "error": str(e)}
                )
        return None
    
    async def _default_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"processed": data}

# === EXAMPLE ===

async def example():
    """Example usage"""
    
    # Create swarm
    swarm = Swarm()
    
    # Add agents
    swarm.add_agent(SimpleAgent("worker1"))
    swarm.add_agent(SimpleAgent("worker2"))
    
    # Custom agent
    class AnalyzerAgent(Agent):
        async def process(self, message: Message) -> Optional[Message]:
            if message.type == MessageType.TASK:
                # Analyze the task
                word_count = len(message.data.get("text", "").split())
                return Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.RESULT,
                    from_agent=self.id,
                    to_agent=message.from_agent,
                    data={"word_count": word_count}
                )
            return None
    
    swarm.add_agent(AnalyzerAgent("analyzer"))
    
    # Start swarm in background
    asyncio.create_task(swarm.start())
    await asyncio.sleep(0.1)  # Let it initialize
    
    # Send tasks
    result = await swarm.task("user", "analyzer", {"text": "Hello world from swarm"})
    print(f"Analysis result: {result.data if result else 'No result'}")
    
    # Broadcast
    await swarm.broadcast("user", {"announcement": "System update"})
    
    # Stop
    await swarm.stop()

if __name__ == "__main__":
    asyncio.run(example())