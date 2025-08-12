# HERO CORE - Unified Command Centre

```
    ██╗  ██╗███████╗██████╗  ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██║  ██║██╔════╝██╔══██╗██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ███████║█████╗  ██████╔╝██║   ██║    ██║     ██║   ██║██████╔╝█████╗  
    ██╔══██║██╔══╝  ██╔══██╗██║   ██║    ██║     ██║   ██║██╔══██╗██╔══╝  
    ██║  ██║███████╗██║  ██║╚██████╔╝    ╚██████╗╚██████╔╝██║  ██║███████╗
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
                                [ by Quantropy ]
```

## Overview

Hero Core is the unified command centre that merges all dashboard capabilities into one powerful monitoring system. It provides real-time monitoring of AI systems, knowledge bases, and system metrics with a clean, flicker-free interface.

## Quick Start

### Launch Hero Core (Recommended)
```bash
./hero
# or
./launch_hero.sh
# or
./dashboard_control.sh hero
```

### Alternative Launch Methods
```bash
# Interactive menu
./dashboard_control.sh

# Direct command
./hero_core.sh
```

## Features

### 🤖 AI Systems Monitoring
- **Claude Code**: Active instances and working directories
- **Qwen-code**: Runtime status
- **Gemini AI**: Connection status
- **VS Code**: Helper processes

### 🧠 Chimera Knowledge Base
- **Graphiti Engine**: Temporal knowledge graphs with Neo4j
  - Entity tracking
  - Episode management
  - Edge relationships
- **Redis**: Key-value memory store
- **Archives**: JSON data files

### 📊 System Metrics
- **CPU Usage**: Real-time percentage with visual bar
- **Memory Usage**: System memory consumption
- **Docker**: Container count and status
- **Network**: Active connections

### ⚡ Activity Monitor
- Real-time processing indicators
- Command frequency tracking
- System uptime

## Keyboard Commands

| Key | Action |
|-----|--------|
| `G` | Show Graphiti details |
| `N` | Open Neo4j browser |
| `D` | Show Docker containers |
| `L` | View activity logs |
| `H` | Show help |
| `R` | Force refresh display |
| `Q` | Quit dashboard |

## File Structure

```
/Users/rudlord/Hero_dashboard/
├── hero                        # Quick launcher
├── launch_hero.sh             # Hero Core launcher with checks
├── hero_core.sh               # Main unified dashboard
├── dashboard_control.sh       # Master control for all dashboards
├── dashboard_diagnostics.sh   # System diagnostics tool
├── graphiti_monitor.py        # Neo4j/Graphiti stats collector
└── README.md                  # This file
```

## Configuration

Hero Core stores its data in:
- **Home**: `~/.hero_core/`
- **Logs**: `~/.hero_core/hero.log`
- **Cache**: `~/.hero_core/cache/`

## System Requirements

- **Neo4j**: For Graphiti knowledge graph
- **Redis**: For short-term memory
- **Docker**: For containerized services
- **Python 3**: For monitoring scripts

## Troubleshooting

### Check System Status
```bash
./dashboard_diagnostics.sh
```

### Stop All Dashboards
```bash
./dashboard_control.sh stop
```

### View Logs
```bash
tail -f ~/.hero_core/hero.log
```

## Advanced Usage

### Following the White Rabbit

When you need more detailed information:
1. Press `G` for Graphiti knowledge graph details
2. Press `N` to access Neo4j browser for graph exploration
3. Press `L` to view detailed activity logs

### Custom Monitoring

The `graphiti_monitor.py` script can be run independently:
```bash
python3 graphiti_monitor.py
```

## Notes

- Hero Core automatically stops other dashboard instances to prevent conflicts
- The dashboard refreshes every 3 seconds
- All metrics are collected in real-time
- The interface uses ANSI escape codes for smooth, flicker-free updates

---

**Created by Quantropy** | Hero Core v1.0