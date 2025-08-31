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

# Project Paths (configurable via environment variables)
CHIMERA_BASE="${CHIMERA_BASE:-/Users/rudlord/q3/Frontline}"
GRAPHITI_BASE="${GRAPHITI_BASE:-/Users/rudlord/q3/0_MEMORY/graphiti}"

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
    HERO_DASHBOARD_DIR="${HERO_DASHBOARD_DIR:-/Users/rudlord/Hero_dashboard}"
    if [ -f "$HERO_DASHBOARD_DIR/monitors/claude_usage_monitor.py" ]; then
        python3 "$HERO_DASHBOARD_DIR/monitors/claude_usage_monitor.py" > /dev/null 2>&1 &
    fi
    
    # Update GitHub activity data
    if [ -f "$HERO_DASHBOARD_DIR/monitors/github_activity_monitor.py" ]; then
        python3 "$HERO_DASHBOARD_DIR/monitors/github_activity_monitor.py" > /dev/null 2>&1 &
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
            local tokens=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_tokens', 0))" 2>/dev/null || echo "0")
            local limit=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('daily_limit', 0))" 2>/dev/null || echo "0")
            local percentage=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('usage_percentage', 0))" 2>/dev/null || echo "0")
            local sessions=$(echo "$usage_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('active_sessions', 0))" 2>/dev/null || echo "0")
            
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
            local graph=$(echo "$activity_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('graph_ascii', ''))" 2>/dev/null || echo "")
            local total=$(echo "$activity_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_contributions', 0))" 2>/dev/null || echo "0")
            local streak=$(echo "$activity_data" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('streak', 0))" 2>/dev/null || echo "0")
            
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
    
    # Claude
    local claude_count=$(pgrep -f "claude" 2>/dev/null | wc -l | tr -d ' ')
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    if [ "$claude_count" -gt 0 ]; then
        printf "${GREEN}●${NC} Claude: ${GREEN}%d${NC}" "$claude_count"
    else
        printf "${DARK}○${NC} Claude: ${GRAY}off${NC}"
    fi
    
    # Qwen
    move_cursor $((row+1)) $((col+15))
    if pgrep -f "qwen" &>/dev/null; then
        printf "${ORANGE}●${NC} Qwen: ${ORANGE}on${NC}"
    else
        printf "${DARK}○${NC} Qwen: ${GRAY}off${NC}"
    fi
    
    # VS Code
    local vscode_count=$(pgrep -f "Code Helper" 2>/dev/null | wc -l | tr -d ' ')
    move_cursor $((row+1)) $((col+28))
    if [ "$vscode_count" -gt 0 ]; then
        printf "${PURPLE}●${NC} VSCode: ${PURPLE}%d${NC}" "$vscode_count"
    else
        printf "${DARK}○${NC} VSCode: ${GRAY}off${NC}"
    fi
}

# Chimera Knowledge Base Section (right side)
update_chimera_section() {
    local row=11
    local col=45
    
    move_cursor $row $col
    echo -e "${MAGENTA}[ CHIMERA KB ]${NC}"
    
    # Neo4j/Graphiti
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    if pgrep -f "neo4j" &>/dev/null; then
        printf "${GREEN}●${NC} Graphiti: ${GREEN}online${NC}"
    else
        printf "${YELLOW}○${NC} Graphiti: ${YELLOW}offline${NC}"
    fi
    
    # Redis
    move_cursor $((row+2)) $((col+2))
    clear_to_eol
    if pgrep -f "redis-server" &>/dev/null; then
        local keys=$(redis-cli dbsize 2>/dev/null | grep -oE "[0-9]+" || echo "0")
        printf "${GREEN}●${NC} Redis: ${WHITE}%s${NC} keys" "$keys"
    else
        printf "${DARK}○${NC} Redis: ${GRAY}offline${NC}"
    fi
    
    # Docker
    local docker_count=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
    move_cursor $((row+3)) $((col+2))
    clear_to_eol
    printf "${CYAN}●${NC} Docker: ${WHITE}%d${NC} containers" "$docker_count"
}

# System Metrics Section (right side)
update_system_section() {
    local row=16
    local col=45
    
    move_cursor $row $col
    echo -e "${CYAN}[ SYSTEM ]${NC}"
    
    # CPU
    local cpu=$(top -l 1 2>/dev/null | grep "CPU usage" | awk '{print $3}' | cut -d% -f1 | cut -d. -f1 || echo "0")
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    printf "CPU: ${WHITE}%3s%%${NC}" "$cpu"
    
    # Memory
    local mem=$(ps aux 2>/dev/null | awk '{sum+=$4} END {if(NR>0) printf "%.0f", sum; else print "0"}')
    move_cursor $((row+2)) $((col+2))
    clear_to_eol
    printf "MEM: ${WHITE}%3s%%${NC}" "$mem"
}

# Status bar
draw_status_bar() {
    local row=24
    
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
    # Increment lazy refresh counter
    LAZY_REFRESH_COUNTER=$((LAZY_REFRESH_COUNTER + 1))
    
    # Update lazy data periodically
    if [ $((LAZY_REFRESH_COUNTER % LAZY_REFRESH_INTERVAL)) -eq 0 ]; then
        update_lazy_data
    fi
    
    # Always update these sections
    update_ai_section
    update_chimera_section
    update_system_section
    
    # Update token and GitHub sections (uses cached data)
    update_claude_usage_section
    update_github_activity_section
    
    draw_status_bar
    
    # Reset cursor position
    move_cursor 28 1
}

# Main loop
main() {
    init
    log_event "Hero Core Enhanced started"
    initial_display
    
    while true; do
        update_display
        
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
                h|H)
                    clear
                    echo -e "${CYAN}HERO CORE ENHANCED - HELP${NC}"
                    echo "═══════════════════════════"
                    echo "T - Refresh token/GitHub data"
                    echo "G - Show Graphiti details"
                    echo "N - Open Neo4j browser"
                    echo "C - Launch Claude monitor (ccm)"
                    echo "R - Force refresh display"
                    echo "Q - Quit"
                    echo ""
                    echo "Token data refreshes every 30 seconds"
                    echo "GitHub data refreshes every 30 seconds"
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
}

# Start
main