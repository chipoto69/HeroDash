#!/usr/bin/env python3
"""
LangSmith Tracer for Hero Command Centre
Provides unified tracing and observability for multi-agent workflows
Outputs: ~/.hero_core/cache/langsmith_traces.json
"""

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
import asyncio
from functools import wraps

try:
    from langsmith import Client, traceable
    from langsmith.run_helpers import get_current_run_tree
    from langsmith.run_trees import RunTree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    print("Warning: LangSmith not available. Install with: pip install langsmith")


class HeroLangSmithTracer:
    """Comprehensive LangSmith integration for Hero Command Centre"""
    
    def __init__(self, project_name: str = "hero-command-centre"):
        """Initialize the tracer with LangSmith configuration"""
        self.project_name = project_name
        self.client = None
        self.current_session = None
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.traces_file = self.cache_dir / "langsmith_traces.json"
        self.stats_file = self.cache_dir / "langsmith_stats.json"
        
        # Initialize LangSmith client if available
        self._init_client()
        
        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.traces = []
        self.stats = {
            "session_started": self.start_time.isoformat(),
            "total_traces": 0,
            "active_agents": set(),
            "workflow_count": 0,
            "error_count": 0,
            "token_usage": {"total": 0, "completion": 0, "prompt": 0}
        }
    
    def _init_client(self):
        """Initialize LangSmith client with environment configuration"""
        if not LANGSMITH_AVAILABLE:
            return
            
        try:
            # Check for required environment variables
            api_key = os.getenv('LANGSMITH_API_KEY')
            if not api_key:
                print("Warning: LANGSMITH_API_KEY not set. Tracing disabled.")
                return
                
            endpoint = os.getenv('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
            
            self.client = Client(
                api_url=endpoint,
                api_key=api_key
            )
            
            # Test connection
            try:
                # Try to get or create the project
                projects = list(self.client.list_projects())
                project_exists = any(p.name == self.project_name for p in projects)
                
                if not project_exists:
                    self.client.create_project(
                        project_name=self.project_name,
                        description="Hero Command Centre Multi-Agent Monitoring"
                    )
                    
                print(f"✅ LangSmith connected - Project: {self.project_name}")
                
            except Exception as e:
                print(f"Warning: LangSmith connection test failed: {e}")
                self.client = None
                
        except Exception as e:
            print(f"Error initializing LangSmith client: {e}")
            self.client = None
    
    def create_workflow_trace(self, workflow_name: str, agent_type: str, 
                            inputs: Dict[str, Any] = None, 
                            metadata: Dict[str, Any] = None) -> str:
        """Create a new workflow trace"""
        trace_id = str(uuid.uuid4())
        inputs = inputs or {}
        metadata = metadata or {}
        
        trace = {
            "id": trace_id,
            "workflow_name": workflow_name,
            "agent_type": agent_type,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "inputs": inputs,
            "outputs": None,
            "metadata": {
                "hero_session": self.session_id,
                "agent_framework": "hero-command-centre",
                **metadata
            },
            "duration_ms": None,
            "error": None,
            "children": []
        }
        
        self.traces.append(trace)
        self.stats["total_traces"] += 1
        self.stats["workflow_count"] += 1
        self.stats["active_agents"].add(agent_type)
        
        # Create LangSmith run if client available
        if self.client:
            try:
                run = self.client.create_run(
                    id=trace_id,
                    project_name=self.project_name,
                    name=f"hero:{workflow_name}",
                    run_type="chain",
                    inputs=inputs,
                    start_time=datetime.now(),
                    tags=[agent_type, "hero-command-centre", "multi-agent"],
                    metadata=trace["metadata"]
                )
            except Exception as e:
                print(f"Warning: Failed to create LangSmith run: {e}")
        
        self._save_cache()
        return trace_id
    
    def update_trace(self, trace_id: str, outputs: Dict[str, Any] = None, 
                    error: str = None, status: str = None):
        """Update an existing trace with results"""
        for trace in self.traces:
            if trace["id"] == trace_id:
                if outputs:
                    trace["outputs"] = outputs
                if error:
                    trace["error"] = error
                    trace["status"] = "error"
                    self.stats["error_count"] += 1
                elif status:
                    trace["status"] = status
                
                # Calculate duration
                start_time = datetime.fromisoformat(trace["timestamp"])
                trace["duration_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # Update LangSmith run
                if self.client:
                    try:
                        self.client.update_run(
                            run_id=trace_id,
                            outputs=outputs,
                            error=error,
                            end_time=datetime.now()
                        )
                    except Exception as e:
                        print(f"Warning: Failed to update LangSmith run: {e}")
                
                break
        
        self._save_cache()
    
    def add_agent_interaction(self, trace_id: str, agent_name: str, 
                            action: str, details: Dict[str, Any] = None):
        """Add an agent interaction to a workflow trace"""
        interaction = {
            "id": str(uuid.uuid4()),
            "agent_name": agent_name,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        for trace in self.traces:
            if trace["id"] == trace_id:
                trace["children"].append(interaction)
                break
        
        self._save_cache()
    
    def traceable_function(self, name: str = None, agent_type: str = "generic"):
        """Decorator to automatically trace function calls"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                func_name = name or func.__name__
                trace_id = self.create_workflow_trace(
                    workflow_name=func_name,
                    agent_type=agent_type,
                    inputs={"args": str(args)[:200], "kwargs": str(kwargs)[:200]}
                )
                
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    self.update_trace(
                        trace_id,
                        outputs={"result": str(result)[:500], "duration_ms": duration},
                        status="completed"
                    )
                    return result
                    
                except Exception as e:
                    self.update_trace(
                        trace_id,
                        error=str(e),
                        status="error"
                    )
                    raise
            
            return wrapper
        return decorator
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about agent activities"""
        active_traces = [t for t in self.traces if t["status"] == "running"]
        completed_traces = [t for t in self.traces if t["status"] == "completed"]
        error_traces = [t for t in self.traces if t["status"] == "error"]
        
        # Calculate average duration for completed traces
        avg_duration = 0
        if completed_traces:
            total_duration = sum(t.get("duration_ms", 0) for t in completed_traces)
            avg_duration = total_duration / len(completed_traces)
        
        # Agent type breakdown
        agent_breakdown = {}
        for trace in self.traces:
            agent_type = trace["agent_type"]
            if agent_type not in agent_breakdown:
                agent_breakdown[agent_type] = {"count": 0, "errors": 0, "avg_duration": 0}
            
            agent_breakdown[agent_type]["count"] += 1
            if trace["status"] == "error":
                agent_breakdown[agent_type]["errors"] += 1
        
        return {
            "session_id": self.session_id,
            "session_duration": str(datetime.now() - self.start_time),
            "total_traces": len(self.traces),
            "active_traces": len(active_traces),
            "completed_traces": len(completed_traces),
            "error_traces": len(error_traces),
            "success_rate": len(completed_traces) / len(self.traces) if self.traces else 0,
            "average_duration_ms": avg_duration,
            "agent_breakdown": agent_breakdown,
            "active_agents": list(self.stats["active_agents"]),
            "langsmith_enabled": self.client is not None,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_recent_activity(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """Get recent agent activity for dashboard display"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_traces = []
        
        for trace in self.traces:
            trace_time = datetime.fromisoformat(trace["timestamp"])
            if trace_time >= cutoff:
                recent_traces.append({
                    "workflow": trace["workflow_name"],
                    "agent": trace["agent_type"],
                    "status": trace["status"],
                    "duration": trace.get("duration_ms"),
                    "timestamp": trace["timestamp"],
                    "interactions": len(trace["children"])
                })
        
        return sorted(recent_traces, key=lambda x: x["timestamp"], reverse=True)
    
    def _save_cache(self):
        """Save traces and statistics to cache files"""
        try:
            # Save traces
            traces_data = {
                "session_id": self.session_id,
                "traces": self.traces[-100:],  # Keep last 100 traces
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.traces_file, 'w') as f:
                json.dump(traces_data, f, indent=2, default=str)
            
            # Save statistics
            stats_data = self.get_agent_statistics()
            with open(self.stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving trace cache: {e}")
    
    def cleanup_old_traces(self, hours: int = 24):
        """Clean up traces older than specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        self.traces = [
            trace for trace in self.traces
            if datetime.fromisoformat(trace["timestamp"]) >= cutoff
        ]
        self._save_cache()


# Global tracer instance
_tracer = None

def get_tracer() -> HeroLangSmithTracer:
    """Get or create the global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = HeroLangSmithTracer()
    return _tracer


def trace_hero_function(name: str = None, agent_type: str = "hero-monitor"):
    """Convenience decorator for tracing Hero dashboard functions"""
    return get_tracer().traceable_function(name=name, agent_type=agent_type)


def trace_agent_workflow(workflow_name: str, agent_type: str, 
                        inputs: Dict[str, Any] = None):
    """Context manager for tracing agent workflows"""
    class WorkflowTracer:
        def __init__(self, tracer, workflow_name, agent_type, inputs):
            self.tracer = tracer
            self.workflow_name = workflow_name
            self.agent_type = agent_type
            self.inputs = inputs
            self.trace_id = None
        
        def __enter__(self):
            self.trace_id = self.tracer.create_workflow_trace(
                self.workflow_name, self.agent_type, self.inputs
            )
            return self.trace_id
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                self.tracer.update_trace(
                    self.trace_id, 
                    error=str(exc_val),
                    status="error"
                )
            else:
                self.tracer.update_trace(
                    self.trace_id,
                    status="completed"
                )
    
    return WorkflowTracer(get_tracer(), workflow_name, agent_type, inputs)


def main():
    """Main function for testing and standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hero LangSmith Tracer")
    parser.add_argument("--test", action="store_true", help="Run test traces")
    parser.add_argument("--stats", action="store_true", help="Show current statistics")
    parser.add_argument("--cleanup", type=int, help="Cleanup traces older than N hours")
    
    args = parser.parse_args()
    
    tracer = get_tracer()
    
    if args.test:
        print("Running test traces...")
        
        # Test workflow trace
        with trace_agent_workflow("test_monitoring", "hero-monitor", {"test": True}) as trace_id:
            time.sleep(0.1)  # Simulate work
            tracer.add_agent_interaction(trace_id, "test-agent", "data_collection")
        
        # Test function tracing
        @trace_hero_function("test_function", "test-agent")
        def test_function(x):
            return x * 2
        
        result = test_function(5)
        print(f"Test function result: {result}")
        
        print("✅ Test traces completed")
    
    if args.stats:
        stats = tracer.get_agent_statistics()
        print("\n📊 LangSmith Tracer Statistics:")
        print(json.dumps(stats, indent=2, default=str))
        
        print("\n🕒 Recent Activity:")
        recent = tracer.get_recent_activity(60)
        for activity in recent[:5]:
            print(f"  {activity['timestamp'][:19]} | {activity['workflow']} | {activity['status']}")
    
    if args.cleanup:
        print(f"Cleaning up traces older than {args.cleanup} hours...")
        tracer.cleanup_old_traces(args.cleanup)
        print("✅ Cleanup completed")
    
    if not any([args.test, args.stats, args.cleanup]):
        # Default: save current statistics
        tracer._save_cache()
        print("💾 Saved current trace data to cache")


if __name__ == "__main__":
    main()