#!/usr/bin/env python3
"""
NATS transport implementation
Requires: pip install nats-py
"""

import asyncio
import json
from typing import Callable, Optional, Dict, Any
from .base import Transport
from ..protocols import Message

try:
    import nats
    from nats.js import JetStreamContext
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

class NATSTransport(Transport):
    """
    NATS/JetStream transport implementation
    High-performance distributed messaging
    """
    
    def __init__(self):
        if not NATS_AVAILABLE:
            raise ImportError("NATS not available. Install with: pip install nats-py")
        
        self.nc = None
        self.js = None
        self.subscriptions = {}
        
    async def connect(self, url: str = "nats://localhost:4222", **kwargs) -> None:
        """Connect to NATS server"""
        self.nc = await nats.connect(url, **kwargs)
        
        # Enable JetStream if requested
        if kwargs.get("jetstream", False):
            self.js = self.nc.jetstream()
    
    async def disconnect(self) -> None:
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.close()
    
    async def send(self, message: Message) -> None:
        """Send a message via NATS"""
        subject = self._get_subject(message)
        payload = message.to_json().encode()
        await self.nc.publish(subject, payload)
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a NATS subject"""
        async def nats_handler(msg):
            try:
                message = Message.from_json(msg.data.decode())
                response = await handler(message)
                
                # If handler returns a response, send it back
                if response and msg.reply:
                    await self.nc.publish(msg.reply, response.to_json().encode())
                    
            except Exception as e:
                print(f"Error handling message: {e}")
        
        sub = await self.nc.subscribe(topic, cb=nats_handler)
        self.subscriptions[topic] = sub
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic"""
        if topic in self.subscriptions:
            await self.subscriptions[topic].unsubscribe()
            del self.subscriptions[topic]
    
    async def request(self, message: Message, timeout: float = 5.0) -> Optional[Message]:
        """Send request and wait for response"""
        subject = self._get_subject(message)
        payload = message.to_json().encode()
        
        try:
            response = await self.nc.request(subject, payload, timeout=timeout)
            return Message.from_json(response.data.decode())
        except asyncio.TimeoutError:
            return None
    
    async def health_check(self) -> bool:
        """Check NATS connection health"""
        return self.nc and not self.nc.is_closed
    
    def _get_subject(self, message: Message) -> str:
        """Convert message to NATS subject"""
        if message.to_agent == "*":
            return f"swarm.broadcast.{message.type.value}"
        else:
            return f"swarm.agent.{message.to_agent}.{message.type.value}"