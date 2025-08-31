#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# HERO CORE ENHANCED - Unified Command Centre with Token Usage & GitHub Activity
# The definitive dashboard for all systems monitoring
# ═══════════════════════════════════════════════════════════════════════════════

# Enhanced Color Palette
CYAN='\033[38;2;93;173;226m'
CYAN_BRIGHT='\033[38;2;127;199;239m'
BLUE='\033[38;2;52;152;219m'
GREEN='\033[38;2;46;204;113m'
YELLOW='\033[38;2;241;196;15m'
ORANGE='\033[38;2;230;126;34m'
RED='\033[38;2;231;76;60m'
PURPLE='\033[38;2;155;89;182m'
MAGENTA='\033[38;2;199;125;255m'
PINK='\033[38;2;255;105;180m'
WHITE='\033[38;5;255m'
GRAY='\033[38;5;245m'
DARK='\033[38;5;238m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Configuration
HERO_HOME="$HOME/.hero_core"
HERO_LOG="$HERO_HOME/hero.log"
HERO_CACHE="$HERO_HOME/cache"
GRAPHITI_STATS="$HERO_CACHE/graphiti_stats.json"
CLAUDE_USAGE="$HERO_CACHE/claude_usage.json"
TOKEN_ANALYSIS="$HERO_CACHE/token_analysis.json"
GITHUB_ACTIVITY="$HERO_CACHE/github_activity.json"
AGENTS_STATUS="$HERO_CACHE/agents_status.json"
CODE_ACTIVITY="$HERO_CACHE/code_activity.json"
LANGSMITH_STATS="$HERO_CACHE/langsmith_stats.json"
AGENT_COORDINATION="$HERO_CACHE/agent_coordination.json"
CHIMERA_INTEGRATION="$HERO_CACHE/chimera_integration.json"
LOCK_FILE="$HERO_HOME/hero.pid"
REFRESH_RATE=3
LAZY_REFRESH_COUNTER=0
LAZY_REFRESH_INTERVAL=10  # Refresh token data every 10 cycles (30 seconds)

# Project Paths (configurable via environment variables)
CHIMERA_BASE="${CHIMERA_BASE:-/Users/rudlord/q3/Frontline}"
GRAPHITI_BASE="${GRAPHITI_BASE:-/Users/rudlord/q3/0_MEMORY/graphiti}"

# Cache for system commands (using regular arrays as fallback for older bash)
CMD_CACHE=()
CMD_CACHE_TIME=()

# Terminal control
clear_to_eol() { [ -t 1 ] && echo -ne "\033[K"; }
move_cursor() { [ -t 1 ] && echo -ne "\033[${1};${2}H"; }
hide_cursor() { [ -t 1 ] && tput civis 2>/dev/null || true; }
show_cursor() { [ -t 1 ] && tput cnorm 2>/dev/null || true; }

# Get terminal size
get_term_size() {
    TERM_WIDTH=$(tput cols 2>/dev/null || echo 140)
    TERM_HEIGHT=$(tput lines 2>/dev/null || echo 50)
    # Dynamic layout to reduce wrapping on narrow terminals
    LEFT_COL=2
    RIGHT_COL=$(( TERM_WIDTH > 90 ? TERM_WIDTH/2 + 2 : TERM_WIDTH - 38 ))
    if [ "$RIGHT_COL" -lt 40 ]; then RIGHT_COL=40; fi
    LEFT_WIDTH=$(( RIGHT_COL - LEFT_COL - 4 ))
    [ "$LEFT_WIDTH" -lt 20 ] && LEFT_WIDTH=20
    RIGHT_WIDTH=$(( TERM_WIDTH - RIGHT_COL - 4 ))
    [ "$RIGHT_WIDTH" -lt 20 ] && RIGHT_WIDTH=20
    STATUS_ROW=$(( TERM_HEIGHT - 4 ))
    [ "$STATUS_ROW" -lt 24 ] && STATUS_ROW=24
}

# Cached command execution (simplified for compatibility)
cached_cmd() {
    local cmd="$1"
    local cache_time=${2:-5}  # Cache for 5 seconds by default
    local cache_key=$(echo "$cmd" | md5 || echo "$cmd")
    local now=$(date +%s)
    
    # Simple cache using grep to find cached entries
    local cache_file="/tmp/hero_cmd_cache"
    touch "$cache_file"
    
    # Check if we have a cached result that's still valid
    if grep -q "^$cache_key|" "$cache_file"; then
        local cached_entry=$(grep "^$cache_key|" "$cache_file")
        local cached_time=$(echo "$cached_entry" | cut -d'|' -f2)
        local cached_result=$(echo "$cached_entry" | cut -d'|' -f3-)
        
        if [ $((now - cached_time)) -lt $cache_time ]; then
            echo "$cached_result"
            return 0
        fi
    fi
    
    # Execute command and cache result
    local result
    result=$(eval "$cmd" 2>/dev/null)
    
    # Update cache (remove old entry if exists, add new one)
    grep -v "^$cache_key|" "$cache_file" > "$cache_file.tmp"
    echo "$cache_key|$now|$result" >> "$cache_file.tmp"
    mv "$cache_file.tmp" "$cache_file"
    
    echo "$result"
}

# Initialize
init() {
    mkdir -p "$HERO_HOME"
    mkdir -p "$HERO_CACHE"
    touch "$HERO_LOG"
    dbg "init start"

    # Single-instance lock: terminate previous instance if still running
    if [ -f "$LOCK_FILE" ]; then
        old_pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            log_event "Existing instance ($old_pid) detected; requesting termination"
            kill "$old_pid" 2>/dev/null || true
            sleep 1
            if kill -0 "$old_pid" 2>/dev/null; then
                kill -9 "$old_pid" 2>/dev/null || true
                sleep 0.2
            fi
        fi
    fi
    echo "$$" > "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE" >/dev/null 2>&1' EXIT
    hide_cursor
    [ -t 1 ] && clear || true
    
    # Stop any other dashboards (avoid killing self)
    for pat in "nexus_dashboard" "hero_dashboard"; do
        if command -v pgrep >/dev/null 2>&1; then
            pgrep -f "$pat" 2>/dev/null | while read -r pid; do
                [ -z "$pid" ] && continue
                if [ "$pid" != "$$" ] && [ "$pid" != "$PPID" ]; then
                    kill "$pid" 2>/dev/null || true
                fi
            done
        else
            # Fallback: best effort without pgrep (macOS has pgrep by default)
            pkill -f "$pat" 2>/dev/null || true
        fi
    done
    sleep 0.5
    
    # Initial data fetch
    update_lazy_data
    dbg "init done"
}

# Cleanup
cleanup() {
    local reason="$1"
    log_event "Dashboard cleanup (reason: ${reason:-unknown})"
    show_cursor
    [ -t 1 ] && clear || true
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║ ${WHITE}Hero Core Session Terminated${CYAN}           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
}
trap 'cleanup EXIT' EXIT
trap 'cleanup INT' INT
trap 'cleanup TERM' TERM

# Log events
log_event() {
    local msg="$(date '+%Y-%m-%d %H:%M:%S') | $1"
    echo "$msg" >> "$HERO_LOG"
    echo "$msg" >> "/tmp/hero_core.log"
}

# Update lazy-refresh data (Claude usage, GitHub activity)
update_lazy_data() {
    # Update Claude usage data
    HERO_DASHBOARD_DIR="${HERO_DASHBOARD_DIR:-/Users/rudlord/Hero_dashboard}"
    if [ -f "$HERO_DASHBOARD_DIR/monitors/claude_usage_monitor.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/claude_usage_monitor.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/claude_usage_monitor.py" > /dev/null 2>&1 &
        fi
    fi
    # Analyze token trends
    if [ -f "$HERO_DASHBOARD_DIR/monitors/token_usage_analyzer.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/token_usage_analyzer.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/token_usage_analyzer.py" > /dev/null 2>&1 &
        fi
    fi
    
    # Update GitHub activity data
    if [ -f "$HERO_DASHBOARD_DIR/monitors/github_activity_monitor.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/github_activity_monitor.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/github_activity_monitor.py" > /dev/null 2>&1 &
        fi
    fi
    # Update agents and code activity
    if [ -f "$HERO_DASHBOARD_DIR/monitors/agents_monitor.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/agents_monitor.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/agents_monitor.py" > /dev/null 2>&1 &
        fi
    fi
    if [ -f "$HERO_DASHBOARD_DIR/monitors/code_activity_monitor.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/code_activity_monitor.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/code_activity_monitor.py" > /dev/null 2>&1 &
        fi
    fi
    
    # Update LangSmith tracing stats
    if [ -f "$HERO_DASHBOARD_DIR/monitors/langsmith_tracer.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/langsmith_tracer.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/langsmith_tracer.py" > /dev/null 2>&1 &
        fi
    fi
    
    # Update agent coordination status
    if [ -f "$HERO_DASHBOARD_DIR/monitors/agent_coordinator.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/agent_coordinator.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/agent_coordinator.py" > /dev/null 2>&1 &
        fi
    fi
    
    # Update Chimera bridge status
    if [ -f "$HERO_DASHBOARD_DIR/monitors/chimera_bridge.py" ]; then
        if ! pgrep -f "$HERO_DASHBOARD_DIR/monitors/chimera_bridge.py" >/dev/null 2>&1; then
            python3 "$HERO_DASHBOARD_DIR/monitors/chimera_bridge.py" > /dev/null 2>&1 &
        fi
    fi
}

# Draw ASCII header
draw_header() {
    move_cursor 1 1
    echo -e "${CYAN_BRIGHT}"
    echo "    ██╗  ██╗███████╗██████╗  ██████╗      ██████╗ ██████╗ ██████╗ ███████╗"
    echo "    ██║  ██║██╔════╝██╔══██╗██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝"
    echo "    ███████║█████╗  ██████╔╝██║   ██║    ██║     ██║   ██║██████╔╝█████╗  "
    echo "    ██╔══██║██╔══╝  ██╔══██╗██║   ██║    ██║     ██║   ██║██╔══██╗██╔══╝  "
    echo "    ██║  ██║███████╗██║  ██║╚██████╔╝    ╚██████╗╚██████╔╝██║  ██║███████╗"
    echo "    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝"
    echo -e "${NC}"
    
    move_cursor 7 35
    echo -e "${GRAY}[ by Quantropy ]${NC}"
    
    move_cursor 9 1
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Claude Token Usage Section
update_claude_usage_section() {
    local row=11
    local col=2
    
    move_cursor $row $col
    echo -e "${CYAN_BRIGHT}[ CLAUDE USAGE ]${NC}"
    
    # Read Claude usage data from cache
    if [ -f "$CLAUDE_USAGE" ]; then
        local usage_data=$(cat "$CLAUDE_USAGE" 2>/dev/null)
        
        if [ -n "$usage_data" ]; then
            # Use jq for faster JSON parsing if available, fallback to python
            if command -v jq >/dev/null 2>&1; then
                local tokens=$(echo "$usage_data" | jq -r '.total_tokens // 0' 2>/dev/null)
                local limit=$(echo "$usage_data" | jq -r '.daily_limit // 0' 2>/dev/null)
                local percentage=$(echo "$usage_data" | jq -r '.usage_percentage // 0' 2>/dev/null)
                local sessions=$(echo "$usage_data" | jq -r '.active_sessions // 0' 2>/dev/null)
            else
                local tokens=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_tokens', 0))" 2>/dev/null || echo "0")
                local limit=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('daily_limit', 0))" 2>/dev/null || echo "0")
                local percentage=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('usage_percentage', 0))" 2>/dev/null || echo "0")
                local sessions=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('active_sessions', 0))" 2>/dev/null || echo "0")
            fi
            
            # Active sessions
            move_cursor $((row+1)) $((col+2))
            clear_to_eol
            printf "Sessions: ${WHITE}%d active${NC}" "$sessions"
            
            # Token usage with bar
            move_cursor $((row+2)) $((col+2))
            clear_to_eol
            # Keep compact formatting (no locale thousands separators) to avoid wrapping
            printf "Tokens: ${WHITE}%d${NC}/${GRAY}%d${NC}" "$tokens" "$limit"
            
            # Usage bar
            move_cursor $((row+3)) $((col+2))
            clear_to_eol
            printf "["
            local bar_width=$(( LEFT_WIDTH - 12 ))
            [ $bar_width -lt 10 ] && bar_width=10
            local filled=$((percentage * bar_width / 100))
            for ((i=0; i<bar_width; i++)); do
                if [ $i -lt $filled ]; then
                    if [ $percentage -lt 50 ]; then
                        echo -ne "${GREEN}█"
                    elif [ $percentage -lt 80 ]; then
                        echo -ne "${YELLOW}█"
                    else
                        echo -ne "${RED}█"
                    fi
                else
                    echo -ne "${DARK}░"
                fi
            done
            echo -ne "${NC}] ${WHITE}${percentage}%${NC}"

            # Trend info
            if [ -f "$TOKEN_ANALYSIS" ]; then
                local trend=$(cat "$TOKEN_ANALYSIS" | (jq -r '.trend // "flat"' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('trend','flat'))" 2>/dev/null || echo flat))
                local avg=$(cat "$TOKEN_ANALYSIS" | (jq -r '.avg_tokens_per_sample // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('avg_tokens_per_sample',0))" 2>/dev/null || echo 0))
                move_cursor $((row+4)) $((col+2))
                clear_to_eol
                case "$trend" in
                    high) printf "Trend: ${RED}high${NC}  Avg Δ: ${WHITE}%s${NC}" "$avg" ;;
                    medium) printf "Trend: ${YELLOW}medium${NC}  Avg Δ: ${WHITE}%s${NC}" "$avg" ;;
                    *) printf "Trend: ${GREEN}flat${NC}  Avg Δ: ${WHITE}%s${NC}" "$avg" ;;
                esac
            fi
        fi
    else
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        echo -ne "${GRAY}Loading token data...${NC}"
    fi
}

# GitHub Activity Section
update_github_activity_section() {
    local row=18
    local col=2
    
    move_cursor $row $col
    echo -e "${PINK}[ GITHUB ACTIVITY - 21 DAYS ]${NC}"
    
    # Read GitHub activity data from cache
    if [ -f "$GITHUB_ACTIVITY" ]; then
        local activity_data=$(cat "$GITHUB_ACTIVITY" 2>/dev/null)
        
        if [ -n "$activity_data" ]; then
            # Use jq for faster JSON parsing if available, fallback to python
            if command -v jq >/dev/null 2>&1; then
                local graph=$(echo "$activity_data" | jq -r '.graph_ascii // ""' 2>/dev/null)
                local total=$(echo "$activity_data" | jq -r '.total_contributions // 0' 2>/dev/null)
                local streak=$(echo "$activity_data" | jq -r '.streak // 0' 2>/dev/null)
            else
                local graph=$(echo "$activity_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('graph_ascii', ''))" 2>/dev/null || echo "")
                local total=$(echo "$activity_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_contributions', 0))" 2>/dev/null || echo "0")
                local streak=$(echo "$activity_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('streak', 0))" 2>/dev/null || echo "0")
            fi
            
            # Activity graph (skip on narrow left panel to prevent wrapping)
            if [ $LEFT_WIDTH -ge 40 ]; then
                move_cursor $((row+1)) $((col+2))
                clear_to_eol
                if [ -n "$graph" ]; then
                    # Color the graph based on activity
                    colored_graph=""
                    for ((i=0; i<${#graph}; i++)); do
                        char="${graph:$i:1}"
                        case "$char" in
                            "·") colored_graph+="${DARK}·${NC}" ;;
                            "▫") colored_graph+="${GREEN}▫${NC}" ;;
                            "▪") colored_graph+="${GREEN}▪${NC}" ;;
                            "◼") colored_graph+="${GREEN}◼${NC}" ;;
                            "█") colored_graph+="${GREEN}█${NC}" ;;
                            *) colored_graph+="$char" ;;
                        esac
                    done
                    echo -ne "Graph: $colored_graph"
                else
                    echo -ne "Graph: ${GRAY}No data${NC}"
                fi
            fi
            
            # Stats
            move_cursor $((row+2)) $((col+2))
            clear_to_eol
            printf "Contributions: ${WHITE}%d${NC}  Streak: ${WHITE}%d days${NC}" "$total" "$streak"
        fi
    else
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        echo -ne "${GRAY}Loading GitHub data...${NC}"
    fi
}

# AI Systems Section (moved down)
update_ai_section() {
    local row=22
    local col=2
    
    move_cursor $row $col
    echo -e "${CYAN}[ AI SYSTEMS ]${NC}"
    
    # Use cached command execution
    local ps_output=$(cached_cmd "ps aux" 3)
    
    # Claude
    local claude_count=$(echo "$ps_output" | grep -c "claude" 2>/dev/null || echo "0")
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    if [ "$claude_count" -gt 0 ]; then
        printf "${GREEN}●${NC} Claude: ${GREEN}%d${NC}" "$claude_count"
    else
        printf "${DARK}○${NC} Claude: ${GRAY}off${NC}"
    fi
    
    if [ $LEFT_WIDTH -ge 36 ]; then
        # Qwen
        move_cursor $((row+1)) $((col+15))
        if echo "$ps_output" | grep -q "qwen"; then
            printf "${ORANGE}●${NC} Qwen: ${ORANGE}on${NC}"
        else
            printf "${DARK}○${NC} Qwen: ${GRAY}off${NC}"
        fi
        
        # VS Code
        local vscode_count=$(echo "$ps_output" | grep -c "Code Helper" 2>/dev/null || echo "0")
        move_cursor $((row+1)) $((col+28))
        if [ "$vscode_count" -gt 0 ]; then
            printf "${PURPLE}●${NC} VSCode: ${PURPLE}%d${NC}" "$vscode_count"
        else
            printf "${DARK}○${NC} VSCode: ${GRAY}off${NC}"
        fi
    fi
}

# Chimera Knowledge Base Section (right side)
update_chimera_section() {
    local row=11
    local col=$RIGHT_COL
    
    move_cursor $row $col
    echo -e "${CYAN}[ CHIMERA INTEGRATION ]${NC}"
    
    # Chimera bridge status
    if [ -f "$CHIMERA_INTEGRATION" ]; then
        local chimera_data=$(cat "$CHIMERA_INTEGRATION" 2>/dev/null)
        local chimera_detected=$(echo "$chimera_data" | (jq -r '.integration_status.chimera_detected // false' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('integration_status',{}).get('chimera_detected',False))" 2>/dev/null || echo false))
        local nats_connected=$(echo "$chimera_data" | (jq -r '.integration_status.nats_connected // false' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('integration_status',{}).get('nats_connected',False))" 2>/dev/null || echo false))
        local agents_discovered=$(echo "$chimera_data" | (jq -r '.chimera_agents.total // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('chimera_agents',{}).get('total',0))" 2>/dev/null || echo 0))
        
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        if [ "$chimera_detected" = "true" ]; then
            printf "Framework: ${GREEN}● detected${NC}  Agents: ${WHITE}%d${NC}" "$agents_discovered"
        else
            printf "Framework: ${GRAY}○ not found${NC}"
        fi
        
        move_cursor $((row+2)) $((col+2))
        clear_to_eol
        if [ "$nats_connected" = "true" ]; then
            printf "NATS: ${GREEN}● connected${NC}"
        else
            printf "NATS: ${GRAY}○ offline${NC}"
        fi
    fi
    
    # Knowledge graph status
    if [ -f "$GRAPHITI_STATS" ]; then
        local data=$(cat "$GRAPHITI_STATS" 2>/dev/null)
        if [ -n "$data" ]; then
            local nodes=$(echo "$data" | jq -r '.node_count // 0' 2>/dev/null || echo "0")
            local edges=$(echo "$data" | jq -r '.edge_count // 0' 2>/dev/null || echo "0")
            
            move_cursor $((row+3)) $((col+2))
            clear_to_eol
            printf "Knowledge: ${WHITE}%s${NC} nodes  ${WHITE}%s${NC} edges" "$nodes" "$edges"
        fi
    fi
    
    # Services status (condensed)
    local services_row=$((row+4))
    
    # Use cached command execution for process checks
    local ps_output=$(cached_cmd "ps aux" 3)
    
    move_cursor $services_row $((col+2))
    clear_to_eol
    
    # Redis status (inline)
    if echo "$ps_output" | grep -q "redis-server"; then
        printf "Redis: ${GREEN}●${NC}  "
    else
        printf "Redis: ${GRAY}○${NC}  "
    fi
    
    # Docker status (inline)
    local docker_count=$(cached_cmd "docker ps -q 2>/dev/null | wc -l" 5 | tr -d ' ')
    move_cursor $((row+3)) $((col+2))
    clear_to_eol
    printf "${CYAN}●${NC} Docker: ${WHITE}%d${NC} containers" "$docker_count"
}

# System Metrics Section (right side)
update_system_section() {
    local row=16
    local col=$RIGHT_COL
    
    move_cursor $row $col
    echo -e "${CYAN}[ SYSTEM ]${NC}"
    
    # CPU - prefer psutil, fallback to parsing top
    local cpu=$(python3 - <<'PY' 2>/dev/null || echo "")
import psutil
print(int(psutil.cpu_percent(interval=0.2)))
PY
)
    if [ -z "$cpu" ]; then
        local top_output=$(cached_cmd "top -l 1" 2)
        cpu=$(echo "$top_output" | awk -F'[ ,]+' '/CPU usage/{for(i=1;i<=NF;i++){if($i ~ /idle/){gsub(/[^0-9.]/,"",$(i-1)); idle=$(i-1)}}} END{if(idle=="") idle=0; print int(100-idle)}' 2>/dev/null | head -n1)
        [ -z "$cpu" ] && cpu=0
    fi
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    printf "CPU: ${WHITE}%3s%%${NC}" "$cpu"
    
    # Memory - use psutil for more accurate results
    local mem=$(python3 -c "
import psutil
print(int(psutil.virtual_memory().percent))
" 2>/dev/null || echo "0")
    move_cursor $((row+2)) $((col+2))
    clear_to_eol
    printf "MEM: ${WHITE}%3s%%${NC}" "$mem"
}

# Agents & Processes Section (left)
update_agents_section() {
    local row=15
    local col=2
    move_cursor $row $col
    echo -e "${CYAN}[ AGENTS & PROCESSES ]${NC}"

    if [ -f "$AGENTS_STATUS" ]; then
        local data=$(cat "$AGENTS_STATUS" 2>/dev/null)
        local total=$(echo "$data" | (jq -r '.total_agents // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('total_agents',0))" 2>/dev/null || echo 0))
        local models=$(echo "$data" | (jq -r '.buckets.models // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('buckets',{}).get('models',0))" 2>/dev/null || echo 0))
        local editors=$(echo "$data" | (jq -r '.buckets.editors // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('buckets',{}).get('editors',0))" 2>/dev/null || echo 0))
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        printf "Total: ${WHITE}%d${NC}  Models: ${WHITE}%d${NC}  Editors: ${WHITE}%d${NC}" "$total" "$models" "$editors"

        # Top processes
        local top_list
        if command -v jq >/dev/null 2>&1; then
            top_list=$(echo "$data" | jq -r '.top[] | "\(.cpu)% CPU · \(.mem)% MEM · PID \(.pid) · \(.name)"' 2>/dev/null | head -3)
        else
            top_list=$(echo "$data" | python3 - <<'PY'
import sys, json
d=json.load(sys.stdin)
for i, t in enumerate(d.get('top', [])[:3]):
    print(f"{t.get('cpu',0)}% CPU · {t.get('mem',0)}% MEM · PID {t.get('pid','-')} · {t.get('name','')}")
PY
)
        fi
        local i=0
        while IFS= read -r line; do
            move_cursor $((row+2+i)) $((col+2))
            clear_to_eol
            # Trim to panel width to avoid wrapping
            printf "%s" "${line:0:$LEFT_WIDTH}"
            i=$((i+1))
        done <<< "$top_list"
    else
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        echo -ne "${GRAY}Scanning processes...${NC}"
    fi
}

# Code Activity Section (right)
update_code_activity_section() {
    local row=20
    local col=$RIGHT_COL
    move_cursor $row $col
    echo -e "${MAGENTA}[ CODE ACTIVITY - 7D ]${NC}"

    if [ -f "$CODE_ACTIVITY" ]; then
        local data=$(cat "$CODE_ACTIVITY" 2>/dev/null)
        local repos=$(echo "$data" | (jq -r '.total_repos // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('total_repos',0))" 2>/dev/null || echo 0))
        local ins=$(echo "$data" | (jq -r '.total_insertions // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('total_insertions',0))" 2>/dev/null || echo 0))
        local del=$(echo "$data" | (jq -r '.total_deletions // 0' 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin).get('total_deletions',0))" 2>/dev/null || echo 0))
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        printf "Repos: ${WHITE}%d${NC}  +${GREEN}%d${NC} / -${RED}%d${NC}" "$repos" "$ins" "$del"

        # Show first repo sparkline
        local repo0
        if command -v jq >/dev/null 2>&1; then
            repo0=$(echo "$data" | jq -r '.repos[0] | "\(.branch) · \(.spark_commits) · \(.path)"' 2>/dev/null)
        else
            repo0=$(echo "$data" | python3 - <<'PY'
import sys, json
d=json.load(sys.stdin)
r=d.get('repos', [{}])[:1]
if r:
    r=r[0]
    print(f"{r.get('branch','-')} · {r.get('spark_commits','')} · {r.get('path','')}")
PY
)
        fi
        if [ -n "$repo0" ]; then
            move_cursor $((row+2)) $((col+2))
            clear_to_eol
            printf "%s" "${repo0:0:$RIGHT_WIDTH}"
        fi
    else
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        echo -ne "${GRAY}Analyzing git activity...${NC}"
    fi
}

# Status bar
draw_status_bar() {
    local row=$STATUS_ROW
    
    move_cursor $row 1
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    move_cursor $((row+1)) 2
    clear_to_eol
    printf "${WHITE}%s${NC} | ${GREEN}%s${NC}@${BLUE}%s${NC} | ${YELLOW}Hero Core Enhanced${NC}" \
        "$(date '+%H:%M:%S')" \
        "$USER" \
        "$(hostname -s)"
    
    move_cursor $((row+2)) 2
    clear_to_eol
    printf "${GRAY}[T]okens [G]raphiti [N]eo4j [C]CM [H]elp [R]efresh [Q]uit${NC}"
}

# Show Claude Monitor
show_claude_monitor() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}         CLAUDE TOKEN USAGE MONITOR                   ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Try to show ccm output
    echo -e "${YELLOW}Launching Claude monitor (ccm)...${NC}"
    echo ""
    
    if command -v ccm &>/dev/null; then
        timeout 5 ccm 2>&1 | head -20
    else
        echo -e "${RED}ccm command not found${NC}"
        echo ""
        echo "To install Claude monitor:"
        echo "  pip install claude-monitor"
        echo "  or"
        echo "  uv tool install claude-monitor"
    fi
    
    echo ""
    echo -e "${GRAY}Press any key to return...${NC}"
    read -n 1
    initial_display
}

# Initial display
initial_display() {
    clear
    get_term_size
    draw_header
}

# Update display
update_display() {
    dbg "update_display tick"
    # Increment lazy refresh counter
    LAZY_REFRESH_COUNTER=$((LAZY_REFRESH_COUNTER + 1))
    
    # Update lazy data periodically
    if [ $((LAZY_REFRESH_COUNTER % LAZY_REFRESH_INTERVAL)) -eq 0 ]; then
        update_lazy_data || dbg "update_lazy_data failed"
    fi
    
    # Always update these sections
    update_agents_section || dbg "agents section failed"
    update_chimera_section || dbg "chimera section failed"
    update_system_section || dbg "system section failed"
    
    # Update token and GitHub sections (uses cached data)
    update_claude_usage_section || dbg "claude section failed"
    update_github_activity_section || dbg "github section failed"
    update_code_activity_section || dbg "code section failed"
    
    draw_status_bar
    
    # Reset cursor position
    move_cursor $((STATUS_ROW + 6)) 1
}

# Main loop
main() {
    dbg "main start"
    init
    log_event "Hero Core Enhanced started"
    initial_display
    
    while true; do
        update_display || dbg "update_display errored"
        
        # Read with timeout
        if read -t $REFRESH_RATE -n 1 key 2>/dev/null; then
            case $key in
                t|T)
                    # Force refresh token data
                    update_lazy_data
                    sleep 1
                    ;;
                g|G)
                    echo -e "\n${YELLOW}Opening Graphiti details...${NC}"
                    if [ -f "$HERO_DASHBOARD_DIR/monitors/graphiti_monitor.py" ]; then
                        python3 "$HERO_DASHBOARD_DIR/monitors/graphiti_monitor.py"
                        echo -e "${GRAY}Press any key to continue...${NC}"
                        read -n 1
                    fi
                    initial_display
                    ;;
                n|N)
                    echo -e "\n${YELLOW}Opening Neo4j Browser...${NC}"
                    open "http://localhost:7474" 2>/dev/null || echo "Neo4j not accessible"
                    ;;
                c|C)
                    show_claude_monitor
                    ;;
                a|A)
                    # Show agent coordination details
                    clear
                    echo -e "${CYAN}AGENT COORDINATION STATUS${NC}"
                    echo "═══════════════════════════"
                    if [ -f "$AGENT_COORDINATION" ]; then
                        cat "$AGENT_COORDINATION" | jq . 2>/dev/null || cat "$AGENT_COORDINATION"
                    else
                        echo "No coordination data available"
                    fi
                    echo ""
                    echo -e "${GRAY}Press any key to return...${NC}"
                    read -n 1
                    initial_display
                    ;;
                l|L)
                    # Show LangSmith traces
                    clear
                    echo -e "${CYAN}LANGSMITH TRACING STATUS${NC}"
                    echo "═══════════════════════════"
                    if [ -f "$LANGSMITH_STATS" ]; then
                        cat "$LANGSMITH_STATS" | jq . 2>/dev/null || cat "$LANGSMITH_STATS"
                    else
                        echo "No tracing data available"
                    fi
                    echo ""
                    echo -e "${GRAY}Press any key to return...${NC}"
                    read -n 1
                    initial_display
                    ;;
                s|S)
                    # Sync with Chimera
                    echo -e "\n${YELLOW}Syncing with Chimera framework...${NC}"
                    if [ -f "$HERO_DASHBOARD_DIR/monitors/chimera_bridge.py" ]; then
                        python3 "$HERO_DASHBOARD_DIR/monitors/chimera_bridge.py" --sync
                    fi
                    sleep 2
                    initial_display
                    ;;
                h|H)
                    clear
                    echo -e "${CYAN}HERO CORE ENHANCED - HELP${NC}"
                    echo "═══════════════════════════"
                    echo "T - Refresh token/GitHub data"
                    echo "A - Show agent coordination status"
                    echo "L - Show LangSmith tracing status"
                    echo "S - Sync with Chimera framework"
                    echo "G - Show Graphiti details"
                    echo "N - Open Neo4j browser"
                    echo "C - Launch Claude monitor (ccm)"
                    echo "R - Force refresh display"
                    echo "Q - Quit"
                    echo ""
                    echo "Multi-agent coordination active"
                    echo "LangSmith tracing integrated"
                    echo "Chimera framework bridge enabled"
                    echo ""
                    echo -e "${GRAY}Press any key to return...${NC}"
                    read -n 1
                    initial_display
                    ;;
                r|R)
                    initial_display
                    ;;
                q|Q)
                    log_event "Dashboard terminated by user"
                    break
                    ;;
            esac
        fi
    done
# Debug helper
dbg() {
    [ -n "$HERO_DEBUG" ] || return 0
    echo "$(date '+%Y-%m-%d %H:%M:%S') | DBG | $1" >> "$HERO_LOG"
}
    dbg "main loop exit"
}

# Start
main
