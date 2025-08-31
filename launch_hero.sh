#!/bin/bash

# HERO CORE LAUNCHER
# Ensures clean start with no conflicts

# Source environment variables if .env file exists
if [ -f "$(dirname "$0")/.env" ]; then
    set -a  # automatically export all variables
    source "$(dirname "$0")/.env"
    set +a
fi

CYAN='\033[38;2;93;173;226m'
GREEN='\033[38;2;46;204;113m'
YELLOW='\033[38;2;241;196;15m'
WHITE='\033[38;5;255m'
GRAY='\033[38;5;245m'
NC='\033[0m'

clear

echo -e "${CYAN}"
echo "    ██╗  ██╗███████╗██████╗  ██████╗      ██████╗ ██████╗ ██████╗ ███████╗"
echo "    ██║  ██║██╔════╝██╔══██╗██╔═══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝"
echo "    ███████║█████╗  ██████╔╝██║   ██║    ██║     ██║   ██║██████╔╝█████╗  "
echo "    ██╔══██║██╔══╝  ██╔══██╗██║   ██║    ██║     ██║   ██║██╔══██╗██╔══╝  "
echo "    ██║  ██║███████╗██║  ██║╚██████╔╝    ╚██████╗╚██████╔╝██║  ██║███████╗"
echo "    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝"
echo -e "${NC}"
echo "                              ${GRAY}[ by Quantropy ]${NC}"
echo ""

echo -e "${YELLOW}Initializing Hero Core...${NC}"
echo ""

# Stop any existing dashboards
if pgrep -f "dashboard" &>/dev/null; then
    echo -e "${YELLOW}Stopping existing dashboards...${NC}"
    pkill -f "hero_dashboard" 2>/dev/null
    pkill -f "nexus_dashboard" 2>/dev/null
    sleep 1
    echo -e "${GREEN}✓ Clean slate achieved${NC}"
fi

# Quick system check
echo -e "${CYAN}System Check:${NC}"

# AI Systems
claude_count=$(pgrep -f "claude" 2>/dev/null | wc -l | tr -d ' ')
[ "$claude_count" -gt 0 ] && echo -e "  ${GREEN}✓${NC} Claude: $claude_count instances" || echo -e "  ${GRAY}○${NC} Claude: offline"

# Knowledge Base
pgrep -f "neo4j" &>/dev/null && echo -e "  ${GREEN}✓${NC} Neo4j/Graphiti: online" || echo -e "  ${GRAY}○${NC} Neo4j: offline"
pgrep -f "redis-server" &>/dev/null && echo -e "  ${GREEN}✓${NC} Redis: active" || echo -e "  ${GRAY}○${NC} Redis: offline"

# Docker
docker_count=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
[ "$docker_count" -gt 0 ] && echo -e "  ${GREEN}✓${NC} Docker: $docker_count containers" || echo -e "  ${GRAY}○${NC} Docker: no containers"

echo ""
echo -e "${CYAN}Launching Hero Core Command Centre...${NC}"
sleep 1

# Launch Hero Core
HERO_DASHBOARD_DIR="${HERO_DASHBOARD_DIR:-/Users/rudlord/Hero_dashboard}"
exec "$HERO_DASHBOARD_DIR/hero_core.sh"