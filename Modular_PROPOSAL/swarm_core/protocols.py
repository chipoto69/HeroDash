#!/usr/bin/env python3
"""
Standard message protocols for agent communication
Language-agnostic JSON protocol that any system can implement
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import json
import uuid
from datetime import datetime

class MessageType(Enum):
    """Standard message types for agent communication"""
    TASK = "task"
    RESULT = "result"
    SYNC = "sync"
    HEARTBEAT = "heartbeat"
    REGISTER = "register"
    DISCOVER = "discover"
    BROADCAST = "broadcast"

class Priority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class Message:
    """
    Standard message format for inter-agent communication
    Designed to be JSON-serializable and language-agnostic
    """
    id: str
    type: MessageType
    from_agent: str
    to_agent: str  # Can be agent_id or "*" for broadcast
    data: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.meta:
            self.meta = {}
    
    def to_json(self) -> str:
        """Serialize message to JSON string"""
        return json.dumps(self.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, MessageType) else self.type,
            "from": self.from_agent,
            "to": self.to_agent,
            "data": self.data,
            "meta": self.meta,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize message from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        msg_type = data.get("type", "task")
        if not isinstance(msg_type, MessageType):
            msg_type = MessageType(msg_type)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=msg_type,
            from_agent=data.get("from", "unknown"),
            to_agent=data.get("to", "*"),
            data=data.get("data", {}),
            meta=data.get("meta", {}),
            timestamp=data.get("timestamp")
        )

class Protocol:
    """
    Protocol helpers for creating standard messages
    """
    
    @staticmethod
    def task(from_agent: str, to_agent: str, task_data: Dict[str, Any], 
             priority: Priority = Priority.MEDIUM, timeout: int = 300) -> Message:
        """Create a task message"""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.TASK,
            from_agent=from_agent,
            to_agent=to_agent,
            data=task_data,
            meta={"priority": priority.value, "timeout": timeout}
        )
    
    @staticmethod
    def result(from_agent: str, to_agent: str, task_id: str, 
               result_data: Dict[str, Any], success: bool = True) -> Message:
        """Create a result message"""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESULT,
            from_agent=from_agent,
            to_agent=to_agent,
            data={"task_id": task_id, "result": result_data, "success": success},
            meta={}
        )
    
    @staticmethod
    def heartbeat(agent_id: str, status: str = "healthy", 
                  metrics: Optional[Dict[str, Any]] = None) -> Message:
        """Create a heartbeat message"""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.HEARTBEAT,
            from_agent=agent_id,
            to_agent="*",
            data={"status": status, "metrics": metrics or {}},
            meta={}
        )
    
    @staticmethod
    def register(agent_id: str, capabilities: List[str], 
                 metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Create an agent registration message"""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.REGISTER,
            from_agent=agent_id,
            to_agent="swarm",
            data={"capabilities": capabilities, "metadata": metadata or {}},
            meta={}
        )
    
    @staticmethod
    def sync(from_agent: str, checkpoint: str, ready: bool = True) -> Message:
        """Create a synchronization message"""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.SYNC,
            from_agent=from_agent,
            to_agent="*",
            data={"checkpoint": checkpoint, "ready": ready},
            meta={}
        )
    
    @staticmethod
    def broadcast(from_agent: str, data: Dict[str, Any]) -> Message:
        """Create a broadcast message to all agents"""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.BROADCAST,
            from_agent=from_agent,
            to_agent="*",
            data=data,
            meta={}
        )