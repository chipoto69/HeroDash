#!/bin/bash

# Launch Hero Web Dashboard
# Comprehensive web interface for Hero agent monitoring and analytics

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$HOME/.hero_core/cache"
LOG_DIR="$HOME/.hero_core/logs"
PID_DIR="$HOME/.hero_core/pids"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
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
    echo "║                    HERO WEB DASHBOARD                         ║"
    echo "║                                                               ║"
    echo "║  Real-time Agent Analytics & Monitoring Interface            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required"
        exit 1
    fi
    
    # Check required Python packages
    local required_packages=("fastapi" "uvicorn" "jinja2")
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        error "Missing required packages: ${missing_packages[*]}"
        echo ""
        echo "Install with:"
        echo "  pip install ${missing_packages[*]}"
        echo ""
        echo "Or install all web dashboard dependencies:"
        echo "  pip install fastapi uvicorn jinja2 websockets"
        exit 1
    fi
    
    info "All dependencies satisfied"
}

# Create necessary directories
create_directories() {
    log "Creating directories..."
    mkdir -p "$CACHE_DIR" "$LOG_DIR" "$PID_DIR"
}

# Check if agents are running
check_agent_status() {
    log "Checking agent status..."
    
    if [[ -f "$PID_DIR/agent_runtime.pid" ]]; then
        local runtime_pid=$(cat "$PID_DIR/agent_runtime.pid")
        if kill -0 "$runtime_pid" 2>/dev/null; then
            info "✅ Agent runtime is running (PID: $runtime_pid)"
        else
            echo -e "${YELLOW}⚠️  Agent runtime is not running${NC}"
            echo "Start agents with: ./agents/launch_agents.sh start"
        fi
    else
        echo -e "${YELLOW}⚠️  No agent runtime found${NC}"
        echo "Start agents with: ./agents/launch_agents.sh start"
    fi
    
    # Check cache files
    local cache_files=("agent_runtime_status.json" "agent_coordination.json" "langsmith_stats.json")
    local missing_cache=()
    
    for cache_file in "${cache_files[@]}"; do
        if [[ ! -f "$CACHE_DIR/$cache_file" ]]; then
            missing_cache+=("$cache_file")
        fi
    done
    
    if [[ ${#missing_cache[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  Some cache files missing: ${missing_cache[*]}${NC}"
        echo "The dashboard will work but may show limited data"
    else
        info "✅ All cache files present"
    fi
}

# Start web dashboard
start_web_dashboard() {
    log "Starting Hero Web Dashboard..."
    
    # Set environment variables
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    # Check if port 8080 is available
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        error "Port 8080 is already in use"
        echo "Stop the existing service or use a different port"
        exit 1
    fi
    
    # Start dashboard in background
    cd "$SCRIPT_DIR"
    python3 web_dashboard.py > "$LOG_DIR/web_dashboard.log" 2>&1 &
    local dashboard_pid=$!
    echo $dashboard_pid > "$PID_DIR/web_dashboard.pid"
    
    # Wait for startup
    sleep 3
    
    if kill -0 $dashboard_pid 2>/dev/null; then
        info "✅ Web dashboard started successfully (PID: $dashboard_pid)"
        
        echo ""
        echo -e "${CYAN}🌐 Web Dashboard URLs:${NC}"
        echo "  Main Dashboard: http://localhost:8080"
        echo "  System Status:  http://localhost:8080/api/status"
        echo "  Agent Details:  http://localhost:8080/api/agents"
        echo "  Performance:    http://localhost:8080/api/performance"
        echo "  Analytics:      http://localhost:8080/api/analytics"
        echo ""
        echo -e "${GREEN}Dashboard is running with real-time WebSocket updates${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop or use './launch_web_dashboard.sh stop'${NC}"
        
        return 0
    else
        error "Failed to start web dashboard"
        echo "Check logs: $LOG_DIR/web_dashboard.log"
        return 1
    fi
}

# Stop web dashboard
stop_web_dashboard() {
    log "Stopping web dashboard..."
    
    if [[ -f "$PID_DIR/web_dashboard.pid" ]]; then
        local pid=$(cat "$PID_DIR/web_dashboard.pid")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid
            fi
            rm -f "$PID_DIR/web_dashboard.pid"
            info "✅ Web dashboard stopped"
        else
            echo -e "${YELLOW}Web dashboard was not running${NC}"
            rm -f "$PID_DIR/web_dashboard.pid"
        fi
    else
        echo -e "${YELLOW}No web dashboard PID file found${NC}"
    fi
}

# Show dashboard status
show_status() {
    echo -e "${CYAN}Web Dashboard Status:${NC}"
    
    if [[ -f "$PID_DIR/web_dashboard.pid" ]]; then
        local pid=$(cat "$PID_DIR/web_dashboard.pid")
        if kill -0 $pid 2>/dev/null; then
            echo "  ✅ Running (PID: $pid)"
            echo "  🌐 URL: http://localhost:8080"
            
            # Show recent log entries
            if [[ -f "$LOG_DIR/web_dashboard.log" ]]; then
                echo ""
                echo "Recent log entries:"
                tail -5 "$LOG_DIR/web_dashboard.log" | sed 's/^/    /'
            fi
        else
            echo "  ❌ Not running (stale PID file)"
            rm -f "$PID_DIR/web_dashboard.pid"
        fi
    else
        echo "  ❌ Not running"
    fi
}

# Start analytics monitor
start_analytics() {
    log "Starting analytics monitor..."
    
    if [[ -f "$PID_DIR/analytics_monitor.pid" ]]; then
        local existing_pid=$(cat "$PID_DIR/analytics_monitor.pid")
        if kill -0 $existing_pid 2>/dev/null; then
            info "Analytics monitor already running (PID: $existing_pid)"
            return 0
        fi
    fi
    
    python3 "$SCRIPT_DIR/monitors/analytics_dashboard.py" > "$LOG_DIR/analytics_monitor.log" 2>&1 &
    local analytics_pid=$!
    echo $analytics_pid > "$PID_DIR/analytics_monitor.pid"
    
    sleep 2
    if kill -0 $analytics_pid 2>/dev/null; then
        info "✅ Analytics monitor started (PID: $analytics_pid)"
    else
        error "Failed to start analytics monitor"
        rm -f "$PID_DIR/analytics_monitor.pid"
    fi
}

# Stop analytics monitor
stop_analytics() {
    log "Stopping analytics monitor..."
    
    if [[ -f "$PID_DIR/analytics_monitor.pid" ]]; then
        local pid=$(cat "$PID_DIR/analytics_monitor.pid")
        if kill -0 $pid 2>/dev/null; then
            kill -TERM $pid
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid
            fi
        fi
        rm -f "$PID_DIR/analytics_monitor.pid"
        info "✅ Analytics monitor stopped"
    fi
}

# Usage information
usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start web dashboard (default)"
    echo "  stop        Stop web dashboard"
    echo "  restart     Restart web dashboard"
    echo "  status      Show dashboard status"
    echo "  analytics   Start analytics monitor"
    echo "  full        Start dashboard + analytics + open browser"
    echo "  logs        Show recent logs"
    echo "  help        Show this help"
}

# Show logs
show_logs() {
    echo -e "${GREEN}Recent Web Dashboard Logs:${NC}"
    if [[ -f "$LOG_DIR/web_dashboard.log" ]]; then
        tail -20 "$LOG_DIR/web_dashboard.log"
    else
        echo "No web dashboard logs found"
    fi
    
    echo ""
    echo -e "${GREEN}Recent Analytics Logs:${NC}"
    if [[ -f "$LOG_DIR/analytics_monitor.log" ]]; then
        tail -10 "$LOG_DIR/analytics_monitor.log"
    else
        echo "No analytics logs found"
    fi
}

# Open browser (macOS only)
open_browser() {
    if command -v open &> /dev/null; then
        sleep 2
        open "http://localhost:8080"
        info "🌐 Opening dashboard in browser"
    fi
}

# Cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    stop_web_dashboard
    stop_analytics
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
            check_agent_status
            if start_web_dashboard; then
                # Keep script running in foreground
                echo ""
                echo -e "${GREEN}Web dashboard is running. Press Ctrl+C to stop.${NC}"
                wait
            fi
            ;;
        stop)
            stop_web_dashboard
            stop_analytics
            ;;
        restart)
            stop_web_dashboard
            stop_analytics
            sleep 2
            exec "$0" start
            ;;
        status)
            show_status
            ;;
        analytics)
            create_directories
            check_dependencies
            start_analytics
            ;;
        full)
            header
            create_directories
            check_dependencies
            check_agent_status
            start_analytics
            if start_web_dashboard; then
                open_browser
                echo ""
                echo -e "${GREEN}Full Hero dashboard stack running. Press Ctrl+C to stop.${NC}"
                wait
            fi
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