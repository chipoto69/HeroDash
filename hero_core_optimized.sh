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
GITHUB_ACTIVITY="$HERO_CACHE/github_activity.json"
REFRESH_RATE=3
LAZY_REFRESH_COUNTER=0
LAZY_REFRESH_INTERVAL=10  # Refresh token data every 10 cycles (30 seconds)

# Project Paths
CHIMERA_BASE="/Users/rudlord/q3/Frontline"
GRAPHITI_BASE="/Users/rudlord/q3/0_MEMORY/graphiti"

# Cache for system commands
declare -A CMD_CACHE
declare -A CMD_CACHE_TIME

# Terminal control
clear_to_eol() { echo -ne "\033[K"; }
move_cursor() { echo -ne "\033[${1};${2}H"; }
hide_cursor() { tput civis 2>/dev/null; }
show_cursor() { tput cnorm 2>/dev/null; }

# Get terminal size
get_term_size() {
    TERM_WIDTH=$(tput cols 2>/dev/null || echo 140)
    TERM_HEIGHT=$(tput lines 2>/dev/null || echo 50)
}

# Cached command execution
cached_cmd() {
    local cmd="$1"
    local cache_time=${2:-5}  # Cache for 5 seconds by default
    local cache_key="$(echo "$cmd" | md5)"
    local now=$(date +%s)
    
    # Check if we have a cached result that's still valid
    if [[ -n "${CMD_CACHE_TIME[$cache_key]}" ]] && [[ $((now - CMD_CACHE_TIME[$cache_key])) -lt $cache_time ]]; then
        echo "${CMD_CACHE[$cache_key]}"
        return 0
    fi
    
    # Execute command and cache result
    local result
    result=$(eval "$cmd" 2>/dev/null)
    CMD_CACHE[$cache_key]="$result"
    CMD_CACHE_TIME[$cache_key]=$now
    
    echo "$result"
}

# Initialize
init() {
    mkdir -p "$HERO_HOME"
    mkdir -p "$HERO_CACHE"
    touch "$HERO_LOG"
    hide_cursor
    clear
    
    # Stop any other dashboards
    pkill -f "nexus_dashboard" 2>/dev/null
    pkill -f "hero_dashboard" 2>/dev/null
    sleep 0.5
    
    # Initial data fetch
    update_lazy_data
}

# Cleanup
cleanup() {
    show_cursor
    clear
    echo -e "${CYAN}╔════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║ ${WHITE}Hero Core Session Terminated${CYAN}           ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════╝${NC}"
}
trap cleanup EXIT INT TERM

# Log events
log_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" >> "$HERO_LOG"
}

# Update lazy-refresh data (Claude usage, GitHub activity)
update_lazy_data() {
    # Update Claude usage data
    if [ -f "/Users/rudlord/Hero_dashboard/monitors/claude_usage_monitor.py" ]; then
        python3 /Users/rudlord/Hero_dashboard/monitors/claude_usage_monitor.py > /dev/null 2>&1 &
    fi
    
    # Update GitHub activity data
    if [ -f "/Users/rudlord/Hero_dashboard/monitors/github_activity_monitor.py" ]; then
        python3 /Users/rudlord/Hero_dashboard/monitors/github_activity_monitor.py > /dev/null 2>&1 &
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
            printf "Tokens: ${WHITE}%s${NC}/${GRAY}%s${NC}" "$(printf "%'d" $tokens)" "$(printf "%'d" $limit)"
            
            # Usage bar
            move_cursor $((row+3)) $((col+2))
            clear_to_eol
            printf "["
            local bar_width=15
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
        fi
    else
        move_cursor $((row+1)) $((col+2))
        clear_to_eol
        echo -ne "${GRAY}Loading token data...${NC}"
    fi
}

# GitHub Activity Section
update_github_activity_section() {
    local row=16
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
            
            # Activity graph
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
    local row=20
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
        printf "${DARK}○${NC} Claude: ${GRAY}off${NC}