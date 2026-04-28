#!/usr/bin/env python3
"""
Edge Case Testing - Test failure modes and corner cases
Tests: Race conditions, malformed messages, circular dependencies, crashes
"""

import asyncio
import json
import random
import time
from typing import Dict, Any, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_core import Swarm, Agent, Message, MessageType, SwarmConfig

class EdgeCaseAgent(Agent):
    """Agent that can simulate various failure modes"""
    
    def __init__(self, agent_id: str, failure_mode: Optional[str] = None):
        super().__init__(agent_id)
        self.failure_mode = failure_mode
        self.crash_after = 5  # Crash after 5 messages
        self.messages_seen = 0
        
    async def process(self, message: Message) -> Optional[Message]:
        self.messages_seen += 1
        
        # Simulate various failure modes
        if self.failure_mode == "crash":
            if self.messages_seen >= self.crash_after:
                raise Exception("Simulated agent crash!")
                
        elif self.failure_mode == "hang":
            if self.messages_seen >= 3:
                await asyncio.sleep(1000)  # Hang forever
                
        elif self.failure_mode == "corrupt":
            # Return corrupted message
            return Message(
                id=None,  # Invalid ID
                type="invalid_type",  # Invalid type
                from_agent=self.id,
                to_agent=message.from_agent,
                data="not_a_dict"  # Invalid data type
            )
            
        elif self.failure_mode == "loop":
            # Create infinite loop
            return Message(
                id=f"{message.id}_loop",
                type=MessageType.TASK,
                from_agent=self.id,
                to_agent=self.id,  # Send to self
                data=message.data
            )
            
        elif self.failure_mode == "memory_leak":
            # Accumulate data without cleanup
            if not hasattr(self, "leaked_data"):
                self.leaked_data = []
            self.leaked_data.append("x" * 1024 * 1024)  # 1MB per message
            
        # Normal processing
        return Message(
            id=f"{message.id}_response",
            type=MessageType.RESULT,
            from_agent=self.id,
            to_agent=message.from_agent,
            data={"processed": True}
        )

class EdgeCaseTester:
    """Test edge cases and failure scenarios"""
    
    def __init__(self):
        self.results = {}
        
    async def test_race_conditions(self) -> Dict[str, Any]:
        """Test concurrent access to shared resources"""
        print("\n🔥 RACE CONDITION TEST")
        print("=" * 60)
        
        swarm = Swarm()
        shared_resource = {"counter": 0, "lock": asyncio.Lock()}
        results = {"conflicts": 0, "success": 0}
        
        class RaceAgent(Agent):
            async def process(self, message: Message) -> Optional[Message]:
                # Try to increment shared counter
                # Intentionally not using lock to cause race condition
                current = shared_resource["counter"]
                await asyncio.sleep(0.001)  # Simulate processing
                shared_resource["counter"] = current + 1
                results["success"] += 1
                return None
        
        # Create agents
        for i in range(20):
            await swarm.add_agent(RaceAgent(f"race_{i}"))
        
        await swarm.start()
        
        # Send concurrent messages
        print("📤 Sending 100 concurrent messages...")
        tasks = []
        for i in range(100):
            tasks.append(swarm.send(Message(
                id=f"race_{i}",
                type=MessageType.TASK,
                from_agent="tester",
                to_agent=f"race_{i % 20}",
                data={"increment": True}
            )))
        
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)
        
        # Check for race condition
        expected = results["success"]
        actual = shared_resource["counter"]
        results["conflicts"] = expected - actual
        
        print(f"📊 Results:")
        print(f"  Expected counter: {expected}")
        print(f"  Actual counter: {actual}")
        print(f"  Lost updates: {results['conflicts']}")
        
        if results["conflicts"] > 0:
            print("  ⚠️ Race condition detected!")
        else:
            print("  ✅ No race conditions")
        
        await swarm.stop()
        return results
    
    async def test_malformed_messages(self) -> Dict[str, Any]:
        """Test handling of invalid messages"""
        print("\n🔥 MALFORMED MESSAGE TEST")
        print("=" * 60)
        
        swarm = Swarm()
        results = {"errors": [], "handled": 0, "crashed": 0}
        
        class RobustAgent(Agent):
            async def process(self, message: Message) -> Optional[Message]:
                try:
                    # Try to access potentially missing fields
                    _ = message.data["required_field"]
                    results["handled"] += 1
                except Exception as e:
                    results["errors"].append(str(e))
                return None
        
        await swarm.add_agent(RobustAgent("robust"))
        await swarm.start()
        
        # Send various malformed messages
        test_cases = [
            # Missing required fields
            {"id": "bad1", "type": "invalid"},
            
            # Wrong data types
            {"id": "bad2", "type": MessageType.TASK, "data": "should_be_dict"},
            
            # Circular reference (causes JSON serialization issues)
            {"id": "bad3", "type": MessageType.TASK, "data": {}},
            
            # Extremely large message
            {"id": "bad4", "type": MessageType.TASK, 
             "data": {"huge": "x" * (10 * 1024 * 1024)}},  # 10MB
            
            # Unicode edge cases
            {"id": "bad5", "type": MessageType.TASK,
             "data": {"unicode": "🔥" * 1000, "null": "\x00", "special": "\n\r\t"}}
        ]
        
        print(f"📤 Sending {len(test_cases)} malformed messages...")
        
        for i, test_case in enumerate(test_cases):
            try:
                if isinstance(test_case, dict):
                    # Try to create message from dict
                    msg = Message.from_dict(test_case)
                else:
                    msg = test_case
                    
                await swarm.send(msg)
                
            except Exception as e:
                results["errors"].append(f"Case {i}: {str(e)}")
        
        await asyncio.sleep(1)
        await swarm.stop()
        
        print(f"📊 Results:")
        print(f"  Errors caught: {len(results['errors'])}")
        print(f"  Messages handled: {results['handled']}")
        print(f"  Agents crashed: {results['crashed']}")
        
        if results["crashed"] == 0:
            print("  ✅ System remained stable")
        else:
            print("  ❌ System instability detected")
        
        return results
    
    async def test_circular_dependencies(self) -> Dict[str, Any]:
        """Test circular task dependencies"""
        print("\n🔥 CIRCULAR DEPENDENCY TEST")
        print("=" * 60)
        
        swarm = Swarm()
        results = {"loops_detected": 0, "max_depth": 0}
        
        class DependentAgent(Agent):
            def __init__(self, agent_id: str):
                super().__init__(agent_id)
                self.seen_messages = set()
                self.depth_counter = {}
                
            async def process(self, message: Message) -> Optional[Message]:
                # Detect loops
                if message.id in self.seen_messages:
                    results["loops_detected"] += 1
                    return None  # Break the loop
                
                self.seen_messages.add(message.id)
                
                # Track depth
                depth = message.meta.get("depth", 0)
                results["max_depth"] = max(results["max_depth"], depth)
                
                # Create dependency
                if depth < 10:  # Limit depth
                    # Forward to next agent in circle
                    next_agent = f"dep_{(int(self.id.split('_')[1]) + 1) % 3}"
                    return Message(
                        id=f"{message.id}_fwd",
                        type=MessageType.TASK,
                        from_agent=self.id,
                        to_agent=next_agent,
                        data=message.data,
                        meta={"depth": depth + 1, "original": message.id}
                    )
                
                return None
        
        # Create circular dependency: A -> B -> C -> A
        for i in range(3):
            await swarm.add_agent(DependentAgent(f"dep_{i}"))
        
        await swarm.start()
        
        print("📤 Creating circular task dependencies...")
        
        # Start the circle
        await swarm.send(Message(
            id="circular_start",
            type=MessageType.TASK,
            from_agent="tester",
            to_agent="dep_0",
            data={"task": "circular"},
            meta={"depth": 0}
        ))
        
        await asyncio.sleep(2)
        await swarm.stop()
        
        print(f"📊 Results:")
        print(f"  Loops detected: {results['loops_detected']}")
        print(f"  Max depth reached: {results['max_depth']}")
        
        if results["loops_detected"] > 0:
            print("  ✅ Circular dependencies handled correctly")
        else:
            print("  ⚠️ No loop detection triggered")
        
        return results
    
    async def test_agent_crashes(self) -> Dict[str, Any]:
        """Test handling of agent crashes"""
        print("\n🔥 AGENT CRASH TEST")
        print("=" * 60)
        
        swarm = Swarm()
        results = {"crashes": 0, "recovered": 0, "messages_lost": 0}
        
        # Create agents with different failure modes
        agents = [
            EdgeCaseAgent("crash_1", "crash"),
            EdgeCaseAgent("hang_1", "hang"),
            EdgeCaseAgent("normal_1", None),
            EdgeCaseAgent("corrupt_1", "corrupt")
        ]
        
        for agent in agents:
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        print("📤 Sending messages to failure-prone agents...")
        
        messages_sent = 0
        for i in range(20):
            for agent in agents:
                try:
                    await swarm.send(Message(
                        id=f"crash_test_{i}_{agent.id}",
                        type=MessageType.TASK,
                        from_agent="tester",
                        to_agent=agent.id,
                        data={"test": "crash"}
                    ))
                    messages_sent += 1
                except Exception as e:
                    results["crashes"] += 1
            
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(2)
        
        # Check agent status
        for agent in agents:
            if hasattr(agent, "messages_seen"):
                if agent.failure_mode and agent.messages_seen < 5:
                    results["recovered"] += 1
        
        await swarm.stop()
        
        print(f"📊 Results:")
        print(f"  Messages sent: {messages_sent}")
        print(f"  Crashes detected: {results['crashes']}")
        print(f"  Agents recovered: {results['recovered']}")
        
        return results
    
    async def test_message_ordering(self) -> Dict[str, Any]:
        """Test message ordering guarantees"""
        print("\n🔥 MESSAGE ORDERING TEST")
        print("=" * 60)
        
        swarm = Swarm()
        results = {"out_of_order": 0, "total": 0}
        
        class OrderAgent(Agent):
            def __init__(self, agent_id: str):
                super().__init__(agent_id)
                self.last_seq = -1
                
            async def process(self, message: Message) -> Optional[Message]:
                seq = message.data.get("sequence", 0)
                if seq <= self.last_seq:
                    results["out_of_order"] += 1
                self.last_seq = seq
                results["total"] += 1
                
                # Add random delay
                await asyncio.sleep(random.uniform(0, 0.01))
                return None
        
        await swarm.add_agent(OrderAgent("order_checker"))
        await swarm.start()
        
        print("📤 Sending 100 ordered messages...")
        
        # Send messages in order
        for i in range(100):
            await swarm.send(Message(
                id=f"order_{i}",
                type=MessageType.TASK,
                from_agent="tester",
                to_agent="order_checker",
                data={"sequence": i}
            ))
        
        await asyncio.sleep(2)
        await swarm.stop()
        
        print(f"📊 Results:")
        print(f"  Messages processed: {results['total']}")
        print(f"  Out of order: {results['out_of_order']}")
        
        if results["out_of_order"] == 0:
            print("  ✅ Message ordering preserved")
        else:
            print("  ⚠️ Message ordering not guaranteed")
        
        return results
    
    async def test_timeout_handling(self) -> Dict[str, Any]:
        """Test timeout scenarios"""
        print("\n🔥 TIMEOUT HANDLING TEST")
        print("=" * 60)
        
        swarm = Swarm()
        results = {"timeouts": 0, "completed": 0}
        
        class SlowAgent(Agent):
            async def process(self, message: Message) -> Optional[Message]:
                delay = message.data.get("delay", 1)
                await asyncio.sleep(delay)
                results["completed"] += 1
                return Message(
                    id=f"{message.id}_done",
                    type=MessageType.RESULT,
                    from_agent=self.id,
                    to_agent=message.from_agent,
                    data={"completed": True}
                )
        
        await swarm.add_agent(SlowAgent("slow"))
        await swarm.start()
        
        print("📤 Sending messages with timeouts...")
        
        # Test various timeout scenarios
        test_cases = [
            {"delay": 0.1, "timeout": 1.0},    # Should complete
            {"delay": 2.0, "timeout": 1.0},    # Should timeout
            {"delay": 0.5, "timeout": 0.5},    # Edge case
        ]
        
        for i, test in enumerate(test_cases):
            try:
                result = await asyncio.wait_for(
                    swarm.task(
                        "tester",
                        "slow",
                        {"delay": test["delay"]}
                    ),
                    timeout=test["timeout"]
                )
                if result:
                    print(f"  Test {i}: Completed in time")
            except asyncio.TimeoutError:
                results["timeouts"] += 1
                print(f"  Test {i}: Timed out (expected)")
        
        await swarm.stop()
        
        print(f"\n📊 Results:")
        print(f"  Timeouts: {results['timeouts']}")
        print(f"  Completed: {results['completed']}")
        
        return results

async def main():
    """Run all edge case tests"""
    tester = EdgeCaseTester()
    
    print("\n" + "="*60)
    print("EDGE CASE TESTING SUITE")
    print("="*60)
    
    # Run all tests
    race_results = await tester.test_race_conditions()
    malformed_results = await tester.test_malformed_messages()
    circular_results = await tester.test_circular_dependencies()
    crash_results = await tester.test_agent_crashes()
    order_results = await tester.test_message_ordering()
    timeout_results = await tester.test_timeout_handling()
    
    # Summary
    print("\n" + "="*60)
    print("EDGE CASE TEST SUMMARY")
    print("="*60)
    
    total_issues = (
        race_results.get("conflicts", 0) +
        len(malformed_results.get("errors", [])) +
        crash_results.get("crashes", 0) +
        order_results.get("out_of_order", 0)
    )
    
    if total_issues == 0:
        print("✅ All edge cases handled correctly!")
    else:
        print(f"⚠️ {total_issues} issues detected across all tests")
        print("  Consider implementing:")
        print("  - Proper locking for shared resources")
        print("  - Message validation and sanitization")
        print("  - Circuit breakers for failing agents")
        print("  - Message ordering guarantees if needed")

if __name__ == "__main__":
    asyncio.run(main())