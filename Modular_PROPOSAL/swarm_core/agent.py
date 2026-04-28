#!/usr/bin/env python3
"""
Lightweight Agent interface - minimal requirements for swarm participation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import asyncio
import uuid
from .protocols import Message, MessageType, Protocol

class Agent(ABC):
    """
    Minimal agent interface - just 3 methods to implement
    Everything else is optional
    """
    
    def __init__(self, agent_id: Optional[str] = None, capabilities: Optional[List[str]] = None):
        self.id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self._capabilities = capabilities or ["general"]
        self._running = False
        self._message_handlers = {}
        
    @abstractmethod
    async def process(self, message: Message) -> Optional[Message]:
        """
        Process a message and optionally return a response
        This is the only required method to implement
        """
        pass
    
    async def capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return self._capabilities
    
    async def health(self) -> Dict[str, Any]:
        """Return health status of the agent"""
        return {
            "status": "healthy" if self._running else "stopped",
            "agent_id": self.id,
            "capabilities": self._capabilities
        }
    
    # Optional lifecycle methods
    async def start(self) -> None:
        """Called when agent starts"""
        self._running = True
        
    async def stop(self) -> None:
        """Called when agent stops"""
        self._running = False

class SimpleAgent(Agent):
    """
    A simple functional agent that uses handlers for different message types
    """
    
    def __init__(self, agent_id: Optional[str] = None, 
                 capabilities: Optional[List[str]] = None,
                 task_handler: Optional[Callable] = None):
        super().__init__(agent_id, capabilities)
        self.task_handler = task_handler or self._default_task_handler
        self.results = {}
        
    async def process(self, message: Message) -> Optional[Message]:
        """Process message based on type"""
        if message.type == MessageType.TASK:
            return await self._process_task(message)
        elif message.type == MessageType.SYNC:
            return await self._process_sync(message)
        elif message.type == MessageType.DISCOVER:
            return await self._process_discover(message)
        return None
        
    async def _process_task(self, message: Message) -> Optional[Message]:
        """Process a task message"""
        try:
            result = await self.task_handler(message.data)
            return Protocol.result(
                from_agent=self.id,
                to_agent=message.from_agent,
                task_id=message.id,
                result_data=result,
                success=True
            )
        except Exception as e:
            return Protocol.result(
                from_agent=self.id,
                to_agent=message.from_agent,
                task_id=message.id,
                result_data={"error": str(e)},
                success=False
            )
    
    async def _process_sync(self, message: Message) -> Optional[Message]:
        """Process a sync message"""
        checkpoint = message.data.get("checkpoint")
        return Protocol.sync(
            from_agent=self.id,
            checkpoint=checkpoint,
            ready=True
        )
    
    async def _process_discover(self, message: Message) -> Optional[Message]:
        """Respond to discovery request"""
        return Protocol.register(
            agent_id=self.id,
            capabilities=self._capabilities,
            metadata={"type": "simple_agent"}
        )
    
    async def _default_task_handler(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default task handler - override this or provide custom handler"""
        return {"processed": task_data, "agent": self.id}

class ReactiveAgent(Agent):
    """
    Agent that reacts to messages with registered handlers
    """
    
    def __init__(self, agent_id: Optional[str] = None, capabilities: Optional[List[str]] = None):
        super().__init__(agent_id, capabilities)
        self.handlers = {
            MessageType.TASK: [],
            MessageType.BROADCAST: [],
            MessageType.SYNC: []
        }
    
    def on(self, message_type: MessageType, handler: Callable):
        """Register a handler for a message type"""
        if message_type in self.handlers:
            self.handlers[message_type].append(handler)
        return self
    
    async def process(self, message: Message) -> Optional[Message]:
        """Process message using registered handlers"""
        if message.type in self.handlers:
            for handler in self.handlers[message.type]:
                result = await handler(message)
                if result:
                    return result
        return None

class StatefulAgent(Agent):
    """
    Agent with built-in state management
    """
    
    def __init__(self, agent_id: Optional[str] = None, 
                 capabilities: Optional[List[str]] = None,
                 initial_state: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, capabilities)
        self.state = initial_state or {}
        self.state_lock = asyncio.Lock()
    
    async def get_state(self, key: str, default: Any = None) -> Any:
        """Thread-safe state getter"""
        async with self.state_lock:
            return self.state.get(key, default)
    
    async def set_state(self, key: str, value: Any) -> None:
        """Thread-safe state setter"""
        async with self.state_lock:
            self.state[key] = value
    
    async def update_state(self, updates: Dict[str, Any]) -> None:
        """Thread-safe state update"""
        async with self.state_lock:
            self.state.update(updates)
    
    async def process(self, message: Message) -> Optional[Message]:
        """Process message - to be implemented by subclasses"""
        raise NotImplementedError("StatefulAgent subclasses must implement process()")