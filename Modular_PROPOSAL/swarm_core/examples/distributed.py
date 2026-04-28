#!/usr/bin/env python3
"""
Distributed swarm example - Multi-agent task processing
"""

import asyncio
from typing import Dict, Any
from swarm_core import Swarm, Agent, Message, MessageType, SwarmConfig

class DataProcessor(Agent):
    """Agent that processes data"""
    
    async def process(self, message: Message) -> Message:
        if message.type == MessageType.TASK:
            data = message.data.get("data", [])
            operation = message.data.get("operation", "sum")
            
            if operation == "sum":
                result = sum(data)
            elif operation == "avg":
                result = sum(data) / len(data) if data else 0
            elif operation == "max":
                result = max(data) if data else None
            else:
                result = data
            
            return Message(
                id=message.id + "_result",
                type=MessageType.RESULT,
                from_agent=self.id,
                to_agent=message.from_agent,
                data={"result": result, "operation": operation}
            )
        return None

class Coordinator(Agent):
    """Agent that coordinates work distribution"""
    
    def __init__(self):
        super().__init__("coordinator")
        self.pending_tasks = {}
        
    async def process(self, message: Message) -> Message:
        if message.type == MessageType.TASK:
            # Split work among processors
            data = message.data.get("data", [])
            chunk_size = len(data) // 3
            
            # Create sub-tasks
            subtasks = []
            for i in range(3):
                start = i * chunk_size
                end = start + chunk_size if i < 2 else len(data)
                chunk = data[start:end]
                
                subtask = Message(
                    id=f"{message.id}_chunk_{i}",
                    type=MessageType.TASK,
                    from_agent=self.id,
                    to_agent=f"processor{i+1}",
                    data={"data": chunk, "operation": message.data.get("operation", "sum")}
                )
                subtasks.append(subtask)
            
            # Store for aggregation
            self.pending_tasks[message.id] = {
                "original": message,
                "subtasks": subtasks,
                "results": []
            }
            
            return None  # Will aggregate results later
            
        elif message.type == MessageType.RESULT:
            # Aggregate results
            for task_id, task_info in self.pending_tasks.items():
                for subtask in task_info["subtasks"]:
                    if message.data.get("task_id") == subtask.id:
                        task_info["results"].append(message.data["result"])
                        
                        # Check if all results are in
                        if len(task_info["results"]) == len(task_info["subtasks"]):
                            # Aggregate
                            final_result = sum(task_info["results"])
                            
                            return Message(
                                id=task_id + "_final",
                                type=MessageType.RESULT,
                                from_agent=self.id,
                                to_agent=task_info["original"].from_agent,
                                data={"result": final_result, "aggregated": True}
                            )
        return None

async def main():
    # Configure for distributed operation (use NATS in production)
    config = SwarmConfig(
        transport="memory",  # Change to "nats" for real distribution
        auto_discover=True,
        heartbeat_interval=10
    )
    
    # Create swarm
    swarm = Swarm(config)
    
    # Add coordinator
    swarm.add_agent(Coordinator())
    
    # Add processors
    for i in range(3):
        swarm.add_agent(DataProcessor(f"processor{i+1}"))
    
    # Start swarm
    await swarm.start()
    
    # Send a large task to coordinator
    large_data = list(range(1, 101))  # Numbers 1-100
    result = await swarm.task(
        "user",
        "coordinator", 
        {"data": large_data, "operation": "sum"}
    )
    
    if result:
        print(f"Distributed processing result: {result.data}")
        # Should print 5050 (sum of 1-100)
    
    # Test synchronization
    success = await swarm.sync("checkpoint1", timeout=5.0)
    print(f"Synchronization {'successful' if success else 'failed'}")
    
    # Stop swarm
    await swarm.stop()

if __name__ == "__main__":
    asyncio.run(main())