#!/usr/bin/env python3
"""
Token Usage Analyzer
Enriches Claude token usage with simple trends and moving averages.
Reads: ~/.hero_core/cache/claude_usage.json
Writes: ~/.hero_core/cache/token_analysis.json and updates token_history.json
"""
import json
import os
from datetime import datetime
from pathlib import Path

CACHE = Path.home() / ".hero_core" / "cache"
USAGE = CACHE / "claude_usage.json"
HIST = CACHE / "token_history.json"
OUT = CACHE / "token_analysis.json"

def load_json(p):
    try:
        with open(p, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def save_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, p)

def main():
    usage = load_json(USAGE) or {}
    total_tokens = int(usage.get("total_tokens", 0))
    ts = datetime.now().isoformat()

    hist = load_json(HIST) or {"samples": []}
    hist["samples"].append({"t": ts, "tokens": total_tokens})
    # Keep last 200 samples
    hist["samples"] = hist["samples"][-200:]

    # Compute simple deltas and moving average over last N samples
    values = [s["tokens"] for s in hist["samples"]]
    deltas = [max(0, values[i] - values[i-1]) for i in range(1, len(values))]
    recent = deltas[-20:] if deltas else []
    avg_rate = sum(recent)/len(recent) if recent else 0
    trend = "flat"
    if avg_rate > 2000:
        trend = "high"
    elif avg_rate > 200:
        trend = "medium"

    analysis = {
        "timestamp": ts,
        "current_tokens": total_tokens,
        "avg_tokens_per_sample": int(avg_rate),
        "trend": trend,
        "samples": len(hist["samples"]),
    }

    save_json(HIST, hist)
    save_json(OUT, analysis)

if __name__ == "__main__":
    main()

