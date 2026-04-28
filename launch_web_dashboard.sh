#!/bin/bash

# Launch Hero Web Dashboard
# Honest operator interface for Hermes agents, Factory Droids, memory, workflows, and alerts

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$HOME/.hero_core/cache"
LOG_DIR="$HOME/.hero_core/logs"
PID_DIR="$HOME/.hero_core/pids"
HERO_WORKFLOWS_ROOT="${HERO_WORKFLOWS_ROOT:-$HOME/ORGANIZED/ACTIVE_PROJECTS/ARSENAL/WORKFLOWS}"
HERO_BRAIN_ROOT="${HERO_BRAIN_ROOT:-$HOME/brain}"
HERO_HERMES_CONFIG="${HERO_HERMES_CONFIG:-$HOME/.hermes/config.yaml}"
HERO_TELEGRAM_CANON="${HERO_TELEGRAM_CANON:-$HOME/wiki/queries/grok420system.md}"
HERO_DASHBOARD_PORT="${HERO_DASHBOARD_PORT:-${PORT:-8080}}"
if ! [[ "$HERO_DASHBOARD_PORT" =~ ^[0-9]+$ ]]; then
    echo -e "\033[1;33m[WARN]\033[0m HERO_DASHBOARD_PORT='$HERO_DASHBOARD_PORT' is not numeric; falling back to 8080"
    HERO_DASHBOARD_PORT=8080
fi

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
    echo "║  Honest operator surface for Hermes / Telegram / GBrain     ║"
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
    local required_packages=("fastapi" "uvicorn" "jinja2" "pyyaml")
    local missing_packages=()

    for package in "${required_packages[@]}"; do
        # Special case: pyyaml imports as yaml
        local import_name="$package"
        if [[ "$package" == "pyyaml" ]]; then
            import_name="yaml"
        fi
        if ! python3 -c "import $import_name" 2>/dev/null; then
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
        echo "  pip install fastapi uvicorn jinja2 'pyyaml>=6.0.0'"
        exit 1
    fi
    
    info "All dependencies satisfied"
}

# Create necessary directories
create_directories() {
    log "Creating directories..."
    mkdir -p "$CACHE_DIR" "$LOG_DIR" "$PID_DIR"
}

# Check reboot inputs
check_agent_status() {
    log "Checking reboot inputs..."

    local hermes_config="$HERO_HERMES_CONFIG"
    local workflows_root="$HERO_WORKFLOWS_ROOT"
    local brain_root="$HERO_BRAIN_ROOT"

    if [[ -f "$hermes_config" ]]; then
        info "[OK] Hermes config present"
    else
        echo -e "${YELLOW}[WARN] Hermes config missing${NC}"
    fi

    if [[ -d "$workflows_root" ]]; then
        info "[OK] WORKFLOWS repo present"
    else
        echo -e "${YELLOW}[WARN] WORKFLOWS repo missing${NC}"
    fi

    if [[ -d "$brain_root" ]]; then
        info "[OK] Brain repo present"
    else
        echo -e "${YELLOW}[WARN] Brain repo missing${NC}"
    fi

    if pgrep -fal 'hermes' >/dev/null 2>&1; then
        info "[OK] Hermes process activity detected"
    else
        echo -e "${YELLOW}[WARN] No Hermes process detected${NC}"
    fi

    if command -v droid >/dev/null 2>&1 || [[ -x "$HOME/.local/bin/droid" ]]; then
        info "[OK] Droid binary present"
    else
        echo -e "${YELLOW}[WARN] Droid binary missing${NC}"
    fi
}

pid_matches_dashboard() {
    local pid="$1"
    [[ -n "$pid" ]] || return 1
    local cmd
    cmd=$(ps -p "$pid" -o args= 2>/dev/null) || return 1
    # Check for exact match of the dashboard command
    [[ "$cmd" == *"web_dashboard.py"* ]] || return 1
    return 0
}

# Start web dashboard
start_web_dashboard() {
    log "Starting Hero Web Dashboard..."
    
    # Set environment variables
    export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
    export HERO_WORKFLOWS_ROOT HERO_BRAIN_ROOT HERO_HERMES_CONFIG HERO_TELEGRAM_CANON HERO_DASHBOARD_PORT
    
    # Check if dashboard port is available
    if lsof -Pi :"$HERO_DASHBOARD_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
        error "Port $HERO_DASHBOARD_PORT is already in use"
        echo "Stop the existing service or use a different port"
        return 1
    fi
    
    # Start dashboard in background
    cd "$SCRIPT_DIR"
    python3 web_dashboard.py > "$LOG_DIR/web_dashboard.log" 2>&1 &
    local dashboard_pid=$!
    echo $dashboard_pid > "$PID_DIR/web_dashboard.pid"
    
    # Wait for startup
    sleep 3
    
    if kill -0 $dashboard_pid 2>/dev/null; then
        info "[OK] Web dashboard started successfully (PID: $dashboard_pid)"
        
        echo ""
        echo -e "${CYAN}Web Dashboard URLs:${NC}"
        echo "  Main Dashboard: http://localhost:$HERO_DASHBOARD_PORT"
        echo "  Status JSON:    http://localhost:$HERO_DASHBOARD_PORT/api/status"
        echo "  Labyrinth JSON: http://localhost:$HERO_DASHBOARD_PORT/api/labyrinth"
        echo "  Actions JSON:   http://localhost:$HERO_DASHBOARD_PORT/api/actions"
        echo "  Health Check:   http://localhost:$HERO_DASHBOARD_PORT/api/healthz"
        echo "  Readiness:      http://localhost:$HERO_DASHBOARD_PORT/api/readiness"
        echo ""
        echo -e "${GREEN}Dashboard is running with honest subsystem probes${NC}"
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
        # Validate PID is a plain unsigned integer
        if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
            error "Invalid PID in pidfile: '$pid'"
            rm -f "$PID_DIR/web_dashboard.pid"
            return 1
        fi
        if kill -0 "$pid" 2>/dev/null && pid_matches_dashboard "$pid"; then
            kill -TERM "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid"
            fi
            rm -f "$PID_DIR/web_dashboard.pid"
            info "[OK] Web dashboard stopped"
        elif kill -0 "$pid" 2>/dev/null; then
            error "PID file points to a non-dashboard process ($pid); refusing to kill it"
            return 1
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
        # Validate PID is a plain unsigned integer
        if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
            echo "  [ERROR] Invalid PID in pidfile: '$pid'"
            rm -f "$PID_DIR/web_dashboard.pid"
            return
        fi
        if kill -0 "$pid" 2>/dev/null && pid_matches_dashboard "$pid"; then
            echo "  [OK] Running (PID: $pid)"
            echo "  URL: http://localhost:$HERO_DASHBOARD_PORT"

            # Show recent log entries
            if [[ -f "$LOG_DIR/web_dashboard.log" ]]; then
                echo ""
                echo "Recent log entries:"
                tail -5 "$LOG_DIR/web_dashboard.log" | sed 's/^/    /'
            fi
        elif kill -0 "$pid" 2>/dev/null; then
            echo "  [WARN] PID file points to a different live process ($pid)"
        else
            echo "  [DOWN] Not running (stale PID file)"
            rm -f "$PID_DIR/web_dashboard.pid"
        fi
    else
        echo "  [DOWN] Not running"
    fi
}

# Start analytics monitor
start_analytics() {
    log "Starting analytics monitor..."
    
    if [[ -f "$PID_DIR/analytics_monitor.pid" ]]; then
        local existing_pid=$(cat "$PID_DIR/analytics_monitor.pid")
        if kill -0 "$existing_pid" 2>/dev/null; then
            # Verify process command-line matches analytics monitor
            local cmd
            cmd=$(ps -p "$existing_pid" -o args= 2>/dev/null) || cmd=""
            if [[ "$cmd" == *"analytics_dashboard.py"* ]] || [[ "$cmd" == *"analytics_monitor"* ]]; then
                info "Analytics monitor already running (PID: $existing_pid)"
                return 0
            else
                # Stale pidfile pointing to different process
                rm -f "$PID_DIR/analytics_monitor.pid"
            fi
        else
            # Process no longer exists, remove stale pidfile
            rm -f "$PID_DIR/analytics_monitor.pid"
        fi
    fi
    
    python3 "$SCRIPT_DIR/monitors/analytics_dashboard.py" > "$LOG_DIR/analytics_monitor.log" 2>&1 &
    local analytics_pid=$!
    echo $analytics_pid > "$PID_DIR/analytics_monitor.pid"
    
    sleep 2
    if kill -0 $analytics_pid 2>/dev/null; then
        info "[OK] Analytics monitor started (PID: $analytics_pid)"
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
        # Validate PID is a plain unsigned integer
        if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
            error "Invalid PID in analytics pidfile: '$pid'"
            rm -f "$PID_DIR/analytics_monitor.pid"
            return 1
        fi
        if kill -0 "$pid" 2>/dev/null; then
            # Validate that PID belongs to analytics_monitor process
            local cmd
            cmd=$(ps -p "$pid" -o args= 2>/dev/null) || cmd=""
            if [[ "$cmd" == *"analytics_dashboard.py"* ]] || [[ "$cmd" == *"analytics_monitor"* ]]; then
                kill -TERM "$pid"
                sleep 2
                if kill -0 "$pid" 2>/dev/null; then
                    kill -KILL "$pid"
                fi
                rm -f "$PID_DIR/analytics_monitor.pid"
                info "[OK] Analytics monitor stopped"
            else
                error "PID file points to a non-analytics process ($pid); refusing to kill it"
                return 1
            fi
        else
            rm -f "$PID_DIR/analytics_monitor.pid"
            info "[OK] Analytics monitor stopped (stale PID)"
        fi
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
        open "http://localhost:$HERO_DASHBOARD_PORT"
        info "Opening dashboard in browser"
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
