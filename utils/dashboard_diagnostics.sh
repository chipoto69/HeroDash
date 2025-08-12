#!/bin/bash

# Dashboard Diagnostics - Quick health check

CYAN='\033[38;2;93;173;226m'
GREEN='\033[38;2;46;204;113m'
YELLOW='\033[38;2;241;196;15m'
RED='\033[38;2;231;76;60m'
WHITE='\033[38;5;255m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${WHITE}DASHBOARD DIAGNOSTICS${NC}${CYAN}                         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check AI Systems
echo -e "${CYAN}AI SYSTEMS:${NC}"
claude_count=$(pgrep -f "claude" 2>/dev/null | wc -l | tr -d ' ')
[ "$claude_count" -gt 0 ] && echo -e "  ${GREEN}✓${NC} Claude: $claude_count instances" || echo -e "  ${YELLOW}○${NC} Claude: offline"

pgrep -f "qwen" &>/dev/null && echo -e "  ${GREEN}✓${NC} Qwen-code: running" || echo -e "  ${YELLOW}○${NC} Qwen-code: not running"

vscode_count=$(pgrep -f "Code Helper" 2>/dev/null | wc -l | tr -d ' ')
[ "$vscode_count" -gt 0 ] && echo -e "  ${GREEN}✓${NC} VS Code: $vscode_count helpers" || echo -e "  ${YELLOW}○${NC} VS Code: not running"

echo ""

# Check Knowledge Systems
echo -e "${CYAN}KNOWLEDGE SYSTEMS:${NC}"
pgrep -f "neo4j" &>/dev/null && echo -e "  ${GREEN}✓${NC} Neo4j/Graphiti: online" || echo -e "  ${YELLOW}○${NC} Neo4j: offline"
pgrep -f "redis-server" &>/dev/null && echo -e "  ${GREEN}✓${NC} Redis: active" || echo -e "  ${YELLOW}○${NC} Redis: offline"
[ -f "$HOME/.entitydb/entities.db" ] && echo -e "  ${GREEN}✓${NC} EntityDB: available" || echo -e "  ${YELLOW}○${NC} EntityDB: not found"
pgrep -f "chroma" &>/dev/null && echo -e "  ${GREEN}✓${NC} ChromaDB: running" || echo -e "  ${YELLOW}○${NC} ChromaDB: offline"

echo ""

# Check Docker
echo -e "${CYAN}INFRASTRUCTURE:${NC}"
docker_count=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
if [ "$docker_count" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Docker: $docker_count containers"
    docker ps 2>/dev/null | grep nats &>/dev/null && echo -e "  ${GREEN}✓${NC} NATS: in Docker" || echo -e "  ${YELLOW}○${NC} NATS: not found"
else
    echo -e "  ${YELLOW}○${NC} Docker: no containers"
fi

echo ""

# Check Directories
echo -e "${CYAN}PROJECT PATHS:${NC}"
[ -d "/Users/rudlord/q3/Frontline" ] && echo -e "  ${GREEN}✓${NC} Frontline project" || echo -e "  ${RED}✗${NC} Frontline not found"
[ -d "/Users/rudlord/q3/0_MEMORY/graphiti" ] && echo -e "  ${GREEN}✓${NC} Graphiti project" || echo -e "  ${RED}✗${NC} Graphiti not found"

echo ""

# Check Dashboard Files
echo -e "${CYAN}DASHBOARD FILES:${NC}"
for file in nexus_dashboard.sh nexus_launcher.sh hero_dashboard_smooth.sh hero_dashboard_graphiti.sh dashboard_control.sh; do
    if [ -f "/Users/rudlord/Hero_dashboard/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file missing"
    fi
done

echo ""

# Check Running Dashboards
echo -e "${CYAN}RUNNING DASHBOARDS:${NC}"
running=$(ps aux | grep -E "nexus_dashboard|hero_dashboard" | grep -v grep | grep -v diagnostics | wc -l | tr -d ' ')
if [ "$running" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠${NC} $running dashboard(s) currently running:"
    ps aux | grep -E "nexus_dashboard|hero_dashboard" | grep -v grep | grep -v diagnostics | while read line; do
        script=$(echo "$line" | awk '{print $12}' | xargs basename)
        pid=$(echo "$line" | awk '{print $2}')
        echo -e "    PID $pid: $script"
    done
else
    echo -e "  ${GREEN}✓${NC} No dashboards running (clean state)"
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════${NC}"
echo -e "Run ${WHITE}./dashboard_control.sh${NC} to launch a dashboard"
echo -e "${CYAN}════════════════════════════════════════════════════${NC}"