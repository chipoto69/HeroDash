#!/usr/bin/env python3
"""
Swarm Core - Minimal inter-agent communication layer
A framework-agnostic system for synchronizing agent swarms
"""

from .core import Swarm, SwarmConfig
from .agent import Agent, Message, MessageType
from .protocols import Protocol

__version__ = "0.1.0"
__all__ = ["Swarm", "SwarmConfig", "Agent", "Message", "MessageType", "Protocol"]