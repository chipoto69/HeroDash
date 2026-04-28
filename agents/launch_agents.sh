#!/bin/bash

# Agent Launcher Script for Hero Command Centre
# Starts agent runtime system and integrates with Hero Dashboard

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERO_DIR="$(dirname "$SCRIPT_DIR")"
CACHE_DIR="$HOME/.hero_core/cache"
LOG_DIR="$HOME/.hero_core/logs"
PID_DIR="$HOME/.hero_core/pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

header() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                    HERO AGENT LAUNCHER                        ║"
    echo "║                                                               ║"
    echo "║  Starting AI Agent Runtime for Hero Command Centre           ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    mkdir -p "$CACHE_DIR" "$LOG_DIR" "$PID_DIR"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check required Python packages
    local required_packages=("asyncio" "yaml" "nats")
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            warn "Python package '$package' not found - some features may be limited"
        fi
    done
    
    # Check if Hero monitors are available
    if [[ ! -f "$HERO_DIR/monitors/agent_coordinator.py" ]]; then
        error "Hero monitors not found - ensure you're in the Hero Dashboard directory"
        exit 1
    fi
    
    info "Dependencies check completed"
}

# Check NATS server
check_nats() {
    log "Checking NATS server..."
    
    local nats_url="${NATS_URL:-nats://localhost:4222}"
    
    # Try to connect to NATS
    if command -v nats &> /dev/null; then
        if nats account info --server="$nats_url" &>/dev/null; then
            info "NATS server is running at $nats_url"
            return 0
        fi
    fi
    
    # Check if we can start NATS locally
    if command -v nats-server &> /dev/null; then
        warn "NATS server not running - starting local instance..."
        start_nats_server
    else
        warn "NATS server not available - agents will run in standalone mode"
        export NATS_STANDALONE=1
    fi
}

# Start local NATS server
start_nats_server() {
    log "Starting local NATS server..."
    
    local nats_config="$CACHE_DIR/nats-server.conf"
    
    # Create NATS configuration
    cat > "$nats_config" << EOF
# NATS Server Configuration for Hero Agents
port: 4222
http_port: 8222

# JetStream Configuration
jetstream {
    store_dir: "$CACHE_DIR/nats"
    max_memory_store: 256MB
    max_file_store: 2GB
}

# Logging
log_file: "$LOG_DIR/nats-server.log"
logtime: true
debug: false
trace: false

# Limits
max_payload: 1MB
max_connections: 64K
max_subscriptions: 0
max_control_line: 4KB
EOF

    # Start NATS server in background
    nats-server -c "$nats_config" &
    local nats_pid=$!
    echo $nats_pid > "$PID_DIR/nats-server.pid"
    
    # Wait for NATS to start
    sleep 2
    
    if kill -0 $nats_pid 2>/dev/null; then
        info "NATS server started with PID $nats_pid"
        
        # Initialize JetStream streams
        sleep 1
        initialize_nats_streams
    else
        error "Failed to start NATS server"
        exit 1
    fi
}

# Initialize NATS streams
initialize_nats_streams() {
    log "Initializing NATS streams..."
    
    if command -v nats &> /dev/null; then
        # Create Hero agent streams
        nats stream add hero_tasks \
            --subjects="hero.v1.*.orchestrator.tasks.>" \
            --storage=file \
            --retention=workqueue \
            --max-msgs=10000 \
            --max-age=24h \
            2>/dev/null || warn "Failed to create hero_tasks stream"
        
        nats stream add hero_events \
            --subjects="hero.v1.*.agents.>,hero.v1.*.monitors.>" \
            --storage=file \
            --retention=limits \
            --max-msgs=50000 \
            --max-age=7d \
            2>/dev/null || warn "Failed to create hero_events stream"
        
        nats stream add hero_knowledge \
            --subjects="hero.v1.*.knowledge.>" \
            --storage=file \
            --retention=limits \
            --max-msgs=100000 \
            --max-age=30d \
            2>/dev/null || warn "Failed to create hero_knowledge stream"
        
        info "NATS streams initialized"
    else
        warn "NATS CLI not available - streams not initialized"
    fi
}

# Start agent runtime
start_agent_runtime() {
    log "Starting Agent Runtime System..."
    
    # Set environment variables
    export PYTHONPATH="$HERO_DIR:$SCRIPT_DIR:$PYTHONPATH"
    export HERO_CACHE_DIR="$CACHE_DIR"
    export HERO_LOG_DIR="$LOG_DIR"
    
    # Configure LLM providers if available
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
        info "Anthropic Claude configured"
    fi
    
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        info "OpenAI configured"
    fi
    
    if [[ -z "${ANTHROPIC_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
        warn "No LLM API keys configured - using mock provider"
        info "Set ANTHROPIC_API_KEY or OPENAI_API_KEY for real LLM integration"
    fi
    
    # Start agent runtime
    python3 "$SCRIPT_DIR/agent_runtime.py" \
        --agents task_orchestrator knowledge_integration \
        > "$LOG_DIR/agent_runtime.log" 2>&1 &
    
    local runtime_pid=$!
    echo $runtime_pid > "$PID_DIR/agent_runtime.pid"
    
    # Wait a moment and check if it started successfully
    sleep 3
    
    if kill -0 $runtime_pid 2>/dev/null; then
        info "Agent Runtime started with PID $runtime_pid"
        return 0
    else
        error "Failed to start Agent Runtime - check logs: $LOG_DIR/agent_runtime.log"
        return 1
    fi
}

# Start Hero monitors
start_hero_monitors() {
    log "Starting Hero monitoring processes..."
    
    # Start agent coordinator if not already running
    if [[ ! -f "$PID_DIR/agent_coordinator.pid" ]]; then
        python3 "$HERO_DIR/monitors/agent_coordinator.py" > "$LOG_DIR/agent_coordinator.log" 2>&1 &
        echo $! > "$PID_DIR/agent_coordinator.pid"
        info "Agent Coordinator started"
    fi
    
    # Start langsmith tracer
    if [[ ! -f "$PID_DIR/langsmith_tracer.pid" ]]; then
        python3 "$HERO_DIR/monitors/langsmith_tracer.py" > "$LOG_DIR/langsmith_tracer.log" 2>&1 &
        echo $! > "$PID_DIR/langsmith_tracer.pid"
        info "LangSmith Tracer started"
    fi
    
    # Start chimera bridge
    if [[ ! -f "$PID_DIR/chimera_bridge.pid" ]]; then
        python3 "$HERO_DIR/monitors/chimera_bridge.py" --sync > "$LOG_DIR/chimera_bridge.log" 2>&1 &
        echo $! > "$PID_DIR/chimera_bridge.pid"
        info "Chimera Bridge started"
    fi
}

# Verify agent status
verify_agents() {
    log "Verifying agent status..."
    
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if [[ -f "$CACHE_DIR/agent_runtime_status.json" ]]; then
            local agent_count=$(python3 -c "
import json
try:
    with open('$CACHE_DIR/agent_runtime_status.json') as f:
        data = json.load(f)
    print(len(data.get('agents', {})))
except:
    print(0)
")
            
            if [[ $agent_count -gt 0 ]]; then
                info "✅ $agent_count agents are active and ready"
                
                # Show agent details
                python3 -c "
import json
try:
    with open('$CACHE_DIR/agent_runtime_status.json') as f:
        data = json.load(f)
    for agent_id, agent in data.get('agents', {}).items():
        print(f'  🤖 {agent[\"agent_type\"]} - {agent[\"status\"]}')
except:
    pass
"
                return 0
            fi
        fi
        
        info "Waiting for agents to initialize... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    warn "Agents may still be starting - check logs for details"
    return 1
}

# Show status dashboard
show_status() {
    echo
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                        AGENT STATUS                           ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    
    # Show running processes
    echo -e "${GREEN}Running Processes:${NC}"
    
    if [[ -f "$PID_DIR/nats-server.pid" ]] && kill -0 $(cat "$PID_DIR/nats-server.pid") 2>/dev/null; then
        echo "  ✅ NATS Server (PID: $(cat "$PID_DIR/nats-server.pid"))"
    fi
    
    if [[ -f "$PID_DIR/agent_runtime.pid" ]] && kill -0 $(cat "$PID_DIR/agent_runtime.pid") 2>/dev/null; then
        echo "  ✅ Agent Runtime (PID: $(cat "$PID_DIR/agent_runtime.pid"))"
    fi
    
    if [[ -f "$PID_DIR/agent_coordinator.pid" ]] && kill -0 $(cat "$PID_DIR/agent_coordinator.pid") 2>/dev/null; then
        echo "  ✅ Agent Coordinator (PID: $(cat "$PID_DIR/agent_coordinator.pid"))"
    fi
    
    # Show cache files
    echo -e "${GREEN}Cache Files:${NC}"
    if [[ -f "$CACHE_DIR/agent_runtime_status.json" ]]; then
        echo "  📊 Runtime Status: $CACHE_DIR/agent_runtime_status.json"
    fi
    
    if [[ -f "$CACHE_DIR/agent_coordination.json" ]]; then
        echo "  🎯 Coordination Data: $CACHE_DIR/agent_coordination.json"
    fi
    
    # Show log files
    echo -e "${GREEN}Log Files:${NC}"
    echo "  📝 Agent Runtime: $LOG_DIR/agent_runtime.log"
    echo "  📝 Agent Coordinator: $LOG_DIR/agent_coordinator.log"
    
    if [[ -f "$LOG_DIR/nats-server.log" ]]; then
        echo "  📝 NATS Server: $LOG_DIR/nats-server.log"
    fi
}

# Stop all processes
stop_agents() {
    log "Stopping all agent processes..."
    
    # Stop agent runtime
    if [[ -f "$PID_DIR/agent_runtime.pid" ]]; then
        local pid=$(cat "$PID_DIR/agent_runtime.pid")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid
            sleep 2
            kill -0 $pid 2>/dev/null && kill -KILL $pid
        fi
        rm -f "$PID_DIR/agent_runtime.pid"
        info "Agent Runtime stopped"
    fi
    
    # Stop Hero monitors
    for service in agent_coordinator langsmith_tracer chimera_bridge; do
        if [[ -f "$PID_DIR/${service}.pid" ]]; then
            local pid=$(cat "$PID_DIR/${service}.pid")
            if kill -0 $pid 2>/dev/null; then
                kill -TERM $pid
            fi
            rm -f "$PID_DIR/${service}.pid"
        fi
    done
    
    # Stop NATS server
    if [[ -f "$PID_DIR/nats-server.pid" ]]; then
        local pid=$(cat "$PID_DIR/nats-server.pid")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid
        fi
        rm -f "$PID_DIR/nats-server.pid"
        info "NATS Server stopped"
    fi
    
    log "All agent processes stopped"
}

# Test agent functionality
test_agents() {
    log "Testing agent functionality..."
    
    # Run integration test
    python3 "$SCRIPT_DIR/test_agent_integration.py" --test integration
    
    # Test LLM bridge
    if python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from llm_bridge import get_llm_bridge; print('LLM Bridge OK')" 2>/dev/null; then
        info "LLM Bridge test passed"
    else
        warn "LLM Bridge test failed"
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start      Start all agent services (default)"
    echo "  stop       Stop all agent services"
    echo "  restart    Restart all agent services"
    echo "  status     Show current status"
    echo "  test       Run agent tests"
    echo "  logs       Show recent log entries"
    echo "  help       Show this help message"
    echo
    echo "Environment Variables:"
    echo "  ANTHROPIC_API_KEY    API key for Claude"
    echo "  OPENAI_API_KEY       API key for OpenAI"
    echo "  NATS_URL            NATS server URL (default: nats://localhost:4222)"
    echo
}

# Show logs
show_logs() {
    echo -e "${GREEN}Recent Agent Runtime Logs:${NC}"
    if [[ -f "$LOG_DIR/agent_runtime.log" ]]; then
        tail -20 "$LOG_DIR/agent_runtime.log"
    else
        echo "No agent runtime logs found"
    fi
    
    echo
    echo -e "${GREEN}Recent Agent Coordinator Logs:${NC}"
    if [[ -f "$LOG_DIR/agent_coordinator.log" ]]; then
        tail -10 "$LOG_DIR/agent_coordinator.log"
    else
        echo "No agent coordinator logs found"
    fi
}

# Trap signals for cleanup
cleanup() {
    echo
    warn "Received interrupt signal - stopping agents..."
    stop_agents
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main execution
main() {
    local command="${1:-start}"
    
    case "$command" in
        start)
            header
            create_directories
            check_dependencies
            check_nats
            start_hero_monitors
            
            if start_agent_runtime; then
                verify_agents
                show_status
                echo
                info "🚀 Agent system is ready! Use './launch_hero_optimized_fixed.sh' to view in Hero Dashboard"
                echo
                info "📚 Next steps:"
                echo "   1. Start Hero Dashboard: ./launch_hero_optimized_fixed.sh"
                echo "   2. View agent status in the dashboard"
                echo "   3. Test workflows: python3 agents/example_workflows.py"
                echo "   4. View logs: $0 logs"
            else
                error "Failed to start agent system"
                exit 1
            fi
            ;;
        stop)
            stop_agents
            ;;
        restart)
            stop_agents
            sleep 2
            exec "$0" start
            ;;
        status)
            show_status
            ;;
        test)
            test_agents
            ;;
        logs)
            show_logs
            ;;
        help)
            usage
            ;;
        *)
            error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"