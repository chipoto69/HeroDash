#!/usr/bin/env python3
"""
Code Activity Monitor
Aggregates git activity for configured repositories over the last 7 days.
Outputs: ~/.hero_core/cache/code_activity.json

Configuration (optional): ~/.hero_core/config.json
{
  "projects": ["/path/to/repo1", "/path/to/repo2"]
}
If missing, defaults to the current repository if it contains a .git folder.
"""
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

def read_config():
    cfg_path = Path.home() / ".hero_core" / "config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text())
        except Exception:
            pass
    # fallback: current dir if it's a git repo
    cwd = Path.cwd()
    projects = []
    if (cwd / ".git").exists():
        projects.append(str(cwd))
    return {"projects": projects}

def run(cmd, timeout=5):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        class R: pass
        r = R(); r.returncode = 1; r.stdout = ""; r.stderr = ""
        return r

def repo_stats(repo):
    # Ensure it's a git repo
    if not (Path(repo) / ".git").exists():
        return None
    # Numstat since 7 days
    r = run(["git", "-C", repo, "log", "--since=7.days", "--pretty=tformat:", "--numstat"], timeout=8)
    insertions = deletions = files = 0
    if r.returncode == 0:
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
                insertions += int(parts[0])
                deletions += int(parts[1])
                files += 1

    # Commits per day for 7 days
    day_counts = defaultdict(int)
    r2 = run(["git", "-C", repo, "log", "--since=7.days", "--pretty=%ad", "--date=format:%Y-%m-%d"], timeout=8)
    if r2.returncode == 0:
        for d in r2.stdout.splitlines():
            if d:
                day_counts[d] += 1
    # Build ordered last 7 days list
    days = []
    today = datetime.now().date()
    for i in range(6, -1, -1):
        dt = today - timedelta(days=i)
        ds = dt.strftime("%Y-%m-%d")
        days.append({"date": ds, "commits": day_counts.get(ds, 0)})

    # Current branch
    branch = "-"
    rb = run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], timeout=3)
    if rb.returncode == 0:
        branch = rb.stdout.strip() or "-"

    return {
        "path": str(repo),
        "branch": branch,
        "insertions": insertions,
        "deletions": deletions,
        "files_changed": files,
        "days": days,
    }

def sparkline(values):
    blocks = "▁▂▃▄▅▆▇█"
    if not values:
        return ""
    vmax = max(values) or 1
    return "".join(blocks[min(7, int(v * 7 / vmax))] for v in values)

def main():
    cfg = read_config()
    projects = cfg.get("projects", [])
    stats = []
    for p in projects:
        s = repo_stats(p)
        if s:
            s["spark_commits"] = sparkline([d["commits"] for d in s["days"]])
            stats.append(s)

    summary = {
        "total_repos": len(stats),
        "total_insertions": sum(s["insertions"] for s in stats),
        "total_deletions": sum(s["deletions"] for s in stats),
        "timestamp": datetime.now().isoformat(),
        "repos": stats[:5],  # keep JSON small for the dashboard
    }

    cache_dir = Path.home() / ".hero_core" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / "code_activity.json"
    tmp = out.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(summary, f, indent=2)
    os.replace(tmp, out)

if __name__ == "__main__":
    main()

