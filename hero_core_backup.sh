#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# HERO CORE - Unified Command Centre
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
REFRESH_RATE=3

# Project Paths
CHIMERA_BASE="/Users/rudlord/q3/Frontline"
GRAPHITI_BASE="/Users/rudlord/q3/0_MEMORY/graphiti"

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

# Get Graphiti stats
get_graphiti_stats() {
    if [ -f "$GRAPHITI_STATS" ]; then
        local file_age=$(($(date +%s) - $(stat -f%m "$GRAPHITI_STATS" 2>/dev/null || echo 0)))
        if [ $file_age -lt 10 ]; then
            cat "$GRAPHITI_STATS" 2>/dev/null
            return
        fi
    fi
    
    # Try to update stats
    if pgrep -f "neo4j" > /dev/null 2>&1; then
        if [ -f "/Users/rudlord/Hero_dashboard/graphiti_monitor.py" ]; then
            python3 /Users/rudlord/Hero_dashboard/graphiti_monitor.py > /dev/null 2>&1 &
            sleep 1
            [ -f "$GRAPHITI_STATS" ] && cat "$GRAPHITI_STATS" 2>/dev/null
        fi
    fi
}

# AI Systems Section
update_ai_section() {
    local row=11
    
    move_cursor $row 2
    echo -e "${CYAN_BRIGHT}[ AI SYSTEMS ]${NC}"
    
    # Claude
    local claude_count=$(pgrep -f "claude" 2>/dev/null | wc -l | tr -d ' ')
    local claude_dirs=$(lsof -c claude 2>/dev/null | grep DIR | awk '{print $NF}' | sort -u | head -3)
    
    move_cursor $((row+1)) 4
    clear_to_eol
    if [ "$claude_count" -gt 0 ]; then
        printf "${GREEN}●${NC} Claude Code: ${GREEN}%d active${NC}" "$claude_count"
        
        if [ -n "$claude_dirs" ]; then
            move_cursor $((row+2)) 6
            clear_to_eol
            echo -ne "${GRAY}Working in: $(echo $claude_dirs | head -1 | xargs basename)${NC}"
        fi
    else
        printf "${DARK}○${NC} Claude Code: ${GRAY}offline${NC}"
    fi
    
    # Qwen
    move_cursor $((row+3)) 4
    clear_to_eol
    if pgrep -f "qwen" &>/dev/null; then
        printf "${ORANGE}●${NC} Qwen-code: ${ORANGE}running${NC}"
    else
        printf "${DARK}○${NC} Qwen-code: ${GRAY}inactive${NC}"
    fi
    
    # Gemini
    move_cursor $((row+4)) 4
    clear_to_eol
    if ps aux | grep -iE "gemini|bard" | grep -v grep > /dev/null 2>&1; then
        printf "${BLUE}●${NC} Gemini AI: ${BLUE}connected${NC}"
    else
        printf "${DARK}○${NC} Gemini AI: ${GRAY}offline${NC}"
    fi
    
    # VS Code
    local vscode_count=$(pgrep -f "Code Helper" 2>/dev/null | wc -l | tr -d ' ')
    move_cursor $((row+5)) 4
    clear_to_eol
    if [ "$vscode_count" -gt 0 ]; then
        printf "${PURPLE}●${NC} VS Code: ${PURPLE}%d helpers${NC}" "$vscode_count"
    else
        printf "${DARK}○${NC} VS Code: ${GRAY}closed${NC}"
    fi
}

# Chimera Knowledge Base Section
update_chimera_section() {
    local row=11
    local col=40
    
    move_cursor $row $col
    echo -e "${MAGENTA}[ CHIMERA KB ]${NC}"
    
    # Get Graphiti stats
    local stats_json=$(get_graphiti_stats)
    local entities=0
    local episodes=0
    local edges=0
    
    if [ -n "$stats_json" ]; then
        entities=$(echo "$stats_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('nodes',{}).get('entities',0))" 2>/dev/null || echo "0")
        episodes=$(echo "$stats_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('nodes',{}).get('episodes',0))" 2>/dev/null || echo "0")
        edges=$(echo "$stats_json" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('edges',{}).get('total',0))" 2>/dev/null || echo "0")
    fi
    
    # Neo4j/Graphiti
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    if pgrep -f "neo4j" &>/dev/null; then
        printf "${GREEN}●${NC} Graphiti: ${WHITE}%d${NC} entities" "$entities"
    else
        printf "${YELLOW}○${NC} Graphiti: ${YELLOW}Neo4j offline${NC}"
    fi
    
    # Episodes
    move_cursor $((row+2)) $((col+2))
    clear_to_eol
    printf "  Episodes: ${WHITE}%d${NC}" "$episodes"
    
    # Edges
    move_cursor $((row+3)) $((col+2))
    clear_to_eol
    printf "  Edges: ${WHITE}%d${NC}" "$edges"
    
    # Redis
    move_cursor $((row+4)) $((col+2))
    clear_to_eol
    if pgrep -f "redis-server" &>/dev/null; then
        local keys=$(redis-cli dbsize 2>/dev/null | grep -oE "[0-9]+" || echo "0")
        printf "${GREEN}●${NC} Redis: ${WHITE}%s${NC} keys" "$keys"
    else
        printf "${DARK}○${NC} Redis: ${GRAY}offline${NC}"
    fi
    
    # Archive files
    move_cursor $((row+5)) $((col+2))
    clear_to_eol
    local archives=0
    [ -d "$CHIMERA_BASE/data-process" ] && archives=$(find "$CHIMERA_BASE/data-process" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    printf "${CYAN}●${NC} Archives: ${WHITE}%d${NC} files" "$archives"
}

# System Metrics Section
update_system_section() {
    local row=18
    
    move_cursor $row 2
    echo -e "${CYAN}[ SYSTEM METRICS ]${NC}"
    
    # CPU
    local cpu=$(top -l 1 2>/dev/null | grep "CPU usage" | awk '{print $3}' | cut -d% -f1 | cut -d. -f1 || echo "0")
    move_cursor $((row+1)) 4
    clear_to_eol
    printf "CPU  [%3s%%] " "$cpu"
    for ((i=0; i<20; i++)); do
        if [ $i -lt $((cpu*20/100)) ]; then
            echo -ne "${GREEN}▓"
        else
            echo -ne "${DARK}░"
        fi
    done
    echo -ne "${NC}"
    
    # Memory
    local mem=$(ps aux 2>/dev/null | awk '{sum+=$4} END {if(NR>0) printf "%.0f", sum; else print "0"}')
    move_cursor $((row+2)) 4
    clear_to_eol
    printf "MEM  [%3s%%] " "$mem"
    for ((i=0; i<20; i++)); do
        if [ $i -lt $((mem*20/100)) ]; then
            echo -ne "${BLUE}▓"
        else
            echo -ne "${DARK}░"
        fi
    done
    echo -ne "${NC}"
    
    # Docker
    local docker_count=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
    move_cursor $((row+3)) 4
    clear_to_eol
    printf "Docker: ${WHITE}%d${NC} containers" "$docker_count"
    
    # Network
    local connections=$(netstat -an 2>/dev/null | grep -c ESTABLISHED || echo "0")
    move_cursor $((row+3)) 25
    printf "Network: ${WHITE}%d${NC} connections" "$connections"
}

# Activity Monitor Section
update_activity_section() {
    local row=18
    local col=50
    
    move_cursor $row $col
    echo -e "${PINK}[ ACTIVITY ]${NC}"
    
    # Recent activity indicator
    local activity_frames=("⣾" "⣽" "⣻" "⢿" "⡿" "⣟" "⣯" "⣷")
    local frame=$(($(date +%S) % 8))
    
    move_cursor $((row+1)) $((col+2))
    clear_to_eol
    echo -ne "${activity_frames[$frame]} Processing"
    
    # Command count
    local cmd_count=$(history 2>/dev/null | tail -10 | wc -l | tr -d ' ')
    move_cursor $((row+2)) $((col+2))
    clear_to_eol
    printf "Commands: ${WHITE}%d${NC}/min" "$cmd_count"
    
    # Uptime
    local uptime=$(uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')
    move_cursor $((row+3)) $((col+2))
    clear_to_eol
    printf "Uptime: ${WHITE}%s${NC}" "$uptime"
}

# Status bar
draw_status_bar() {
    local row=23
    
    move_cursor $row 1
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    move_cursor $((row+1)) 2
    clear_to_eol
    printf "${WHITE}%s${NC} | ${GREEN}%s${NC}@${BLUE}%s${NC} | ${YELLOW}Hero Core v1.0${NC}" \
        "$(date '+%H:%M:%S')" \
        "$USER" \
        "$(hostname -s)"
    
    move_cursor $((row+2)) 2
    clear_to_eol
    printf "${GRAY}[G]raphiti [N]eo4j [D]ocker [L]ogs [H]elp [R]efresh [Q]uit${NC}"
}

# Show Graphiti details
show_graphiti_details() {
    clear
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║${WHITE}         GRAPHITI TEMPORAL KNOWLEDGE GRAPH            ${MAGENTA}║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${CYAN}Location:${NC} $GRAPHITI_BASE"
    echo ""
    
    if [ -f "$GRAPHITI_STATS" ]; then
        echo -e "${CYAN}Current Statistics:${NC}"
        python3 -c "
import json
with open('$GRAPHITI_STATS', 'r') as f:
    data = json.load(f)
    nodes = data.get('nodes', {})
    edges = data.get('edges', {})
    print(f'  Entities: {nodes.get(\"entities\", 0):,}')
    print(f'  Episodes: {nodes.get(\"episodes\", 0):,}')
    print(f'  Communities: {nodes.get(\"communities\", 0):,}')
    print(f'  Total Edges: {edges.get(\"total\", 0):,}')
" 2>/dev/null || echo "  Unable to load statistics"
    fi
    
    echo ""
    echo -e "${CYAN}Quick Commands:${NC}"
    echo "  cd $GRAPHITI_BASE"
    echo "  docker-compose up -d"
    echo "  python examples/quickstart/quickstart_neo4j.py"
    echo ""
    echo -e "${GRAY}Press any key to return...${NC}"
    read -n 1
    initial_display
}

# Show help
show_help() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}                 HERO CORE HELP                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${WHITE}Keyboard Commands:${NC}"
    echo "  G - Show Graphiti details"
    echo "  N - Open Neo4j browser (http://localhost:7474)"
    echo "  D - Show Docker containers"
    echo "  L - View activity logs"
    echo "  H - Show this help"
    echo "  R - Force refresh display"
    echo "  Q - Quit dashboard"
    echo ""
    echo -e "${WHITE}Sections:${NC}"
    echo "  • AI Systems - Claude, Qwen, Gemini, VS Code status"
    echo "  • Chimera KB - Knowledge base with Graphiti engine"
    echo "  • System Metrics - CPU, Memory, Docker, Network"
    echo "  • Activity - Real-time processing indicators"
    echo ""
    echo -e "${WHITE}Configuration:${NC}"
    echo "  Dashboard Home: $HERO_HOME"
    echo "  Log File: $HERO_LOG"
    echo "  Cache Directory: $HERO_CACHE"
    echo ""
    echo -e "${GRAY}Press any key to return...${NC}"
    read -n 1
    initial_display
}

# Show Docker containers
show_docker() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${WHITE}              DOCKER CONTAINERS                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if docker ps 2>/dev/null; then
        echo ""
        echo -e "${GREEN}Active containers listed above${NC}"
    else
        echo -e "${YELLOW}No Docker containers running or Docker not accessible${NC}"
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
    update_ai_section
    update_chimera_section
    update_system_section
    update_activity_section
    draw_status_bar
    
    # Reset cursor position
    move_cursor 27 1
}

# Main loop
main() {
    init
    log_event "Hero Core started"
    initial_display
    
    while true; do
        update_display
        
        # Read with timeout
        if read -t $REFRESH_RATE -n 1 key 2>/dev/null; then
            case $key in
                g|G)
                    show_graphiti_details
                    ;;
                n|N)
                    echo -e "\n${YELLOW}Opening Neo4j Browser...${NC}"
                    open "http://localhost:7474" 2>/dev/null || echo "Neo4j not accessible"
                    ;;
                d|D)
                    show_docker
                    ;;
                l|L)
                    clear
                    echo -e "${CYAN}Recent Activity Log:${NC}"
                    tail -50 "$HERO_LOG" | less
                    initial_display
                    ;;
                h|H)
                    show_help
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