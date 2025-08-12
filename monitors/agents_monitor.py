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

AGENT_KEYWORDS = [
    # Foundation/model runners
    "claude", "ccm", "ollama", "openai", "qwen", "llama", "vllm",
    # Coding assistants/editors
    "code", "cursor", "aider", "swe", "copilot", "windsurf",
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

def filter_agents(procs):
    agents = []
    for p in procs:
        if any(k in p["cmd"] for k in AGENT_KEYWORDS):
            agents.append(p)
    return agents

def summarize(agents):
    total = len(agents)
    top_cpu = sorted(agents, key=lambda x: x.get("cpu", 0.0), reverse=True)[:5]
    top_cpu = [
        {
            "pid": a["pid"],
            "cpu": round(a.get("cpu", 0.0), 1),
            "mem": round(a.get("mem", 0.0), 1),
            "name": a["cmd"][:60],
        }
        for a in top_cpu
    ]
    buckets = {
        "models": sum(1 for a in agents if any(k in a["cmd"] for k in ["claude", "qwen", "llama", "ollama", "vllm"])),
        "editors": sum(1 for a in agents if any(k in a["cmd"] for k in ["code", "cursor", "windsurf"])),
        "assistants": sum(1 for a in agents if any(k in a["cmd"] for k in ["aider", "copilot", "swe"]))
    }
    return total, top_cpu, buckets

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

