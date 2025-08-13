#!/usr/bin/env python3
"""
Stress Testing Suite - Find the breaking points of the swarm
Tests: Agent scaling, message throughput, connection stability
"""

import asyncio
import time
import psutil
import gc
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_core import Swarm, Agent, Message, MessageType, SwarmConfig

@dataclass
class TestMetrics:
    """Metrics collected during stress tests"""
    agent_count: int
    messages_sent: int
    messages_received: int
    messages_dropped: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    memory_mb: float
    cpu_percent: float
    test_duration_sec: float
    errors: List[str]

class StressTestAgent(Agent):
    """Agent designed for stress testing"""
    
    def __init__(self, agent_id: str, response_delay: float = 0):
        super().__init__(agent_id)
        self.messages_processed = 0
        self.response_delay = response_delay
        self.latencies = []
        
    async def process(self, message: Message) -> Message:
        start = time.time()
        
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)
        
        self.messages_processed += 1
        
        # Track latency
        if "sent_time" in message.meta:
            latency = (time.time() - message.meta["sent_time"]) * 1000
            self.latencies.append(latency)
        
        return Message(
            id=f"{message.id}_response",
            type=MessageType.RESULT,
            from_agent=self.id,
            to_agent=message.from_agent,
            data={"processed": True, "agent": self.id}
        )

class StressTester:
    """Main stress testing orchestrator"""
    
    def __init__(self, transport: str = "memory"):
        self.config = SwarmConfig(transport=transport)
        self.metrics: List[TestMetrics] = []
        
    async def test_agent_scaling(self, max_agents: int = 1000, increment: int = 10) -> List[TestMetrics]:
        """Test how many agents the swarm can handle"""
        print(f"\n🚀 AGENT SCALING TEST (up to {max_agents} agents)")
        print("=" * 60)
        
        results = []
        current_agents = increment
        
        while current_agents <= max_agents:
            try:
                print(f"\n📊 Testing with {current_agents} agents...")
                metrics = await self._run_agent_test(current_agents)
                results.append(metrics)
                
                # Check if we're hitting limits
                if metrics.messages_dropped > 0 or metrics.errors:
                    print(f"⚠️ Degradation detected at {current_agents} agents")
                    if metrics.messages_dropped > metrics.messages_sent * 0.1:  # >10% drop rate
                        print(f"❌ Breaking point reached: {current_agents} agents")
                        break
                
                print(f"✅ {current_agents} agents: {metrics.avg_latency_ms:.2f}ms avg latency, "
                      f"{metrics.memory_mb:.1f}MB RAM")
                
                # Exponential increment after 100 agents
                if current_agents >= 100:
                    current_agents = int(current_agents * 1.5)
                else:
                    current_agents += increment
                    
            except Exception as e:
                print(f"❌ Failed at {current_agents} agents: {e}")
                break
                
        return results
    
    async def test_message_throughput(self, 
                                     agent_count: int = 10,
                                     duration_sec: int = 10) -> TestMetrics:
        """Test maximum message throughput"""
        print(f"\n🚀 MESSAGE THROUGHPUT TEST ({agent_count} agents, {duration_sec}s)")
        print("=" * 60)
        
        swarm = Swarm(self.config)
        agents = []
        
        # Create agents
        for i in range(agent_count):
            agent = StressTestAgent(f"throughput_{i}")
            agents.append(agent)
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Metrics
        start_time = time.time()
        messages_sent = 0
        latencies = []
        errors = []
        
        # Send messages continuously
        async def message_sender():
            nonlocal messages_sent
            while time.time() - start_time < duration_sec:
                try:
                    for i in range(agent_count):
                        message = Message(
                            id=f"msg_{messages_sent}",
                            type=MessageType.TASK,
                            from_agent="tester",
                            to_agent=f"throughput_{i}",
                            data={"test": "throughput"},
                            meta={"sent_time": time.time()}
                        )
                        await swarm.send(message)
                        messages_sent += 1
                    
                    # No delay - maximum throughput
                    await asyncio.sleep(0)  # Yield control
                    
                except Exception as e:
                    errors.append(str(e))
        
        # Run sender
        sender_task = asyncio.create_task(message_sender())
        await asyncio.sleep(duration_sec)
        sender_task.cancel()
        
        # Collect metrics
        await asyncio.sleep(1)  # Let remaining messages process
        
        total_processed = sum(a.messages_processed for a in agents)
        all_latencies = []
        for agent in agents:
            all_latencies.extend(agent.latencies)
        
        await swarm.stop()
        
        # Calculate metrics
        metrics = TestMetrics(
            agent_count=agent_count,
            messages_sent=messages_sent,
            messages_received=total_processed,
            messages_dropped=messages_sent - total_processed,
            avg_latency_ms=sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            p95_latency_ms=self._percentile(all_latencies, 95),
            p99_latency_ms=self._percentile(all_latencies, 99),
            max_latency_ms=max(all_latencies) if all_latencies else 0,
            memory_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_percent=psutil.Process().cpu_percent(),
            test_duration_sec=duration_sec,
            errors=errors
        )
        
        print(f"\n📊 Results:")
        print(f"  Messages/sec: {messages_sent / duration_sec:.0f}")
        print(f"  Processed: {total_processed}/{messages_sent} ({total_processed/messages_sent*100:.1f}%)")
        print(f"  Avg latency: {metrics.avg_latency_ms:.2f}ms")
        print(f"  P95 latency: {metrics.p95_latency_ms:.2f}ms")
        print(f"  P99 latency: {metrics.p99_latency_ms:.2f}ms")
        
        return metrics
    
    async def test_burst_load(self, 
                             agent_count: int = 10,
                             burst_size: int = 1000) -> TestMetrics:
        """Test handling of sudden message bursts"""
        print(f"\n🚀 BURST LOAD TEST ({burst_size} messages to {agent_count} agents)")
        print("=" * 60)
        
        swarm = Swarm(self.config)
        agents = []
        
        for i in range(agent_count):
            agent = StressTestAgent(f"burst_{i}")
            agents.append(agent)
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Send burst
        start_time = time.time()
        messages = []
        
        print(f"💥 Sending {burst_size} messages...")
        for i in range(burst_size):
            message = Message(
                id=f"burst_{i}",
                type=MessageType.TASK,
                from_agent="tester",
                to_agent=f"burst_{i % agent_count}",
                data={"burst": i},
                meta={"sent_time": time.time()}
            )
            messages.append(swarm.send(message))
        
        # Send all at once
        await asyncio.gather(*messages)
        send_time = time.time() - start_time
        
        print(f"📤 Sent in {send_time:.3f}s ({burst_size/send_time:.0f} msg/s)")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Collect results
        total_processed = sum(a.messages_processed for a in agents)
        all_latencies = []
        for agent in agents:
            all_latencies.extend(agent.latencies)
        
        await swarm.stop()
        
        metrics = TestMetrics(
            agent_count=agent_count,
            messages_sent=burst_size,
            messages_received=total_processed,
            messages_dropped=burst_size - total_processed,
            avg_latency_ms=sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            p95_latency_ms=self._percentile(all_latencies, 95),
            p99_latency_ms=self._percentile(all_latencies, 99),
            max_latency_ms=max(all_latencies) if all_latencies else 0,
            memory_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_percent=psutil.Process().cpu_percent(),
            test_duration_sec=time.time() - start_time,
            errors=[]
        )
        
        print(f"\n📊 Burst Results:")
        print(f"  Processed: {total_processed}/{burst_size} ({total_processed/burst_size*100:.1f}%)")
        print(f"  Avg latency: {metrics.avg_latency_ms:.2f}ms")
        print(f"  Max latency: {metrics.max_latency_ms:.2f}ms")
        
        return metrics
    
    async def test_memory_growth(self, 
                                agent_count: int = 50,
                                duration_min: int = 5) -> List[Tuple[float, float]]:
        """Test for memory leaks over time"""
        print(f"\n🚀 MEMORY GROWTH TEST ({agent_count} agents for {duration_min} minutes)")
        print("=" * 60)
        
        swarm = Swarm(self.config)
        
        for i in range(agent_count):
            await swarm.add_agent(StressTestAgent(f"memory_{i}"))
        
        await swarm.start()
        
        memory_samples = []
        start_time = time.time()
        
        async def send_messages():
            msg_id = 0
            while time.time() - start_time < duration_min * 60:
                for i in range(agent_count):
                    await swarm.send(Message(
                        id=f"mem_{msg_id}",
                        type=MessageType.TASK,
                        from_agent="tester",
                        to_agent=f"memory_{i}",
                        data={"test": "memory"}
                    ))
                    msg_id += 1
                await asyncio.sleep(0.1)  # Steady rate
        
        # Start sending
        sender = asyncio.create_task(send_messages())
        
        # Sample memory
        while time.time() - start_time < duration_min * 60:
            gc.collect()  # Force garbage collection
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            elapsed = time.time() - start_time
            memory_samples.append((elapsed, memory_mb))
            print(f"  [{elapsed/60:.1f}min] Memory: {memory_mb:.1f}MB")
            await asyncio.sleep(30)  # Sample every 30 seconds
        
        sender.cancel()
        await swarm.stop()
        
        # Analyze growth
        if len(memory_samples) > 2:
            start_mem = memory_samples[0][1]
            end_mem = memory_samples[-1][1]
            growth = end_mem - start_mem
            growth_rate = growth / duration_min  # MB per minute
            
            print(f"\n📊 Memory Analysis:")
            print(f"  Start: {start_mem:.1f}MB")
            print(f"  End: {end_mem:.1f}MB")
            print(f"  Growth: {growth:.1f}MB ({growth_rate:.2f}MB/min)")
            
            if growth_rate > 10:
                print("  ⚠️ WARNING: Possible memory leak detected!")
            else:
                print("  ✅ Memory usage stable")
        
        return memory_samples
    
    # Helper methods
    
    async def _run_agent_test(self, agent_count: int) -> TestMetrics:
        """Run a test with specified number of agents"""
        swarm = Swarm(self.config)
        agents = []
        
        # Create agents
        for i in range(agent_count):
            agent = StressTestAgent(f"scale_{i}")
            agents.append(agent)
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Send test messages
        start_time = time.time()
        test_duration = 5  # seconds
        messages_sent = 0
        
        while time.time() - start_time < test_duration:
            for i in range(min(10, agent_count)):  # Send to first 10 agents
                await swarm.send(Message(
                    id=f"test_{messages_sent}",
                    type=MessageType.TASK,
                    from_agent="tester",
                    to_agent=f"scale_{i}",
                    data={"test": "scale"},
                    meta={"sent_time": time.time()}
                ))
                messages_sent += 1
            await asyncio.sleep(0.01)
        
        # Collect results
        await asyncio.sleep(1)
        
        total_processed = sum(a.messages_processed for a in agents)
        all_latencies = []
        for agent in agents:
            all_latencies.extend(agent.latencies)
        
        await swarm.stop()
        
        return TestMetrics(
            agent_count=agent_count,
            messages_sent=messages_sent,
            messages_received=total_processed,
            messages_dropped=messages_sent - total_processed,
            avg_latency_ms=sum(all_latencies) / len(all_latencies) if all_latencies else 0,
            p95_latency_ms=self._percentile(all_latencies, 95),
            p99_latency_ms=self._percentile(all_latencies, 99),
            max_latency_ms=max(all_latencies) if all_latencies else 0,
            memory_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_percent=psutil.Process().cpu_percent(),
            test_duration_sec=test_duration,
            errors=[]
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

async def main():
    """Run all stress tests"""
    tester = StressTester(transport="memory")
    
    # Test 1: Agent scaling
    print("\n" + "="*60)
    print("STRESS TESTING SUITE - FINDING BREAKING POINTS")
    print("="*60)
    
    scaling_results = await tester.test_agent_scaling(max_agents=500, increment=10)
    
    # Test 2: Message throughput
    throughput = await tester.test_message_throughput(agent_count=10, duration_sec=10)
    
    # Test 3: Burst handling
    burst = await tester.test_burst_load(agent_count=10, burst_size=1000)
    
    # Test 4: Memory growth
    memory = await tester.test_memory_growth(agent_count=20, duration_min=2)
    
    # Summary
    print("\n" + "="*60)
    print("STRESS TEST SUMMARY")
    print("="*60)
    
    if scaling_results:
        max_stable = max([r.agent_count for r in scaling_results if r.messages_dropped == 0])
        print(f"✅ Max stable agents: {max_stable}")
    
    print(f"✅ Throughput: {throughput.messages_sent / throughput.test_duration_sec:.0f} msg/sec")
    print(f"✅ Burst handling: {burst.messages_received}/{burst.messages_sent} processed")
    
    if memory:
        growth = memory[-1][1] - memory[0][1]
        print(f"✅ Memory growth: {growth:.1f}MB over {len(memory)*30/60:.1f} minutes")

if __name__ == "__main__":
    asyncio.run(main())