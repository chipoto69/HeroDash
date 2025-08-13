#!/usr/bin/env python3
"""
Comprehensive Test Suite for NATS Inter-Agentic Communication Layer
Tests task distribution, synchronization, load balancing, and agent coordination
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import logging
import sys
from typing import List, Dict, Any
import subprocess
import signal

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from inter_agent_communication import (
    InterAgentCommunicationLayer, TaskPriority, TaskStatus, AgentStatus,
    Task, Agent
)
from agent_coordination_utils import BaseAgent, TaskResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CommunicationLayerTest")

class TestAgent(BaseAgent):
    """Test agent implementation"""
    
    def __init__(self, processing_delay: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.processing_delay = processing_delay
        self.processed_tasks = []
        
    async def default_task_handler(self, task_data: Dict[str, Any]) -> TaskResult:
        """Handle test tasks with configurable delay"""
        task_type = task_data.get("task_type", "unknown")
        task_id = task_data.get("task_id", "unknown")
        
        self.logger.info(f"Processing {task_type} task: {task_id}")
        
        # Simulate processing time
        await asyncio.sleep(self.processing_delay)
        
        # Store for verification
        self.processed_tasks.append({
            "task_id": task_id,
            "task_type": task_type,
            "processed_at": datetime.now().isoformat()
        })
        
        # Randomly fail some tasks for testing
        import random
        if random.random() < 0.1:  # 10% failure rate
            return TaskResult(
                success=False,
                data={},
                error="Simulated random failure"
            )
        
        return TaskResult(
            success=True,
            data={
                "task_id": task_id,
                "processed_by": self.agent_id,
                "result": f"Completed {task_type} successfully"
            }
        )
    
    async def on_sync_checkpoint(self, sync_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sync checkpoint with test data"""
        return {
            "agent_id": self.agent_id,
            "checkpoint_data": f"Agent {self.agent_id} ready",
            "processed_tasks": len(self.processed_tasks)
        }

class CommunicationLayerTestSuite:
    """Comprehensive test suite for the communication layer"""
    
    def __init__(self, nats_url: str = "nats://localhost:4223"):
        self.nats_url = nats_url
        self.communication_layer = None
        self.test_agents: List[TestAgent] = []
        self.test_results = {}
        
    async def setup(self) -> bool:
        """Setup test environment"""
        logger.info("🔧 Setting up test environment...")
        
        # Check if NATS is running
        if not await self._check_nats_server():
            logger.error("NATS server is not running - please start it first")
            return False
        
        # Initialize communication layer
        self.communication_layer = InterAgentCommunicationLayer(
            nats_url=self.nats_url,
            environment="test"
        )
        
        if not await self.communication_layer.initialize():
            logger.error("Failed to initialize communication layer")
            return False
        
        logger.info("✅ Test environment setup complete")
        return True
    
    async def _check_nats_server(self) -> bool:
        """Check if NATS server is running"""
        try:
            import nats
            nc = await nats.connect(self.nats_url, connect_timeout=2)
            await nc.close()
            return True
        except Exception:
            return False
    
    async def create_test_agents(self, count: int = 5) -> List[TestAgent]:
        """Create test agents with different configurations"""
        agents = []
        
        configurations = [
            {
                "agent_type": "fast_processor",
                "capabilities": ["data_processing", "analysis"],
                "processing_delay": 0.5,
                "max_concurrent_tasks": 3
            },
            {
                "agent_type": "slow_processor", 
                "capabilities": ["complex_analysis", "reporting"],
                "processing_delay": 2.0,
                "max_concurrent_tasks": 2
            },
            {
                "agent_type": "generalist",
                "capabilities": ["general", "utility"],
                "processing_delay": 1.0,
                "max_concurrent_tasks": 4
            },
            {
                "agent_type": "specialist",
                "capabilities": ["machine_learning", "nlp"],
                "processing_delay": 1.5,
                "max_concurrent_tasks": 2
            },
            {
                "agent_type": "monitor",
                "capabilities": ["monitoring", "health_check"],
                "processing_delay": 0.2,
                "max_concurrent_tasks": 10
            }
        ]
        
        for i in range(count):
            config = configurations[i % len(configurations)]
            
            agent = TestAgent(
                agent_type=config["agent_type"],
                name=f"TestAgent_{i+1}",
                capabilities=config["capabilities"],
                processing_delay=config["processing_delay"],
                max_concurrent_tasks=config["max_concurrent_tasks"],
                nats_url=self.nats_url,
                environment="test"
            )
            
            if await agent.initialize():
                agents.append(agent)
                logger.info(f"✅ Created test agent: {agent.name}")
            else:
                logger.error(f"❌ Failed to create test agent: {agent.name}")
        
        self.test_agents = agents
        return agents
    
    async def test_basic_communication(self) -> Dict[str, Any]:
        """Test basic NATS communication"""
        logger.info("🧪 Testing basic communication...")
        
        test_results = {
            "test_name": "basic_communication",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            # Test message publishing and receiving
            messages_sent = 0
            messages_received = []
            
            # Setup subscriber
            async def message_handler(msg):
                messages_received.append(json.loads(msg.data.decode()))
            
            await self.communication_layer.nc.subscribe("test.basic", cb=message_handler)
            
            # Send test messages
            for i in range(10):
                message = {"test_id": i, "timestamp": datetime.now().isoformat()}
                await self.communication_layer.nc.publish("test.basic", json.dumps(message).encode())
                messages_sent += 1
                await asyncio.sleep(0.1)
            
            # Wait for messages to be received
            await asyncio.sleep(2)
            
            test_results["details"] = {
                "messages_sent": messages_sent,
                "messages_received": len(messages_received),
                "success_rate": len(messages_received) / messages_sent if messages_sent > 0 else 0
            }
            
            test_results["status"] = "passed" if len(messages_received) == messages_sent else "failed"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Basic communication test: {test_results['status']}")
        return test_results
    
    async def test_agent_registration(self) -> Dict[str, Any]:
        """Test agent registration process"""
        logger.info("🧪 Testing agent registration...")
        
        test_results = {
            "test_name": "agent_registration",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            initial_count = len(self.communication_layer.agents)
            
            # Create test agents
            agents = await self.create_test_agents(3)
            
            # Wait for registration to propagate
            await asyncio.sleep(5)
            
            final_count = len(self.communication_layer.agents)
            
            test_results["details"] = {
                "initial_agent_count": initial_count,
                "agents_created": len(agents),
                "final_agent_count": final_count,
                "registration_success": final_count > initial_count
            }
            
            test_results["status"] = "passed" if final_count > initial_count else "failed"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Agent registration test: {test_results['status']}")
        return test_results
    
    async def test_task_distribution(self) -> Dict[str, Any]:
        """Test task distribution and execution"""
        logger.info("🧪 Testing task distribution...")
        
        test_results = {
            "test_name": "task_distribution",
            "status": "running", 
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            # Create tasks with different priorities
            task_ids = []
            task_types = ["data_processing", "analysis", "general", "monitoring"]
            priorities = [TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW, TaskPriority.CRITICAL]
            
            for i in range(20):
                task_type = task_types[i % len(task_types)]
                priority = priorities[i % len(priorities)]
                
                task_id = await self.communication_layer.create_task(
                    task_type=task_type,
                    description=f"Test task {i+1}",
                    data={"test_data": f"value_{i}"},
                    priority=priority
                )
                task_ids.append(task_id)
            
            # Wait for tasks to be distributed and completed
            await asyncio.sleep(15)
            
            # Check task completion
            completed_tasks = 0
            failed_tasks = 0
            pending_tasks = 0
            
            for task_id in task_ids:
                if task_id in self.communication_layer.tasks:
                    task = self.communication_layer.tasks[task_id]
                    if task.status == TaskStatus.COMPLETED:
                        completed_tasks += 1
                    elif task.status == TaskStatus.FAILED:
                        failed_tasks += 1
                    else:
                        pending_tasks += 1
            
            test_results["details"] = {
                "tasks_created": len(task_ids),
                "tasks_completed": completed_tasks,
                "tasks_failed": failed_tasks,
                "tasks_pending": pending_tasks,
                "completion_rate": completed_tasks / len(task_ids) if task_ids else 0,
                "failure_rate": failed_tasks / len(task_ids) if task_ids else 0
            }
            
            # Test passes if most tasks completed successfully
            test_results["status"] = "passed" if completed_tasks >= len(task_ids) * 0.7 else "failed"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Task distribution test: {test_results['status']}")
        return test_results
    
    async def test_load_balancing(self) -> Dict[str, Any]:
        """Test load balancing across agents"""
        logger.info("🧪 Testing load balancing...")
        
        test_results = {
            "test_name": "load_balancing",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            # Create many tasks to test load balancing
            task_ids = []
            for i in range(50):
                task_id = await self.communication_layer.create_task(
                    task_type="general",
                    description=f"Load balancing test task {i+1}",
                    data={"test_index": i},
                    priority=TaskPriority.MEDIUM
                )
                task_ids.append(task_id)
            
            # Wait for distribution
            await asyncio.sleep(20)
            
            # Analyze task distribution across agents
            agent_task_counts = {}
            for agent in self.test_agents:
                agent_task_counts[agent.agent_id] = len(agent.processed_tasks)
            
            if agent_task_counts:
                max_tasks = max(agent_task_counts.values())
                min_tasks = min(agent_task_counts.values())
                avg_tasks = sum(agent_task_counts.values()) / len(agent_task_counts)
                load_balance_ratio = min_tasks / max_tasks if max_tasks > 0 else 0
            else:
                max_tasks = min_tasks = avg_tasks = load_balance_ratio = 0
            
            test_results["details"] = {
                "tasks_created": len(task_ids),
                "agent_task_distribution": agent_task_counts,
                "max_tasks_per_agent": max_tasks,
                "min_tasks_per_agent": min_tasks,
                "avg_tasks_per_agent": avg_tasks,
                "load_balance_ratio": load_balance_ratio
            }
            
            # Good load balancing if ratio > 0.6 (fairly even distribution)
            test_results["status"] = "passed" if load_balance_ratio > 0.6 else "failed"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Load balancing test: {test_results['status']}")
        return test_results
    
    async def test_synchronization(self) -> Dict[str, Any]:
        """Test agent synchronization mechanisms"""
        logger.info("🧪 Testing synchronization...")
        
        test_results = {
            "test_name": "synchronization",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            # Create sync point with subset of agents
            sync_agents = {agent.agent_id for agent in self.test_agents[:3]}
            sync_id = f"test_sync_{uuid.uuid4().hex[:8]}"
            
            await self.communication_layer.create_sync_point(
                sync_id=sync_id,
                required_agents=sync_agents,
                timeout_seconds=30,
                data={"test_sync": True}
            )
            
            # Wait for synchronization to complete
            await asyncio.sleep(10)
            
            # Check if sync completed
            sync_completed = sync_id not in self.communication_layer.sync_points
            
            test_results["details"] = {
                "sync_id": sync_id,
                "required_agents": list(sync_agents),
                "sync_completed": sync_completed,
                "agents_participated": len(sync_agents)
            }
            
            test_results["status"] = "passed" if sync_completed else "failed"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Synchronization test: {test_results['status']}")
        return test_results
    
    async def test_fault_tolerance(self) -> Dict[str, Any]:
        """Test system fault tolerance"""
        logger.info("🧪 Testing fault tolerance...")
        
        test_results = {
            "test_name": "fault_tolerance",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            # Create tasks before simulating failure
            task_ids_before = []
            for i in range(10):
                task_id = await self.communication_layer.create_task(
                    task_type="general",
                    description=f"Pre-failure task {i+1}",
                    data={"phase": "before"},
                    priority=TaskPriority.MEDIUM
                )
                task_ids_before.append(task_id)
            
            # Wait for some processing
            await asyncio.sleep(3)
            
            # Simulate agent failure by shutting down one agent
            if self.test_agents:
                failing_agent = self.test_agents[0]
                original_status = failing_agent.status
                await failing_agent.shutdown()
                
                # Wait for failure detection
                await asyncio.sleep(5)
                
                # Create more tasks to test system resilience
                task_ids_after = []
                for i in range(10):
                    task_id = await self.communication_layer.create_task(
                        task_type="general",
                        description=f"Post-failure task {i+1}",
                        data={"phase": "after"},
                        priority=TaskPriority.MEDIUM
                    )
                    task_ids_after.append(task_id)
                
                # Wait for recovery
                await asyncio.sleep(10)
                
                # Check system state
                total_tasks = len(task_ids_before) + len(task_ids_after)
                completed_tasks = sum(1 for task_id in task_ids_before + task_ids_after 
                                    if task_id in self.communication_layer.tasks and 
                                    self.communication_layer.tasks[task_id].status == TaskStatus.COMPLETED)
                
                test_results["details"] = {
                    "failing_agent": failing_agent.agent_id,
                    "tasks_before_failure": len(task_ids_before),
                    "tasks_after_failure": len(task_ids_after),
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "system_recovery": completed_tasks > 0,
                    "remaining_agents": len([a for a in self.test_agents[1:] if a.running])
                }
                
                # Test passes if system continued processing after failure
                test_results["status"] = "passed" if completed_tasks > total_tasks * 0.5 else "failed"
            else:
                test_results["status"] = "failed"
                test_results["error"] = "No test agents available"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Fault tolerance test: {test_results['status']}")
        return test_results
    
    async def test_performance(self) -> Dict[str, Any]:
        """Test system performance under load"""
        logger.info("🧪 Testing performance under load...")
        
        test_results = {
            "test_name": "performance",
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            start_time = time.time()
            
            # Create high volume of tasks
            task_ids = []
            batch_size = 100
            
            for batch in range(3):  # 300 tasks total
                batch_tasks = []
                for i in range(batch_size):
                    task_id = await self.communication_layer.create_task(
                        task_type="general",
                        description=f"Performance test task {batch*batch_size + i + 1}",
                        data={"batch": batch, "index": i},
                        priority=TaskPriority.MEDIUM
                    )
                    batch_tasks.append(task_id)
                task_ids.extend(batch_tasks)
                await asyncio.sleep(1)  # Small delay between batches
            
            creation_time = time.time() - start_time
            
            # Wait for processing to complete
            processing_start = time.time()
            await asyncio.sleep(30)  # Wait for processing
            processing_time = time.time() - processing_start
            
            # Analyze results
            completed = sum(1 for task_id in task_ids 
                          if task_id in self.communication_layer.tasks and 
                          self.communication_layer.tasks[task_id].status == TaskStatus.COMPLETED)
            
            throughput = completed / processing_time if processing_time > 0 else 0
            
            test_results["details"] = {
                "total_tasks_created": len(task_ids),
                "tasks_completed": completed,
                "creation_time": creation_time,
                "processing_time": processing_time,
                "throughput": throughput,
                "completion_rate": completed / len(task_ids) if task_ids else 0,
                "tasks_per_second": throughput
            }
            
            # Test passes if throughput > 5 tasks/second and completion rate > 80%
            test_results["status"] = "passed" if throughput > 5 and completed > len(task_ids) * 0.8 else "failed"
            
        except Exception as e:
            test_results["status"] = "failed"
            test_results["error"] = str(e)
        
        test_results["end_time"] = datetime.now().isoformat()
        logger.info(f"📊 Performance test: {test_results['status']}")
        return test_results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases"""
        logger.info("🚀 Starting comprehensive communication layer tests...")
        
        overall_results = {
            "test_suite": "Inter-Agent Communication Layer",
            "start_time": datetime.now().isoformat(),
            "environment": "test",
            "nats_url": self.nats_url,
            "tests": [],
            "summary": {}
        }
        
        # List of test methods
        test_methods = [
            self.test_basic_communication,
            self.test_agent_registration,
            self.test_task_distribution,
            self.test_load_balancing,
            self.test_synchronization,
            self.test_fault_tolerance,
            self.test_performance
        ]
        
        # Run each test
        for test_method in test_methods:
            try:
                result = await test_method()
                overall_results["tests"].append(result)
                logger.info(f"✅ {result['test_name']}: {result['status']}")
            except Exception as e:
                logger.error(f"❌ Failed to run {test_method.__name__}: {e}")
                overall_results["tests"].append({
                    "test_name": test_method.__name__,
                    "status": "error",
                    "error": str(e)
                })
        
        # Calculate summary
        total_tests = len(overall_results["tests"])
        passed_tests = sum(1 for test in overall_results["tests"] if test["status"] == "passed")
        failed_tests = sum(1 for test in overall_results["tests"] if test["status"] == "failed")
        error_tests = sum(1 for test in overall_results["tests"] if test["status"] == "error")
        
        overall_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "overall_status": "passed" if passed_tests == total_tests else "failed"
        }
        
        overall_results["end_time"] = datetime.now().isoformat()
        
        # Save results to file
        results_file = Path.home() / ".hero_core" / "cache" / "communication_test_results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(overall_results, f, indent=2)
        
        logger.info(f"📊 Test suite completed: {passed_tests}/{total_tests} tests passed")
        logger.info(f"📁 Results saved to: {results_file}")
        
        return overall_results
    
    async def cleanup(self):
        """Clean up test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        # Shutdown test agents
        for agent in self.test_agents:
            try:
                await agent.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down agent {agent.agent_id}: {e}")
        
        # Shutdown communication layer
        if self.communication_layer:
            await self.communication_layer.shutdown()
        
        logger.info("✅ Test environment cleaned up")

async def main():
    """Main test runner"""
    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test Inter-Agent Communication Layer")
    parser.add_argument("--nats-url", default="nats://localhost:4222", 
                       help="NATS server URL")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick test subset")
    args = parser.parse_args()
    
    test_suite = CommunicationLayerTestSuite(nats_url=args.nats_url)
    
    try:
        if not await test_suite.setup():
            logger.error("Failed to setup test environment")
            return 1
        
        if args.quick:
            # Run basic tests only
            results = await test_suite.test_basic_communication()
            logger.info(f"Quick test result: {results['status']}")
        else:
            # Run full test suite
            results = await test_suite.run_all_tests()
            
            # Print summary
            summary = results["summary"]
            print("\n" + "="*50)
            print("COMMUNICATION LAYER TEST RESULTS")
            print("="*50)
            print(f"Total Tests: {summary['total_tests']}")
            print(f"Passed: {summary['passed']}")
            print(f"Failed: {summary['failed']}")
            print(f"Errors: {summary['errors']}")
            print(f"Pass Rate: {summary['pass_rate']:.1%}")
            print(f"Overall Status: {summary['overall_status'].upper()}")
            print("="*50)
        
        return 0 if results.get("summary", {}).get("overall_status") == "passed" else 1
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return 1
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
