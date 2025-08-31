#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD CONTROL CENTER
# Master control script for all Hero/Nexus dashboard variations
# ═══════════════════════════════════════════════════════════════════════════════

# Colors
CYAN='\033[38;2;93;173;226m'
GREEN='\033[38;2;46;204;113m'
YELLOW='\033[38;2;241;196;15m'
RED='\033[38;2;231;76;60m'
MAGENTA='\033[38;2;199;125;255m'
WHITE='\033[38;5;255m'
NC='\033[0m'
BOLD='\033[1m'

# Dashboard directory (configurable via environment variable)
DASHBOARD_DIR="${HERO_DASHBOARD_DIR:-/Users/rudlord/Hero_dashboard}"

# Function to stop all dashboards
stop_all() {
    echo -e "${YELLOW}Stopping all dashboard processes...${NC}"
    pkill -f "hero_dashboard" 2>/dev/null
    pkill -f "nexus_dashboard" 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ All dashboards stopped${NC}"
}

# Function to check running dashboards
check_status() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}║     ${WHITE}${BOLD}DASHBOARD STATUS CHECK${NC}${CYAN}                       ║${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    local count=$(pgrep -f "dashboard" 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$count" -gt 0 ]; then
        echo -e "${GREEN}Found $count dashboard process(es) running:${NC}"
        ps aux | grep -E "hero_dashboard|nexus_dashboard" | grep -v grep | grep -v dashboard_control | while read line; do
            pid=$(echo "$line" | awk '{print $2}')
            script=$(echo "$line" | awk '{print $12}' | xargs basename)
            echo -e "  ${WHITE}PID $pid${NC}: $script"
        done
    else
        echo -e "${YELLOW}No dashboards currently running${NC}"
    fi
    echo ""
}

# Function to list available dashboards
list_dashboards() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}║     ${WHITE}${BOLD}AVAILABLE DASHBOARDS${NC}${CYAN}                          ║${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${MAGENTA}PRIMARY:${NC}"
    echo -e "  ${WHITE}H)${NC} HERO CORE          - ${GREEN}★ UNIFIED COMMAND CENTRE ★${NC}"
    echo ""
    
    echo -e "${CYAN}Alternative Dashboards:${NC}"
    echo -e "  ${WHITE}1)${NC} Nexus Dashboard      - Clean, no conflicts"
    echo -e "  ${WHITE}2)${NC} Hero Smooth         - Flicker-free updates"
    echo -e "  ${WHITE}3)${NC} Hero Graphiti       - Knowledge graph focus"
    echo ""
    
    echo -e "${YELLOW}Development/Testing:${NC}"
    echo -e "  ${WHITE}4)${NC} Hero Enhanced       - Chimera KB features"
    echo -e "  ${WHITE}5)${NC} Hero Unified        - All systems integrated"
    echo -e "  ${WHITE}6)${NC} Hero Integrated     - Latest development"
    echo ""
    
    echo -e "${CYAN}Utilities:${NC}"
    echo -e "  ${WHITE}S)${NC} Status - Check running dashboards"
    echo -e "  ${WHITE}K)${NC} Kill   - Stop all dashboards"
    echo -e "  ${WHITE}Q)${NC} Quit   - Exit control center"
    echo ""
}

# Function to launch dashboard
launch_dashboard() {
    local script="$1"
    local name="$2"
    
    if [ ! -f "$DASHBOARD_DIR/$script" ]; then
        echo -e "${RED}Error: $script not found${NC}"
        return 1
    fi
    
    # Stop any running dashboards first
    stop_all
    
    echo -e "${GREEN}Launching $name...${NC}"
    
    # Make sure it's executable
    chmod +x "$DASHBOARD_DIR/$script"
    
    # Launch in background but keep output visible
    exec "$DASHBOARD_DIR/$script"
}

# Main menu
main() {
    clear
    
    while true; do
        list_dashboards
        
        echo -n -e "${WHITE}Select option: ${NC}"
        read -n 1 choice
        echo ""
        echo ""
        
        case $choice in
            h|H)
                launch_dashboard "launch_hero.sh" "HERO CORE"
                ;;
            1)
                launch_dashboard "nexus_launcher.sh" "Nexus Dashboard"
                ;;
            2)
                launch_dashboard "hero_dashboard_smooth.sh" "Hero Smooth Dashboard"
                ;;
            3)
                launch_dashboard "hero_dashboard_graphiti.sh" "Hero Graphiti Dashboard"
                ;;
            4)
                launch_dashboard "hero_dashboard_enhanced.sh" "Hero Enhanced Dashboard"
                ;;
            5)
                launch_dashboard "launch_unified.sh" "Hero Unified Dashboard"
                ;;
            6)
                launch_dashboard "hero_dashboard_integrated.sh" "Hero Integrated Dashboard"
                ;;
            s|S)
                check_status
                echo "Press any key to continue..."
                read -n 1
                clear
                ;;
            k|K)
                stop_all
                echo "Press any key to continue..."
                read -n 1
                clear
                ;;
            q|Q)
                echo -e "${CYAN}Exiting Dashboard Control Center${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                sleep 1
                clear
                ;;
        esac
    done
}

# Handle arguments
case "${1:-}" in
    stop)
        stop_all
        ;;
    status)
        check_status
        ;;
    hero)
        launch_dashboard "launch_hero.sh" "HERO CORE"
        ;;
    nexus)
        launch_dashboard "nexus_launcher.sh" "Nexus Dashboard"
        ;;
    smooth)
        launch_dashboard "hero_dashboard_smooth.sh" "Hero Smooth Dashboard"
        ;;
    graphiti)
        launch_dashboard "hero_dashboard_graphiti.sh" "Hero Graphiti Dashboard"
        ;;
    *)
        main
        ;;
esac