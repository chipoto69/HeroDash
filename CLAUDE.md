# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Hero Core Command Centre - AI Agent Collaboration Framework

## Project Overview

The Hero Core Command Centre is a comprehensive terminal-based dashboard that provides real-time monitoring of AI systems, development tools, and system resources. It integrates with the Frontline/Chimera AI agent collaboration framework to create a unified command centre for managing multiple AI agents working together.

## Architecture

### Core Components

1. **Hero Dashboard (Terminal UI)**
   - Main optimized dashboard: `hero_core_optimized_fixed.sh`
   - Launcher script: `launch_hero_optimized_fixed.sh`
   - Setup script: `setup_optimized_fixed.sh`

2. **Monitoring System**
   - Python monitors in `monitors/` directory
   - JSON cache system under `~/.hero_core/cache/`
   - Real-time data collection and visualization

3. **AI Agent Integration**
   - LangSmith/LangChain tracing for observability
   - NATS messaging for agent communication
   - Multi-agent coordination and task delegation

4. **Knowledge Systems**
   - Graphiti temporal knowledge graphs
   - Neo4j hypergraph integration
   - ChromaDB for embeddings and search

### Technology Stack

- **Backend**: Python 3.8+ with asyncio
- **Frontend**: Terminal-based with ANSI colors and real-time updates
- **Messaging**: NATS JetStream for agent communication
- **Observability**: LangSmith + LangGraph for workflow tracing
- **Knowledge**: ChromaDB, Neo4j, Graphiti for knowledge management
- **Platform**: Optimized for macOS (compatible with Linux)

## Common Development Tasks

### Setup and Installation

```bash
# Initial setup (run once)
./setup_optimized_fixed.sh

# Install dependencies
pip install langsmith langchain langgraph psutil
brew install jq  # For JSON processing optimization
```

### Running the Dashboard

```bash
# Launch optimized dashboard
./hero_optimized

# Or directly
./launch_hero_optimized_fixed.sh

# Run individual monitors
python3 monitors/claude_usage_monitor_optimized.py
python3 monitors/agents_monitor.py
python3 monitors/langsmith_tracer.py
```

### Development Commands

```bash
# Lint shell scripts
shellcheck hero_core_optimized_fixed.sh launch_hero_optimized_fixed.sh

# Lint Python code
flake8 monitors/*.py

# Format Python code
black monitors/*.py

# Run tests (when implemented)
pytest tests/
```

### Agent Integration Commands

```bash
# Start Chimera agent framework (requires frontline setup)
cd /Users/rudlord/q3/frontline
make nats-up && make nats-bootstrap
make run-langgraph

# Monitor agent activities
python3 monitors/agent_coordinator.py
python3 monitors/chimera_bridge.py
```

## High-Level Architecture

### Agent Collaboration Framework

```
┌─────────────────────────────────────────────────────────────┐
│                    LangSmith Studio (Observability)         │
└─────────────────────────────────────────────────────────────┘
                              ↑
                         LangGraph Tracing
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Hero Command Centre Dashboard                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Agent       │  │  Performance │  │  Knowledge   │     │
│  │  Monitor     │  │  Metrics     │  │  Graph       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    NATS JetStream Bus                       │
│ Streams: Tasks, Results, Events, Control | KV Store | OS    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  UI Agent   │ Embedder  │ Retriever │ Memory  │ Orchestrator│
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Patterns

1. **Agent Registration**: Agents register with coordinator through NATS
2. **Task Distribution**: Coordinator assigns tasks based on agent capabilities
3. **Execution Tracking**: LangSmith traces all agent interactions
4. **Knowledge Sharing**: Agents share insights through knowledge graph
5. **Performance Monitoring**: Real-time metrics in Hero dashboard

### Key Integration Points

- **NATS Subjects**: `hero.v1.{env}.agents.{action}` for Hero-specific messages
- **LangSmith Projects**: `hero-command-centre` for unified tracing
- **Cache System**: JSON files in `~/.hero_core/cache/` for state persistence
- **Knowledge APIs**: REST endpoints for cross-agent data sharing

## File Structure and Conventions

### Core Scripts
- `hero_core_optimized_fixed.sh` - Main dashboard with AI agent sections
- `launch_hero_optimized_fixed.sh` - Launcher with environment setup
- `setup_optimized_fixed.sh` - One-time setup and dependency checking

### Monitor Modules
- `monitors/langsmith_tracer.py` - LangSmith integration and tracing
- `monitors/agent_coordinator.py` - Multi-agent task coordination
- `monitors/chimera_bridge.py` - Bridge to Chimera framework
- `monitors/agents_monitor.py` - AI agent process monitoring
- `monitors/*_monitor_optimized.py` - Optimized monitoring modules

### Configuration
- Environment variables: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`
- Cache directory: `~/.hero_core/cache/`
- Log files: `~/.hero_core/hero.log`
- NATS configuration: Inherited from Chimera setup

## Coding Conventions

### Bash Scripts
- Use safe patterns: quote variables, prefer `$(...)` over backticks
- Implement caching for expensive operations
- Follow existing color and formatting patterns
- Use functions for reusable code blocks

### Python Modules
- Follow PEP 8: 4-space indentation, meaningful names
- Use type hints for function signatures
- Implement proper error handling and logging
- Use `@traceable` decorator for LangSmith integration
- Keep modules single-responsibility

### JSON Data Formats
- Use consistent timestamp formats (ISO 8601)
- Include metadata for tracing (correlation_id, agent_name)
- Implement atomic writes with temporary files
- Validate JSON structure before writing

## Performance Optimizations

### Caching Strategy
- Command output caching with TTL
- JSON file-based cache for compatibility
- Lazy refresh for expensive operations
- Memory-efficient data structures

### Agent Communication
- Asynchronous NATS messaging
- Correlation ID tracking
- Circuit breaker patterns
- Batch processing for bulk operations

## Testing Guidelines

### Manual Testing
```bash
# Smoke test - verify dashboard launches
./launch_hero_optimized_fixed.sh

# Monitor test - verify JSON output
python3 monitors/agents_monitor.py
cat ~/.hero_core/cache/agents_status.json

# Agent integration test
python3 monitors/chimera_bridge.py --test
```

### Automated Testing (Future)
- Unit tests for monitor modules
- Integration tests for agent communication
- Performance benchmarks for dashboard rendering
- End-to-end tests for complete workflows

## Security Considerations

### API Keys and Secrets
- Store LangSmith API key in environment variables
- Never commit secrets to repository
- Use local config files ignored by git
- Implement proper credential rotation

### Agent Communication
- Use TLS for NATS connections
- Implement proper authentication
- Validate all incoming messages
- Rate limiting for agent requests

## Troubleshooting

### Common Issues
- **Dashboard crash**: Check bash version compatibility (`bash --version`)
- **Missing data**: Verify monitor scripts are executable
- **Agent connection**: Check NATS server status
- **Performance**: Enable command caching, install `jq`

### Debug Commands
```bash
# Check monitor outputs
ls -la ~/.hero_core/cache/

# Verify NATS connection
nats stream ls

# Check LangSmith traces
export LANGSMITH_TRACING=true
python3 monitors/langsmith_tracer.py --debug
```

## Integration with Frontline/Chimera

The Hero Dashboard integrates with the existing Frontline/Chimera codebase located at `/Users/rudlord/q3/frontline/`. Key integration points:

- **NATS Messaging**: Uses existing NATS infrastructure
- **LangGraph Workflows**: Extends existing workflow patterns
- **Knowledge Systems**: Connects to ChromaDB and Neo4j
- **Agent Framework**: Leverages existing agent architecture

Ensure the Frontline environment is properly set up before running agent integration features.

## Future Enhancements

### Planned Features
- Real-time 3D visualization of agent interactions
- Machine learning for optimal task distribution
- Plugin architecture for custom monitors
- WebSocket interface for remote monitoring
- Historical analytics and reporting

### Extensibility
- Monitor plugin system
- Custom agent implementations
- Configurable dashboard layouts
- External API integrations