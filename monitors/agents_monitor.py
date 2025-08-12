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

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def main():
    cache_dir = Path.home() / ".hero_core" / "cache"
    out_file = cache_dir / "agents_status.json"
    procs = list_processes_ps()
    agents = filter_agents(procs)
    total, top_cpu, buckets = summarize(agents)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "total_agents": total,
        "buckets": buckets,
        "top": top_cpu,
    }
    save_json(out_file, payload)

if __name__ == "__main__":
    main()

