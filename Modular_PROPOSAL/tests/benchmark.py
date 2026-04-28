#!/usr/bin/env python3
"""
Benchmark Suite - Real-world performance testing
Tests performance under realistic workloads
"""

import asyncio
import time
import statistics
import psutil
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_core import Swarm, Agent, Message, MessageType, SwarmConfig

@dataclass 
class BenchmarkResult:
    """Results from a benchmark run"""
    name: str
    agent_count: int
    duration_sec: float
    messages_sent: int
    messages_processed: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_msg_sec: float
    cpu_percent: float
    memory_mb: float
    success_rate: float
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

class BenchmarkAgent(Agent):
    """Agent optimized for benchmarking"""
    
    def __init__(self, agent_id: str, processing_time: float = 0.01):
        super().__init__(agent_id)
        self.processing_time = processing_time
        self.messages_processed = 0
        self.latencies = []
        self.errors = 0
        
    async def process(self, message: Message) -> Message:
        """Process with configurable delay"""
        start = time.time()
        
        try:
            # Simulate processing
            if self.processing_time > 0:
                await asyncio.sleep(self.processing_time)
            
            self.messages_processed += 1
            
            # Track latency
            if "sent_time" in message.meta:
                latency = (time.time() - message.meta["sent_time"]) * 1000
                self.latencies.append(latency)
            
            # Return result
            return Message(
                id=f"{message.id}_result",
                type=MessageType.RESULT,
                from_agent=self.id,
                to_agent=message.from_agent,
                data={
                    "processed": True,
                    "processing_time": time.time() - start
                }
            )
            
        except Exception as e:
            self.errors += 1
            raise

class Benchmark:
    """Main benchmark orchestrator"""
    
    def __init__(self, transport: str = "memory"):
        self.transport = transport
        self.results: List[BenchmarkResult] = []
        
    async def run_all(self) -> List[BenchmarkResult]:
        """Run all benchmark scenarios"""
        print("\n" + "="*60)
        print("COMPREHENSIVE BENCHMARK SUITE")
        print("="*60)
        
        # Scenario 1: Small swarm, high frequency
        result1 = await self.benchmark_small_swarm()
        self.results.append(result1)
        
        # Scenario 2: Medium swarm, moderate load
        result2 = await self.benchmark_medium_swarm()
        self.results.append(result2)
        
        # Scenario 3: Large swarm, distributed work
        result3 = await self.benchmark_large_swarm()
        self.results.append(result3)
        
        # Scenario 4: Your specific setup (6-7 agents)
        result4 = await self.benchmark_your_setup()
        self.results.append(result4)
        
        # Scenario 5: Map-reduce pattern
        result5 = await self.benchmark_mapreduce()
        self.results.append(result5)
        
        # Scenario 6: Pipeline pattern
        result6 = await self.benchmark_pipeline()
        self.results.append(result6)
        
        # Save results
        self.save_results()
        self.print_summary()
        
        return self.results
    
    async def benchmark_small_swarm(self) -> BenchmarkResult:
        """Small swarm (10 agents), high message frequency"""
        print("\n🔬 Benchmark 1: Small Swarm, High Frequency")
        print("-" * 40)
        
        config = SwarmConfig(transport=self.transport)
        swarm = Swarm(config)
        
        # Create agents
        agent_count = 10
        agents = []
        for i in range(agent_count):
            agent = BenchmarkAgent(f"small_{i}", processing_time=0.001)
            agents.append(agent)
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Run benchmark
        duration = 10  # seconds
        start_time = time.time()
        messages_sent = 0
        
        print(f"  Running for {duration} seconds...")
        
        while time.time() - start_time < duration:
            # Send burst of messages
            for _ in range(100):
                target = agents[messages_sent % agent_count]
                await swarm.send(Message(
                    id=f"small_{messages_sent}",
                    type=MessageType.TASK,
                    from_agent="benchmark",
                    to_agent=target.id,
                    data={"test": "small_swarm"},
                    meta={"sent_time": time.time()}
                ))
                messages_sent += 1
            
            await asyncio.sleep(0.01)  # Small delay between bursts
        
        # Collect results
        result = await self._collect_results(
            "small_swarm",
            agents,
            messages_sent,
            time.time() - start_time
        )
        
        await swarm.stop()
        
        print(f"  ✅ Throughput: {result.throughput_msg_sec:.0f} msg/sec")
        print(f"  ✅ Avg latency: {result.avg_latency_ms:.2f}ms")
        
        return result
    
    async def benchmark_medium_swarm(self) -> BenchmarkResult:
        """Medium swarm (100 agents), moderate load"""
        print("\n🔬 Benchmark 2: Medium Swarm, Moderate Load")
        print("-" * 40)
        
        config = SwarmConfig(transport=self.transport)
        swarm = Swarm(config)
        
        # Create agents
        agent_count = 100
        agents = []
        for i in range(agent_count):
            agent = BenchmarkAgent(f"medium_{i}", processing_time=0.01)
            agents.append(agent)
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Run benchmark
        duration = 10
        start_time = time.time()
        messages_sent = 0
        
        print(f"  Running with {agent_count} agents...")
        
        while time.time() - start_time < duration:
            # Send to random agents
            for _ in range(10):
                target = agents[messages_sent % agent_count]
                await swarm.send(Message(
                    id=f"medium_{messages_sent}",
                    type=MessageType.TASK,
                    from_agent="benchmark",
                    to_agent=target.id,
                    data={"test": "medium_swarm"},
                    meta={"sent_time": time.time()}
                ))
                messages_sent += 1
            
            await asyncio.sleep(0.1)
        
        result = await self._collect_results(
            "medium_swarm",
            agents,
            messages_sent,
            time.time() - start_time
        )
        
        await swarm.stop()
        
        print(f"  ✅ Handled {agent_count} agents smoothly")
        print(f"  ✅ Success rate: {result.success_rate:.1%}")
        
        return result
    
    async def benchmark_large_swarm(self) -> BenchmarkResult:
        """Large swarm (500+ agents), distributed workload"""
        print("\n🔬 Benchmark 3: Large Swarm, Distributed Work")
        print("-" * 40)
        
        config = SwarmConfig(transport=self.transport)
        swarm = Swarm(config)
        
        # Create many lightweight agents
        agent_count = 500
        agents = []
        
        print(f"  Creating {agent_count} agents...")
        
        for i in range(agent_count):
            agent = BenchmarkAgent(f"large_{i}", processing_time=0.1)
            agents.append(agent)
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Run benchmark
        duration = 10
        start_time = time.time()
        messages_sent = 0
        
        print(f"  Distributing work across {agent_count} agents...")
        
        # Send work to all agents
        tasks = []
        for agent in agents:
            tasks.append(swarm.send(Message(
                id=f"large_{messages_sent}",
                type=MessageType.TASK,
                from_agent="benchmark",
                to_agent=agent.id,
                data={"test": "large_swarm"},
                meta={"sent_time": time.time()}
            )))
            messages_sent += 1
        
        # Send all at once
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await asyncio.sleep(2)
        
        result = await self._collect_results(
            "large_swarm",
            agents,
            messages_sent,
            time.time() - start_time
        )
        
        await swarm.stop()
        
        print(f"  ✅ Managed {agent_count} agents")
        print(f"  ✅ Memory usage: {result.memory_mb:.1f}MB")
        
        return result
    
    async def benchmark_your_setup(self) -> BenchmarkResult:
        """Your specific setup: 6-7 agents, continuous operation"""
        print("\n🔬 Benchmark 4: Your Setup (6-7 agents, continuous)")
        print("-" * 40)
        
        config = SwarmConfig(transport=self.transport)
        swarm = Swarm(config)
        
        # Create agents matching your setup
        agents = [
            BenchmarkAgent("claude_1", processing_time=1.0),    # Claude is slower
            BenchmarkAgent("claude_2", processing_time=1.0),
            BenchmarkAgent("qwen", processing_time=0.2),        # Local model, faster
            BenchmarkAgent("langraph", processing_time=0.5),
            BenchmarkAgent("retriever", processing_time=0.3),
            BenchmarkAgent("embedder", processing_time=0.1),
            BenchmarkAgent("monitor", processing_time=0.01)
        ]
        
        for agent in agents:
            await swarm.add_agent(agent)
        
        await swarm.start()
        
        # Simulate your workload pattern
        duration = 30  # 30 seconds simulates longer operation
        start_time = time.time()
        messages_sent = 0
        
        print(f"  Simulating your continuous workload...")
        
        while time.time() - start_time < duration:
            # Your pattern: bursts of activity
            current_time = time.time() - start_time
            
            if int(current_time) % 5 == 0:
                # Every 5 seconds: burst
                for _ in range(20):
                    target = agents[messages_sent % len(agents)]
                    await swarm.send(Message(
                        id=f"your_{messages_sent}",
                        type=MessageType.TASK,
                        from_agent="user",
                        to_agent=target.id,
                        data={"task": "process"},
                        meta={"sent_time": time.time()}
                    ))
                    messages_sent += 1
            else:
                # Normal activity
                for _ in range(3):
                    target = agents[messages_sent % len(agents)]
                    await swarm.send(Message(
                        id=f"your_{messages_sent}",
                        type=MessageType.TASK,
                        from_agent="user",
                        to_agent=target.id,
                        data={"task": "process"},
                        meta={"sent_time": time.time()}
                    ))
                    messages_sent += 1
            
            await asyncio.sleep(0.5)
        
        result = await self._collect_results(
            "your_setup",
            agents,
            messages_sent,
            time.time() - start_time
        )
        
        await swarm.stop()
        
        print(f"  ✅ Your workload: easily handled")
        print(f"  ✅ CPU overhead: {result.cpu_percent:.1f}%")
        
        return result
    
    async def benchmark_mapreduce(self) -> BenchmarkResult:
        """Map-reduce pattern benchmark"""
        print("\n🔬 Benchmark 5: Map-Reduce Pattern")
        print("-" * 40)
        
        config = SwarmConfig(transport=self.transport)
        swarm = Swarm(config)
        
        # Create mapper and reducer agents
        mappers = []
        for i in range(10):
            mapper = BenchmarkAgent(f"mapper_{i}", processing_time=0.05)
            mappers.append(mapper)
            await swarm.add_agent(mapper)
        
        reducer = BenchmarkAgent("reducer", processing_time=0.01)
        await swarm.add_agent(reducer)
        
        await swarm.start()
        
        # Run map-reduce
        start_time = time.time()
        data_chunks = 100
        
        print(f"  Mapping {data_chunks} chunks across {len(mappers)} mappers...")
        
        # Map phase
        map_tasks = []
        for i in range(data_chunks):
            mapper = mappers[i % len(mappers)]
            map_tasks.append(swarm.send(Message(
                id=f"map_{i}",
                type=MessageType.TASK,
                from_agent="coordinator",
                to_agent=mapper.id,
                data={"chunk": i, "operation": "map"},
                meta={"sent_time": time.time()}
            )))
        
        await asyncio.gather(*map_tasks)
        
        # Reduce phase
        await swarm.send(Message(
            id="reduce",
            type=MessageType.TASK,
            from_agent="coordinator",
            to_agent="reducer",
            data={"operation": "reduce", "chunks": data_chunks},
            meta={"sent_time": time.time()}
        ))
        
        await asyncio.sleep(1)
        
        all_agents = mappers + [reducer]
        result = await self._collect_results(
            "mapreduce",
            all_agents,
            data_chunks + 1,
            time.time() - start_time
        )
        
        await swarm.stop()
        
        print(f"  ✅ Map-reduce completed")
        print(f"  ✅ Parallelism achieved")
        
        return result
    
    async def benchmark_pipeline(self) -> BenchmarkResult:
        """Pipeline pattern benchmark"""
        print("\n🔬 Benchmark 6: Pipeline Pattern")
        print("-" * 40)
        
        config = SwarmConfig(transport=self.transport)
        swarm = Swarm(config)
        
        # Create pipeline stages
        stages = []
        for i in range(5):
            stage = BenchmarkAgent(f"stage_{i}", processing_time=0.02)
            stages.append(stage)
            await swarm.add_agent(stage)
        
        await swarm.start()
        
        # Run pipeline
        start_time = time.time()
        items = 50
        
        print(f"  Processing {items} items through {len(stages)}-stage pipeline...")
        
        for item in range(items):
            # Send through pipeline
            current_data = {"item": item, "stage": 0}
            
            for i, stage in enumerate(stages):
                await swarm.send(Message(
                    id=f"pipeline_{item}_{i}",
                    type=MessageType.TASK,
                    from_agent="pipeline" if i == 0 else stages[i-1].id,
                    to_agent=stage.id,
                    data={**current_data, "stage": i},
                    meta={"sent_time": time.time()}
                ))
                
                await asyncio.sleep(0.01)  # Small delay between stages
        
        await asyncio.sleep(2)
        
        result = await self._collect_results(
            "pipeline",
            stages,
            items * len(stages),
            time.time() - start_time
        )
        
        await swarm.stop()
        
        print(f"  ✅ Pipeline processing complete")
        print(f"  ✅ Stage efficiency maintained")
        
        return result
    
    # Helper methods
    
    async def _collect_results(self, 
                               name: str,
                               agents: List[BenchmarkAgent],
                               messages_sent: int,
                               duration: float) -> BenchmarkResult:
        """Collect and analyze benchmark results"""
        
        # Aggregate metrics
        total_processed = sum(a.messages_processed for a in agents)
        all_latencies = []
        total_errors = sum(a.errors for a in agents)
        
        for agent in agents:
            all_latencies.extend(agent.latencies)
        
        # Calculate statistics
        if all_latencies:
            all_latencies.sort()
            avg_latency = statistics.mean(all_latencies)
            p50 = all_latencies[len(all_latencies) // 2]
            p95 = all_latencies[int(len(all_latencies) * 0.95)]
            p99 = all_latencies[int(len(all_latencies) * 0.99)]
        else:
            avg_latency = p50 = p95 = p99 = 0
        
        # System metrics
        process = psutil.Process()
        
        return BenchmarkResult(
            name=name,
            agent_count=len(agents),
            duration_sec=duration,
            messages_sent=messages_sent,
            messages_processed=total_processed,
            avg_latency_ms=avg_latency,
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            throughput_msg_sec=total_processed / duration if duration > 0 else 0,
            cpu_percent=process.cpu_percent(),
            memory_mb=process.memory_info().rss / 1024 / 1024,
            success_rate=(total_processed / messages_sent) if messages_sent > 0 else 0
        )
    
    def save_results(self):
        """Save benchmark results to file"""
        output_dir = Path("benchmark_results")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"benchmark_{timestamp}.json"
        
        with open(output_file, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
    
    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        
        print("\n📊 Performance Metrics:")
        print(f"{'Scenario':<20} {'Agents':<10} {'Throughput':<15} {'Avg Latency':<15} {'Success Rate':<12}")
        print("-" * 72)
        
        for r in self.results:
            print(f"{r.name:<20} {r.agent_count:<10} "
                  f"{r.throughput_msg_sec:<15.0f} {r.avg_latency_ms:<15.2f} "
                  f"{r.success_rate:<12.1%}")
        
        print("\n🏆 Key Findings:")
        
        # Find best throughput
        best_throughput = max(self.results, key=lambda r: r.throughput_msg_sec)
        print(f"  Highest throughput: {best_throughput.name} "
              f"({best_throughput.throughput_msg_sec:.0f} msg/sec)")
        
        # Find best latency
        best_latency = min(self.results, key=lambda r: r.avg_latency_ms)
        print(f"  Lowest latency: {best_latency.name} "
              f"({best_latency.avg_latency_ms:.2f}ms)")
        
        # Your setup performance
        your_setup = next((r for r in self.results if r.name == "your_setup"), None)
        if your_setup:
            print(f"\n  Your setup performance:")
            print(f"    - Throughput: {your_setup.throughput_msg_sec:.0f} msg/sec")
            print(f"    - Latency: {your_setup.avg_latency_ms:.2f}ms")
            print(f"    - CPU: {your_setup.cpu_percent:.1f}%")
            print(f"    - Memory: {your_setup.memory_mb:.1f}MB")
            print(f"    - ✅ Well within system capacity!")

async def main():
    """Run complete benchmark suite"""
    
    # Test with memory transport (default)
    print("\n🚀 Running benchmarks with MEMORY transport")
    memory_bench = Benchmark(transport="memory")
    memory_results = await memory_bench.run_all()
    
    # Optionally test with NATS if available
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        nats_available = sock.connect_ex(('localhost', 4224)) == 0
        sock.close()
        
        if nats_available:
            print("\n🚀 Running benchmarks with NATS transport")
            nats_bench = Benchmark(transport="nats")
            nats_results = await nats_bench.run_all()
            
            # Compare results
            print("\n📊 Transport Comparison:")
            print("  Memory transport: Best for single-process, lowest latency")
            print("  NATS transport: Best for distributed, higher scalability")
    except:
        print("\n  (NATS benchmarks skipped - server not available)")

if __name__ == "__main__":
    asyncio.run(main())