#!/usr/bin/env python3
"""
Agents Monitor
Collects AI/agent-related process info and writes a compact JSON snapshot.
Outputs: ~/.hero_core/cache/agents_status.json
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add path for Hero monitors
sys.path.append(str(Path(__file__).parent))

try:
    from langsmith_tracer import get_tracer, trace_hero_function
except ImportError:
    # Fallback if langsmith_tracer not available
    def get_tracer():
        return None
    def trace_hero_function(name=None, agent_type="hero-monitor"):
        def decorator(func):
            return func
        return decorator

AGENT_KEYWORDS = [
    # Foundation/model runners
    "claude", "ccm", "ollama", "openai", "qwen", "llama", "vllm",
    # Coding assistants/editors
    "code", "cursor", "aider", "swe", "copilot", "windsurf",
    # Chimera/LangGraph agents
    "langgraph", "langsmith", "chimera", "nats", "embedder", "retriever",
    # Multi-agent frameworks
    "autogen", "crewai", "swarm", "multi-agent", "orchestrator",
]

def list_processes_ps():
    import subprocess, shlex
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=2)
    except Exception:
        return []
    lines = result.stdout.splitlines()[1:]
    procs = []
    for ln in lines:
        parts = ln.split(None, 10)
        if len(parts) < 11:
            continue
        user, pid, cpu, mem, vsz, rss, _, _, _, _, cmd = parts
        try:
            procs.append({
                "pid": int(pid),
                "cpu": float(cpu),
                "mem": float(mem),
                "cmd": cmd.lower(),
                "user": user,
            })
        except Exception:
            continue
    return procs

@trace_hero_function("filter_agents", "agents-monitor")
def filter_agents(procs):
    """Filter processes to find AI agents and related services"""
    agents = []
    for p in procs:
        if any(k in p["cmd"] for k in AGENT_KEYWORDS):
            # Enhanced agent classification
            agent_type = classify_agent_type(p["cmd"])
            p["agent_type"] = agent_type
            p["framework"] = detect_framework(p["cmd"])
            agents.append(p)
    return agents

@trace_hero_function("summarize_agents", "agents-monitor")
def summarize(agents):
    """Create comprehensive summary of agent activities"""
    total = len(agents)
    top_cpu = sorted(agents, key=lambda x: x.get("cpu", 0.0), reverse=True)[:5]
    top_cpu = [
        {
            "pid": a["pid"],
            "cpu": round(a.get("cpu", 0.0), 1),
            "mem": round(a.get("mem", 0.0), 1),
            "name": a["cmd"][:60],
            "type": a.get("agent_type", "unknown"),
            "framework": a.get("framework", "unknown"),
        }
        for a in top_cpu
    ]
    
    # Enhanced categorization
    buckets = {
        "models": sum(1 for a in agents if any(k in a["cmd"] for k in ["claude", "qwen", "llama", "ollama", "vllm"])),
        "editors": sum(1 for a in agents if any(k in a["cmd"] for k in ["code", "cursor", "windsurf"])),
        "assistants": sum(1 for a in agents if any(k in a["cmd"] for k in ["aider", "copilot", "swe"])),
        "chimera": sum(1 for a in agents if any(k in a["cmd"] for k in ["chimera", "langgraph", "nats"])),
        "multi_agent": sum(1 for a in agents if any(k in a["cmd"] for k in ["autogen", "crewai", "swarm", "orchestrator"]))
    }
    
    # Framework breakdown
    frameworks = {}
    for agent in agents:
        fw = agent.get("framework", "unknown")
        frameworks[fw] = frameworks.get(fw, 0) + 1
    
    # Performance metrics
    total_cpu = sum(a.get("cpu", 0.0) for a in agents)
    total_mem = sum(a.get("mem", 0.0) for a in agents)
    
    return total, top_cpu, buckets, frameworks, total_cpu, total_mem

def classify_agent_type(cmd: str) -> str:
    """Classify agent type based on command string"""
    cmd_lower = cmd.lower()
    
    if any(k in cmd_lower for k in ["claude", "ccm"]):
        return "claude_agent"
    elif any(k in cmd_lower for k in ["ollama", "vllm", "llama"]):
        return "local_llm"
    elif any(k in cmd_lower for k in ["cursor", "code", "windsurf"]):
        return "code_editor"
    elif any(k in cmd_lower for k in ["chimera", "langgraph"]):
        return "chimera_agent"
    elif any(k in cmd_lower for k in ["nats", "jetstream"]):
        return "messaging_service"
    elif any(k in cmd_lower for k in ["embedder", "retriever"]):
        return "knowledge_agent"
    elif any(k in cmd_lower for k in ["orchestrator", "supervisor"]):
        return "coordinator_agent"
    elif any(k in cmd_lower for k in ["autogen", "crewai", "swarm"]):
        return "multi_agent_framework"
    else:
        return "generic_agent"

def detect_framework(cmd: str) -> str:
    """Detect the framework being used"""
    cmd_lower = cmd.lower()
    
    if "chimera" in cmd_lower:
        return "chimera"
    elif "langgraph" in cmd_lower:
        return "langgraph"
    elif "autogen" in cmd_lower:
        return "autogen"
    elif "crewai" in cmd_lower:
        return "crewai"
    elif "swarm" in cmd_lower:
        return "swarm"
    elif "nats" in cmd_lower:
        return "nats"
    elif any(k in cmd_lower for k in ["claude", "openai"]):
        return "llm_api"
    elif "ollama" in cmd_lower:
        return "ollama"
    else:
        return "unknown"

def get_chimera_status() -> Dict[str, Any]:
    """Get status of Chimera-specific services"""
    chimera_base = "/Users/rudlord/q3/frontline"
    
    status = {
        "nats_running": False,
        "langgraph_active": False,
        "agents_count": 0,
        "services": []
    }
    
    # Check if NATS is running
    try:
        import subprocess
        result = subprocess.run(["pgrep", "-f", "nats-server"], 
                              capture_output=True, text=True, timeout=2)
        status["nats_running"] = len(result.stdout.strip()) > 0
    except Exception:
        pass
    
    # Check for LangGraph processes
    try:
        result = subprocess.run(["pgrep", "-f", "langgraph"], 
                              capture_output=True, text=True, timeout=2)
        status["langgraph_active"] = len(result.stdout.strip()) > 0
    except Exception:
        pass
    
    # Check for Chimera-specific services
    chimera_services = ["embedder", "retriever", "memory", "orchestrator"]
    for service in chimera_services:
        try:
            result = subprocess.run(["pgrep", "-f", service], 
                                  capture_output=True, text=True, timeout=1)
            if result.stdout.strip():
                status["services"].append(service)
                status["agents_count"] += 1
        except Exception:
            pass
    
    return status

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

@trace_hero_function("main_agents_monitor", "agents-monitor")
def main():
    """Main function to collect and save agent status"""
    cache_dir = Path.home() / ".hero_core" / "cache"
    out_file = cache_dir / "agents_status.json"
    
    # Get tracer for workflow tracking
    tracer = get_tracer()
    if tracer:
        tracer.add_agent_interaction(
            tracer.session_id, 
            "agents-monitor", 
            "collect_agent_data"
        )
    
    try:
        procs = list_processes_ps()
        agents = filter_agents(procs)
        total, top_cpu, buckets, frameworks, total_cpu, total_mem = summarize(agents)
        
        # Get Chimera-specific status
        chimera_status = get_chimera_status()
        
        # Enhanced payload with more comprehensive data
        payload = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": total,
            "buckets": buckets,
            "frameworks": frameworks,
            "top_cpu": top_cpu,
            "performance": {
                "total_cpu_usage": round(total_cpu, 2),
                "total_memory_usage": round(total_mem, 2),
                "average_cpu_per_agent": round(total_cpu / total if total > 0 else 0, 2)
            },
            "chimera_status": chimera_status,
            "hero_integration": {
                "langsmith_enabled": tracer is not None and tracer.client is not None if tracer else False,
                "tracing_active": tracer is not None,
                "monitor_version": "2.0_enhanced"
            },
            "metadata": {
                "scan_duration_ms": 0,  # Could be calculated
                "process_count_total": len(procs),
                "agent_detection_rate": round(total / len(procs) if procs else 0, 3)
            }
        }
        
        save_json(out_file, payload)
        
        # Update tracer statistics if available
        if tracer:
            tracer.stats["active_agents"].update(frameworks.keys())
            tracer._save_cache()
            
    except Exception as e:
        # Save error state
        error_payload = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "total_agents": 0,
            "buckets": {},
            "status": "error"
        }
        save_json(out_file, error_payload)
        
        if tracer:
            tracer.add_agent_interaction(
                tracer.session_id,
                "agents-monitor",
                "error",
                {"error": str(e)}
            )

if __name__ == "__main__":
    main()

