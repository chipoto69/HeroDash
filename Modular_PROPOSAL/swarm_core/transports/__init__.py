#!/usr/bin/env python3
"""
Transport layer implementations
"""

from .base import Transport
from .memory import MemoryTransport

# Optional imports
try:
    from .nats import NATSTransport
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    NATSTransport = None

def get_transport(transport_type: str = "memory") -> Transport:
    """
    Factory function to get a transport instance
    
    Args:
        transport_type: Type of transport ("memory", "nats", etc.)
    
    Returns:
        Transport instance
    """
    if transport_type == "memory":
        return MemoryTransport()
    elif transport_type == "nats":
        if not NATS_AVAILABLE:
            raise ImportError("NATS transport not available. Install with: pip install nats-py")
        return NATSTransport()
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")

__all__ = ["Transport", "MemoryTransport", "get_transport"]
if NATS_AVAILABLE:
    __all__.append("NATSTransport")