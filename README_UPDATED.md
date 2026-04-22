# HeroDash - Hero Core Command Centre

> Legacy readme. The reboot branch no longer uses this document as the source of truth.
> Use `README.md` for the real current dashboard contract.

```
    ██╗  ██╗███████╗██████╗  ██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██║  ██║██╔════╝██╔══██╗██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ███████║█████╗  ██████╔╝██║   ██║    ██║     ██║   ██║██████╔╝█████╗  
    ██╔══██║██╔══╝  ██╔══██╗██║   ██║    ██║     ██║   ██║██╔══██╗██╔══╝  
    ██║  ██║███████╗██║  ██║╚██████╔╝    ╚██████╗╚██████╔╝██║  ██║███████╗
    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
                                [ by Quantropy ]
```

## 🚀 Overview

Hero Core is a comprehensive terminal-based dashboard that provides real-time monitoring of AI systems, development tools, and system resources. It features a beautiful, flicker-free interface with lazy refresh capabilities for optimal performance.

![Terminal Dashboard](https://img.shields.io/badge/Terminal-Dashboard-blue)
![Version](https://img.shields.io/badge/Version-1.0-green)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey)

## 📚 Documentation

This repository contains both the original Hero Core Dashboard and an optimized, fixed version with significant performance improvements:

### Original Documentation
- [Technical Documentation](docs/DOCUMENTATION.md) - Complete technical details
- [User Guide](docs/USER_GUIDE.md) - Detailed usage instructions
- [Quick Reference](QUICK_REFERENCE.txt) - Command cheat sheet

### Optimized Version Documentation
- [Optimization Summary](docs/OPTIMIZED_VERSION_FIXED.md) - Details of all optimizations
- [Progress Log](docs/PROGRESS_LOG.md) - Complete history of improvements
- [Optimization Summary (Detailed)](OPTIMIZATION_SUMMARY_FIXED.md) - Technical breakdown
- [Optimized Version README](README_OPTIMIZED.md) - Usage instructions

### Key Improvements in Optimized Version
- **20-30% CPU Usage Reduction** through command caching
- **15-25% Faster Response Times** with intelligent caching
- **40-50% Fewer System Calls** by reducing redundant operations
- **Fixed Stability Issues** that caused immediate crashes
- **Enhanced Compatibility** with older bash versions

## ✨ Features

### 🤖 AI Systems Monitoring
- **Claude Code**: Active instances tracking with working directories
- **Token Usage**: Real-time Claude token consumption with visual progress bar
- **Qwen-code**: Runtime status monitoring
- **VS Code**: Helper process tracking

### 📊 GitHub Integration
- **21-Day Activity Graph**: Visual representation of your contributions
- **Contribution Stats**: Total contributions and current streak
- **Activity Levels**: Color-coded visualization

### 🧠 Knowledge Base Systems
- **Graphiti/Neo4j**: Temporal knowledge graph monitoring
- **Redis**: Key-value store metrics
- **Docker**: Container status and count
- **Archive Files**: JSON data file tracking

### 💻 System Metrics
- **CPU Usage**: Real-time percentage with visual bar
- **Memory Usage**: System memory consumption
- **Network**: Active connection monitoring

## 📦 Installation

### Prerequisites
- macOS (tested on Darwin 24.5.0)
- Python 3.x
- Bash 4.0+

### Optional Dependencies
- Redis
- Neo4j
- Docker
- Claude monitor (`ccm`)

### Quick Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HeroDash.git
cd HeroDash
```

2. Make scripts executable:
```bash
chmod +x hero launch_hero.sh hero_core.sh
chmod +x monitors/*.py utils/*.sh
```

3. Launch the dashboard:
```bash
./hero
```

## 🎮 Usage

### Launch Methods

```bash
# Quick start (original)
./hero

# With system checks (original)
./launch_hero.sh

# Direct execution (original)
./hero_core.sh

# Optimized version
./hero_optimized

# Optimized version with setup
./setup_optimized_fixed.sh
```

### Keyboard Commands

| Key | Action | Description |
|-----|--------|-------------|
| `T` | Refresh Tokens | Force update token/GitHub data |
| `G` | Graphiti Details | Show knowledge graph statistics |
| `N` | Neo4j Browser | Open http://localhost:7474 |
| `C` | Claude Monitor | Launch ccm tool |
| `H` | Help | Show command list |
| `R` | Refresh | Force full screen refresh |
| `Q` | Quit | Exit dashboard |

## 📁 Project Structure

```
HeroDash/
├── hero                      # Quick launcher
├── launch_hero.sh           # Launcher with system checks
├── hero_core.sh            # Main dashboard application
├── hero_core_optimized_fixed.sh # Optimized dashboard (recommended)
├── launch_hero_optimized_fixed.sh # Optimized launcher
├── hero_optimized          # Symlink to optimized launcher
├── monitors/               # Python monitoring scripts
│   ├── claude_usage_monitor.py
│   ├── github_activity_monitor.py
│   └── graphiti_monitor.py
├── utils/                  # Utility scripts
│   ├── dashboard_control.sh
│   └── dashboard_diagnostics.sh
└── docs/                   # Documentation
    ├── DOCUMENTATION.md    # Technical documentation
    ├── USER_GUIDE.md       # User guide
    ├── OPTIMIZED_VERSION_FIXED.md # Optimized version docs
    └── PROGRESS_LOG.md     # Development progress log
```

## 🔧 Configuration

Hero Core stores its configuration and cache in:
```
~/.hero_core/
├── hero.log              # Activity log
└── cache/                # Data cache
    ├── claude_usage.json
    ├── github_activity.json
    └── graphiti_stats.json
```

### Refresh Rates
- **Fast Updates** (3 seconds): AI systems, system metrics
- **Lazy Updates** (30 seconds): Token usage, GitHub activity

## 🛠️ Utilities

### System Diagnostics
```bash
./utils/dashboard_diagnostics.sh
```

### Dashboard Control
```bash
# Stop all dashboards
./utils/dashboard_control.sh stop

# Check status
./utils/dashboard_control.sh status
```

## 📈 Performance

- **CPU Usage**: ~0.1-0.5% idle, ~1-2% during updates (optimized version 20-30% lower)
- **Memory**: ~10-15 MB for bash, ~30 MB per Python monitor
- **Update Method**: Cursor-based rendering (no screen flicker)
- **Data Collection**: Asynchronous Python monitors with JSON caching

## 🔍 Troubleshooting

### Common Issues

1. **"Loading token data..."** - Press `T` to force refresh
2. **Screen flickers** - Ensure terminal supports ANSI escape codes
3. **High CPU usage** - Increase `REFRESH_RATE` in hero_core.sh

### View Logs
```bash
tail -f ~/.hero_core/hero.log
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Credits

Created by **Quantropy**

### Technologies Used
- Bash scripting with ANSI escape codes
- Python for data collection
- JSON for inter-process communication
- Terminal-based UI rendering

## 🌟 Features Roadmap

- [ ] Real GitHub API integration
- [ ] Claude API integration
- [ ] Historical data persistence
- [ ] Multi-platform support (Linux, Windows)
- [ ] WebSocket real-time updates
- [ ] Custom alert thresholds
- [ ] Theme customization

---

**Hero Core v1.0** | Terminal Dashboard Excellence