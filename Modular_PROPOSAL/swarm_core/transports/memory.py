#!/usr/bin/env python3
"""
In-memory transport for testing and local development
Zero dependencies, perfect for unit tests
"""

import asyncio
from typing import Callable, Optional, Dict, Any, List
from collections import defaultdict
from .base import Transport
from ..protocols import Message

class MemoryTransport(Transport):
    """
    In-memory message transport
    Perfect for testing and single-process swarms
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.response_futures: Dict[str, asyncio.Future] = {}
        self.connected = False
        self._processor_task = None
        
    async def connect(self, url: str = "memory://", **kwargs) -> None:
        """Connect to in-memory transport"""
        self.connected = True
        self._processor_task = asyncio.create_task(self._process_messages())
        
    async def disconnect(self) -> None:
        """Disconnect from in-memory transport"""
        self.connected = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
    
    async def send(self, message: Message) -> None:
        """Send a message to the queue"""
        if not self.connected:
            raise RuntimeError("Transport not connected")
        await self.message_queue.put(message)
    
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic"""
        self.subscribers[topic].append(handler)
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            del self.subscribers[topic]
    
    async def request(self, message: Message, timeout: float = 5.0) -> Optional[Message]:
        """Send a message and wait for response"""
        future = asyncio.Future()
        self.response_futures[message.id] = future
        
        await self.send(message)
        
        try:
            response = await asyncio.wait_for(future, timeout)
            return response
        except asyncio.TimeoutError:
            return None
        finally:
            if message.id in self.response_futures:
                del self.response_futures[message.id]
    
    async def _process_messages(self):
        """Process messages from the queue"""
        while self.connected:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=0.1
                )
                
                # Route to subscribers
                topics = self._get_matching_topics(message)
                for topic in topics:
                    for handler in self.subscribers.get(topic, []):
                        asyncio.create_task(self._handle_message(handler, message))
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")
    
    async def _handle_message(self, handler: Callable, message: Message):
        """Handle a message with a subscriber"""
        try:
            response = await handler(message)
            
            # If this is a response to a request, fulfill the future
            if response and message.id in self.response_futures:
                self.response_futures[message.id].set_result(response)
                
        except Exception as e:
            print(f"Handler error: {e}")
    
    def _get_matching_topics(self, message: Message) -> List[str]:
        """Get topics that match this message"""
        topics = []
        
        # Direct agent targeting
        if message.to_agent != "*":
            topics.append(f"agent.{message.to_agent}")
        
        # Broadcast messages
        if message.to_agent == "*":
            topics.append("broadcast")
        
        # Message type topics
        topics.append(f"type.{message.type.value}")
        
        # Wildcard topic
        topics.append("*")
        
        return topics