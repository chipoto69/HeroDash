#!/usr/bin/env python3
"""
Basic swarm example - 10 lines to get started
"""

import asyncio
from swarm_core import Swarm, SimpleAgent

async def main():
    # Create swarm with 3 agents
    swarm = Swarm()
    swarm.add_agent(SimpleAgent("worker1"))
    swarm.add_agent(SimpleAgent("worker2"))
    swarm.add_agent(SimpleAgent("worker3"))
    
    # Start swarm
    await swarm.start()
    
    # Send a task
    result = await swarm.task("user", "worker1", {"action": "process", "data": [1, 2, 3]})
    print(f"Result: {result.data if result else 'No result'}")
    
    # Stop swarm
    await swarm.stop()

if __name__ == "__main__":
    asyncio.run(main())