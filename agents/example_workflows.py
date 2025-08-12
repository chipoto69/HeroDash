#!/usr/bin/env python3
"""
Example Workflows for Hero Command Centre Agents
Demonstrates multi-agent collaboration patterns and integration
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add path for Hero monitors
sys.path.append(str(Path(__file__).parent.parent / "monitors"))

try:
    from agent_coordinator import get_coordinator, TaskPriority
    from langsmith_tracer import get_tracer, trace_hero_function
    HERO_AVAILABLE = True
except ImportError:
    HERO_AVAILABLE = False
    print("Hero framework not available - running in demo mode")

def display_header():
    """Display example workflow header"""
    print("\n" + "="*70)
    print("🚀 HERO COMMAND CENTRE - AGENT WORKFLOW EXAMPLES")
    print("="*70)
    print("Demonstrating multi-agent collaboration in action")
    print()

@trace_hero_function("workflow_demo", "demo-runner")
def run_basic_workflow_demo():
    """Run a basic workflow demonstration"""
    print("📋 BASIC WORKFLOW DEMO")
    print("-" * 40)
    
    if not HERO_AVAILABLE:
        print("⚠️  Running in simulation mode (Hero framework not available)")
        return simulate_workflow()
    
    coordinator = get_coordinator()
    tracer = get_tracer()
    
    # Submit a knowledge analysis task
    print("1. Submitting knowledge analysis task...")
    task_id = coordinator.submit_task(
        "system_knowledge_analysis",
        "Analyze current system performance and identify optimization opportunities",
        ["knowledge_graph_management", "pattern_recognition"],
        TaskPriority.HIGH,
        {
            "analysis_type": "performance_optimization",
            "time_range": "24h",
            "focus_areas": ["agent_coordination", "resource_utilization"]
        }
    )
    print(f"   ✅ Task submitted: {task_id}")
    
    # Submit a coordination task
    print("2. Submitting workflow coordination task...")
    task_id2 = coordinator.submit_task(
        "multi_agent_workflow",
        "Coordinate multi-step data processing workflow",
        ["workflow_orchestration", "task_distribution"],
        TaskPriority.NORMAL,
        {
            "workflow_steps": ["data_collection", "analysis", "insight_generation"],
            "parallel_execution": True
        }
    )
    print(f"   ✅ Task submitted: {task_id2}")
    
    # Monitor task execution
    print("3. Monitoring task execution...")
    for i in range(5):
        status = coordinator.get_system_status()
        running_tasks = status.get("tasks", {}).get("running", 0)
        completed_tasks = status.get("tasks", {}).get("completed", 0)
        
        print(f"   📊 Running: {running_tasks}, Completed: {completed_tasks}")
        time.sleep(2)
        
        if running_tasks == 0:
            break
    
    print("   ✅ Workflow execution completed")
    print()

def simulate_workflow():
    """Simulate workflow execution for demo purposes"""
    steps = [
        "🔍 Task Orchestrator analyzing requirements...",
        "🧠 Knowledge Integration processing patterns...", 
        "⚡ Task distribution across agent network...",
        "📊 Real-time coordination and monitoring...",
        "✨ Insight generation and knowledge consolidation...",
        "✅ Workflow completed successfully"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"   {step}")
        time.sleep(1.5)
    
    print()

def demonstrate_agent_capabilities():
    """Show agent capabilities and integration points"""
    print("🤖 AGENT CAPABILITIES OVERVIEW")
    print("-" * 40)
    
    capabilities = {
        "Task Orchestrator": [
            "🎯 Intelligent task assignment",
            "⚖️  Dynamic load balancing", 
            "🔄 Workflow coordination",
            "📈 Performance optimization",
            "🚨 Failure handling & recovery"
        ],
        "Knowledge Integration": [
            "🧩 Temporal knowledge graphs",
            "🔍 Semantic pattern recognition",
            "💡 Insight generation",
            "🔗 Multi-source data synthesis",
            "📚 Context preservation"
        ]
    }
    
    for agent_type, agent_capabilities in capabilities.items():
        print(f"\n{agent_type}:")
        for capability in agent_capabilities:
            print(f"   {capability}")
    
    print()

def show_integration_status():
    """Show current integration status"""
    print("🔌 INTEGRATION STATUS")
    print("-" * 40)
    
    # Check cache files
    cache_dir = Path.home() / ".hero_core" / "cache"
    
    integration_files = {
        "agent_runtime_status.json": "Agent Runtime",
        "agent_coordination.json": "Task Coordination", 
        "langsmith_stats.json": "LangSmith Tracing",
        "chimera_integration.json": "Chimera Bridge"
    }
    
    for filename, description in integration_files.items():
        file_path = cache_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    timestamp = data.get('timestamp', 'Unknown')
                print(f"   ✅ {description}: Active (Updated: {timestamp[:19]})")
            except:
                print(f"   ⚠️  {description}: File exists but unreadable")
        else:
            print(f"   ❌ {description}: Not found")
    
    print()

def create_sample_workflow_file():
    """Create a sample workflow configuration"""
    print("📝 CREATING SAMPLE WORKFLOW")
    print("-" * 40)
    
    sample_workflow = {
        "workflow_id": "hero_demo_workflow_001",
        "name": "System Analysis and Optimization Pipeline",
        "description": "Multi-agent workflow for comprehensive system analysis",
        "created_at": datetime.now().isoformat(),
        "steps": [
            {
                "step_id": "data_collection",
                "name": "System Data Collection",
                "agent_type": "task_orchestrator",
                "required_capabilities": ["system_monitoring", "data_collection"],
                "inputs": {
                    "collection_scope": ["performance_metrics", "agent_activities", "resource_usage"],
                    "time_range": "24h"
                },
                "dependencies": []
            },
            {
                "step_id": "pattern_analysis", 
                "name": "Pattern Recognition and Analysis",
                "agent_type": "knowledge_integration",
                "required_capabilities": ["pattern_recognition", "temporal_analysis"],
                "inputs": {
                    "analysis_type": "performance_patterns",
                    "pattern_scope": "multi_agent_coordination"
                },
                "dependencies": ["data_collection"]
            },
            {
                "step_id": "optimization_planning",
                "name": "Optimization Strategy Planning",
                "agent_type": "task_orchestrator", 
                "required_capabilities": ["workflow_orchestration", "optimization_planning"],
                "inputs": {
                    "optimization_goals": ["reduce_latency", "improve_throughput", "balance_load"],
                    "constraint_factors": ["resource_limits", "performance_requirements"]
                },
                "dependencies": ["pattern_analysis"]
            },
            {
                "step_id": "knowledge_consolidation",
                "name": "Knowledge Graph Update",
                "agent_type": "knowledge_integration",
                "required_capabilities": ["knowledge_graph_management", "insight_generation"],
                "inputs": {
                    "consolidation_scope": "optimization_insights",
                    "persistence_level": "long_term"
                },
                "dependencies": ["optimization_planning"]
            }
        ],
        "execution_mode": "sequential_with_parallel_branches",
        "timeout_minutes": 30,
        "retry_policy": {
            "max_retries": 3,
            "backoff_strategy": "exponential"
        },
        "success_criteria": {
            "all_steps_completed": True,
            "quality_threshold": 0.8,
            "performance_within_limits": True
        }
    }
    
    # Save workflow file
    workflow_file = Path(__file__).parent / "sample_workflow.json"
    with open(workflow_file, 'w') as f:
        json.dump(sample_workflow, f, indent=2)
    
    print(f"   ✅ Sample workflow saved to: {workflow_file}")
    print(f"   📋 Steps: {len(sample_workflow['steps'])}")
    print(f"   🎯 Mode: {sample_workflow['execution_mode']}")
    print()

def show_next_steps():
    """Show next steps for using the agent system"""
    print("🎯 NEXT STEPS - ACTIVATING YOUR AGENTS")
    print("="*70)
    
    steps = [
        {
            "step": "1. Set up LangSmith (if using real LLM)",
            "commands": [
                "export LANGSMITH_API_KEY='your_api_key_here'",
                "export LANGSMITH_PROJECT='hero-command-centre'"
            ],
            "note": "Optional - agents will use mock provider without this"
        },
        {
            "step": "2. Launch the Agent Runtime System", 
            "commands": [
                "./agents/launch_agents.sh start"
            ],
            "note": "This starts NATS, agent runtime, and monitoring"
        },
        {
            "step": "3. Launch Hero Dashboard",
            "commands": [
                "./launch_hero_optimized_fixed.sh"
            ],
            "note": "Watch agents come alive in real-time!"
        },
        {
            "step": "4. Test Agent Communication",
            "commands": [
                "python3 agents/test_agent_integration.py --test workflow",
                "python3 monitors/agent_coordinator.py --status"
            ],
            "note": "Verify everything is working correctly"
        },
        {
            "step": "5. Submit Your First Task",
            "commands": [
                "python3 -c \"",
                "from monitors.agent_coordinator import get_coordinator, TaskPriority",
                "coordinator = get_coordinator()",
                "task_id = coordinator.submit_task(",
                "    'hello_world_analysis',",
                "    'Analyze the Hero Command Centre system status',", 
                "    ['system_monitoring', 'knowledge_graph_management'],",
                "    TaskPriority.NORMAL",
                ")",
                "print(f'Task submitted: {task_id}')",
                "\""
            ],
            "note": "Watch the task get processed in the dashboard!"
        }
    ]
    
    for i, step_info in enumerate(steps, 1):
        print(f"\n{step_info['step']}")
        print("-" * len(step_info['step']))
        
        for cmd in step_info['commands']:
            print(f"   {cmd}")
        
        if step_info.get('note'):
            print(f"   💡 {step_info['note']}")
    
    print("\n" + "="*70)
    print("🎉 Your AI agents are ready to revolutionize your workflow!")
    print("="*70)

def main():
    """Main demonstration function"""
    display_header()
    
    # Show system capabilities
    demonstrate_agent_capabilities()
    
    # Check integration status
    show_integration_status()
    
    # Create sample workflow
    create_sample_workflow_file()
    
    # Run basic workflow demo
    run_basic_workflow_demo()
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()