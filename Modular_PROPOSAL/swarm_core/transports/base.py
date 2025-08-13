#!/usr/bin/env python3
"""
Abstract transport interface - implement this to add new transport layers
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any
from ..protocols import Message

class Transport(ABC):
    """
    Abstract transport layer interface
    Implement this to add support for different message brokers
    """
    
    @abstractmethod
    async def connect(self, url: str, **kwargs) -> None:
        """Connect to the transport layer"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the transport layer"""
        pass
    
    @abstractmethod
    async def send(self, message: Message) -> None:
        """Send a message"""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to a topic with a message handler"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic"""
        pass
    
    @abstractmethod
    async def request(self, message: Message, timeout: float = 5.0) -> Optional[Message]:
        """Send a message and wait for response"""
        pass
    
    async def health_check(self) -> bool:
        """Check if transport is healthy"""
        return True