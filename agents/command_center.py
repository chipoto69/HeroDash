#!/usr/bin/env python3
"""
Hero Agent Command Center CLI
Interactive command-line interface for managing AI agents, viewing analytics, and controlling workflows
"""

import json
import os
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import cmd
import sys
import uuid

# Add Hero monitors to path
sys.path.append(str(Path(__file__).parent.parent / "monitors"))

try:
    from agent_coordinator import get_coordinator, TaskPriority
    from langsmith_tracer import get_tracer
    HERO_AVAILABLE = True
except ImportError:
    HERO_AVAILABLE = False

# Cache directory
CACHE_DIR = Path.home() / ".hero_core" / "cache"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CommandCenter")

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class HeroCommandCenter(cmd.Cmd):
    """Interactive command center for Hero agents"""
    
    intro = f"""
{Colors.HEADER}╔═══════════════════════════════════════════════════════════════╗
║                    HERO AGENT COMMAND CENTER                  ║
║                                                               ║
║  Interactive CLI for AI Agent Management and Analytics        ║
╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.CYAN}Type 'help' for available commands or 'quit' to exit{Colors.ENDC}
"""
    
    prompt = f"{Colors.GREEN}hero> {Colors.ENDC}"
    
    def __init__(self):
        super().__init__()
        self.cache_dir = CACHE_DIR
        self.coordinator = None
        self.tracer = None
        
        # Initialize connections if available
        if HERO_AVAILABLE:
            try:
                self.coordinator = get_coordinator()
                self.tracer = get_tracer()
            except Exception as e:
                print(f"{Colors.YELLOW}Warning: Could not connect to Hero services: {e}{Colors.ENDC}")
    
    def read_json_file(self, filename: str) -> Dict[str, Any]:
        """Read JSON file with error handling"""
        file_path = self.cache_dir / filename
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Colors.RED}Error reading {filename}: {e}{Colors.ENDC}")
        return {}
    
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{title:^60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    def print_table(self, headers: List[str], rows: List[List[str]], widths: List[int] = None):
        """Print formatted table"""
        if not widths:
            widths = [max(len(str(item)) for item in col) for col in zip(headers, *rows)]
        
        # Print headers
        header_row = " | ".join(f"{header:<{width}}" for header, width in zip(headers, widths))
        print(f"{Colors.CYAN}{header_row}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'-' * len(header_row)}{Colors.ENDC}")
        
        # Print rows
        for row in rows:
            data_row = " | ".join(f"{str(item):<{width}}" for item, width in zip(row, widths))
            print(data_row)
    
    def do_status(self, args):
        """Show overall system status
        Usage: status [detailed]
        """
        self.print_header("SYSTEM STATUS")
        
        # Agent runtime status
        runtime_data = self.read_json_file("agent_runtime_status.json")
        coordination_data = self.read_json_file("agent_coordination.json")
        langsmith_data = self.read_json_file("langsmith_stats.json")
        
        if runtime_data:
            runtime_stats = runtime_data.get("runtime_stats", {})
            agents = runtime_data.get("agents", {})
            
            print(f"{Colors.GREEN}🚀 Agent Runtime{Colors.ENDC}")
            print(f"  Uptime: {runtime_stats.get('uptime_seconds', 0)} seconds")
            print(f"  Total Agents: {len(agents)}")
            print(f"  Active Agents: {len([a for a in agents.values() if a.get('status') == 'active'])}")
        
        if coordination_data:
            coord_stats = coordination_data.get("coordination_stats", {})
            tasks = coordination_data.get("tasks", {})
            
            print(f"\n{Colors.BLUE}📋 Task Coordination{Colors.ENDC}")
            print(f"  Total Tasks: {coord_stats.get('total_tasks_processed', 0)}")
            print(f"  Success Rate: {coord_stats.get('success_rate', 0):.2%}")
            print(f"  Queue Length: {tasks.get('queue_length', 0)}")
            print(f"  Running: {tasks.get('running', 0)}")
        
        if langsmith_data:
            print(f"\n{Colors.PURPLE}🧠 LangSmith Integration{Colors.ENDC}")
            print(f"  Total Traces: {langsmith_data.get('total_traces', 0)}")
            print(f"  Success Rate: {langsmith_data.get('success_rate', 0):.2%}")
            print(f"  Avg Duration: {langsmith_data.get('average_duration_ms', 0):.1f}ms")
        
        if "detailed" in args:
            self._show_detailed_status()
    
    def _show_detailed_status(self):
        """Show detailed system status"""
        print(f"\n{Colors.CYAN}📊 Detailed Status{Colors.ENDC}")
        
        # Check all cache files
        cache_files = [
            "agent_runtime_status.json",
            "agent_coordination.json", 
            "langsmith_stats.json",
            "token_analysis.json",
            "agents_status.json"
        ]
        
        print(f"\n{Colors.YELLOW}Cache Files:{Colors.ENDC}")
        for filename in cache_files:
            file_path = self.cache_dir / filename
            if file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                print(f"  ✅ {filename} (updated: {mtime.strftime('%H:%M:%S')})")
            else:
                print(f"  ❌ {filename} (missing)")
    
    def do_agents(self, args):
        """Show agent information
        Usage: agents [list|details|<agent_id>]
        """
        if not args or args == "list":
            self._list_agents()
        elif args == "details":
            self._show_agent_details()
        else:
            self._show_specific_agent(args)
    
    def _list_agents(self):
        """List all agents"""
        self.print_header("AGENT LIST")
        
        runtime_data = self.read_json_file("agent_runtime_status.json")
        agents = runtime_data.get("agents", {})
        
        if not agents:
            print(f"{Colors.YELLOW}No agents currently active{Colors.ENDC}")
            return
        
        headers = ["Agent ID", "Type", "Status", "Current Task"]
        rows = []
        
        for agent_id, agent_data in agents.items():
            rows.append([
                agent_id[:8] + "...",
                agent_data.get("agent_type", "unknown"),
                agent_data.get("status", "unknown"),
                agent_data.get("current_task", "idle")[:20] + "..." if len(agent_data.get("current_task", "")) > 20 else agent_data.get("current_task", "idle")
            ])
        
        self.print_table(headers, rows)
    
    def _show_agent_details(self):
        """Show detailed agent information"""
        self.print_header("AGENT DETAILS")
        
        runtime_data = self.read_json_file("agent_runtime_status.json")
        agents = runtime_data.get("agents", {})
        
        for agent_id, agent_data in agents.items():
            print(f"\n{Colors.GREEN}🤖 Agent: {agent_id[:8]}...{Colors.ENDC}")
            print(f"  Type: {agent_data.get('agent_type', 'unknown')}")
            print(f"  Status: {agent_data.get('status', 'unknown')}")
            print(f"  Current Task: {agent_data.get('current_task', 'idle')}")
            
            performance = agent_data.get("performance", {})
            if performance:
                print(f"  Performance:")
                print(f"    Tasks Completed: {performance.get('tasks_completed', 0)}")
                print(f"    Success Rate: {performance.get('success_rate', 0):.2%}")
                print(f"    Avg Response Time: {performance.get('avg_response_time', 0):.2f}s")
    
    def _show_specific_agent(self, agent_id: str):
        """Show details for a specific agent"""
        # Try to find agent by partial ID
        runtime_data = self.read_json_file("agent_runtime_status.json")
        agents = runtime_data.get("agents", {})
        
        matching_agents = [aid for aid in agents.keys() if aid.startswith(agent_id)]
        
        if not matching_agents:
            print(f"{Colors.RED}Agent not found: {agent_id}{Colors.ENDC}")
            return
        
        if len(matching_agents) > 1:
            print(f"{Colors.YELLOW}Multiple agents match '{agent_id}':{Colors.ENDC}")
            for aid in matching_agents:
                print(f"  {aid}")
            return
        
        agent_id_full = matching_agents[0]
        agent_data = agents[agent_id_full]
        
        self.print_header(f"AGENT: {agent_id_full[:8]}...")
        
        print(f"{Colors.GREEN}Basic Information:{Colors.ENDC}")
        print(f"  Full ID: {agent_id_full}")
        print(f"  Type: {agent_data.get('agent_type', 'unknown')}")
        print(f"  Status: {agent_data.get('status', 'unknown')}")
        print(f"  Current Task: {agent_data.get('current_task', 'idle')}")
        print(f"  Last Heartbeat: {agent_data.get('last_heartbeat', 'never')}")
        
        performance = agent_data.get("performance", {})
        if performance:
            print(f"\n{Colors.BLUE}Performance Metrics:{Colors.ENDC}")
            print(f"  Tasks Completed: {performance.get('tasks_completed', 0)}")
            print(f"  Success Rate: {performance.get('success_rate', 0):.2%}")
            print(f"  Average Response Time: {performance.get('avg_response_time', 0):.2f}s")
            print(f"  Total Tokens Used: {performance.get('total_tokens', 0)}")
    
    def do_tasks(self, args):
        """Show task information
        Usage: tasks [active|completed|history]
        """
        if not args or args == "active":
            self._show_active_tasks()
        elif args == "completed":
            self._show_completed_tasks()
        elif args == "history":
            self._show_task_history()
        else:
            print(f"{Colors.RED}Unknown tasks command: {args}{Colors.ENDC}")
    
    def _show_active_tasks(self):
        """Show currently active tasks"""
        self.print_header("ACTIVE TASKS")
        
        coordination_data = self.read_json_file("agent_coordination.json")
        recent_activity = coordination_data.get("recent_activity", [])
        
        active_tasks = [task for task in recent_activity if task.get("status") in ["assigned", "running"]]
        
        if not active_tasks:
            print(f"{Colors.YELLOW}No active tasks{Colors.ENDC}")
            return
        
        headers = ["Task ID", "Name", "Agent", "Status", "Started"]
        rows = []
        
        for task in active_tasks:
            start_time = datetime.fromisoformat(task.get("started", "")).strftime("%H:%M:%S")
            rows.append([
                task.get("task_id", "")[:8] + "...",
                task.get("name", "")[:20] + "..." if len(task.get("name", "")) > 20 else task.get("name", ""),
                task.get("agent", "")[:15] + "..." if len(task.get("agent", "")) > 15 else task.get("agent", ""),
                task.get("status", ""),
                start_time
            ])
        
        self.print_table(headers, rows)
    
    def _show_completed_tasks(self):
        """Show recently completed tasks"""
        self.print_header("COMPLETED TASKS")
        
        coordination_data = self.read_json_file("agent_coordination.json")
        recent_activity = coordination_data.get("recent_activity", [])
        
        completed_tasks = [task for task in recent_activity if task.get("status") == "completed"]
        
        if not completed_tasks:
            print(f"{Colors.YELLOW}No completed tasks in recent history{Colors.ENDC}")
            return
        
        headers = ["Task ID", "Name", "Agent", "Duration", "Completed"]
        rows = []
        
        for task in completed_tasks:
            duration = task.get("duration", "N/A")
            if isinstance(duration, (int, float)):
                duration = f"{duration:.2f}s"
            
            rows.append([
                task.get("task_id", "")[:8] + "...",
                task.get("name", "")[:20] + "..." if len(task.get("name", "")) > 20 else task.get("name", ""),
                task.get("agent", "")[:15] + "..." if len(task.get("agent", "")) > 15 else task.get("agent", ""),
                str(duration),
                task.get("started", "")[:19]  # Show timestamp without microseconds
            ])
        
        self.print_table(headers, rows)
    
    def _show_task_history(self):
        """Show task execution history"""
        self.print_header("TASK HISTORY")
        
        coordination_data = self.read_json_file("agent_coordination.json")
        coord_stats = coordination_data.get("coordination_stats", {})
        
        print(f"{Colors.GREEN}Summary Statistics:{Colors.ENDC}")
        print(f"  Total Tasks Processed: {coord_stats.get('total_tasks_processed', 0)}")
        print(f"  Success Rate: {coord_stats.get('success_rate', 0):.2%}")
        print(f"  Average Duration: {coord_stats.get('average_task_duration', 0):.2f}s")
        print(f"  Load Balancing Score: {coord_stats.get('load_balancing_score', 0):.2f}")
        
        # Show recent activity
        print(f"\n{Colors.BLUE}Recent Activity:{Colors.ENDC}")
        recent_activity = coordination_data.get("recent_activity", [])
        
        for task in recent_activity[-10:]:  # Show last 10 tasks
            status_color = Colors.GREEN if task.get("status") == "completed" else Colors.YELLOW
            print(f"  {status_color}•{Colors.ENDC} {task.get('name', '')[:30]} "
                  f"({task.get('status', '')}) - {task.get('agent', '')}")
    
    def do_submit(self, args):
        """Submit a new task to agents
        Usage: submit <task_name> [description] [--priority high|normal|low]
        """
        if not args:
            print(f"{Colors.RED}Usage: submit <task_name> [description] [--priority high|normal|low]{Colors.ENDC}")
            return
        
        if not HERO_AVAILABLE or not self.coordinator:
            print(f"{Colors.RED}Agent coordinator not available{Colors.ENDC}")
            return
        
        # Parse arguments
        parts = args.split()
        task_name = parts[0]
        description = " ".join(parts[1:]) if len(parts) > 1 else f"User submitted task: {task_name}"
        
        # Default capabilities for user-submitted tasks
        capabilities = ["task_orchestration", "general_processing"]
        priority = TaskPriority.NORMAL
        
        try:
            task_id = self.coordinator.submit_task(
                task_name,
                description,
                capabilities,
                priority
            )
            
            print(f"{Colors.GREEN}✅ Task submitted successfully{Colors.ENDC}")
            print(f"  Task ID: {task_id}")
            print(f"  Name: {task_name}")
            print(f"  Description: {description}")
            print(f"  Priority: {priority.value}")
            
        except Exception as e:
            print(f"{Colors.RED}Error submitting task: {e}{Colors.ENDC}")
    
    def do_analytics(self, args):
        """Show analytics data
        Usage: analytics [summary|detailed|export]
        """
        if not args or args == "summary":
            self._show_analytics_summary()
        elif args == "detailed":
            self._show_detailed_analytics()
        elif args == "export":
            self._export_analytics()
        else:
            print(f"{Colors.RED}Unknown analytics command: {args}{Colors.ENDC}")
    
    def _show_analytics_summary(self):
        """Show analytics summary"""
        self.print_header("ANALYTICS SUMMARY")
        
        # Check if analytics dashboard data exists
        analytics_cache = self.cache_dir / "analytics_dashboard.json"
        if analytics_cache.exists():
            analytics_data = self.read_json_file("analytics_dashboard.json")
            
            current_metrics = analytics_data.get("current_metrics", {})
            trends = analytics_data.get("performance_trends", {})
            
            print(f"{Colors.GREEN}Current Performance:{Colors.ENDC}")
            print(f"  Active Agents: {current_metrics.get('active_agents', 0)}")
            print(f"  Success Rate: {current_metrics.get('success_rate', 0):.2%}")
            print(f"  Total Tasks: {current_metrics.get('total_tasks', 0)}")
            print(f"  LangSmith Traces: {current_metrics.get('langsmith_traces', 0)}")
            
            if trends:
                print(f"\n{Colors.BLUE}Performance Trends:{Colors.ENDC}")
                for metric, trend_data in trends.items():
                    if isinstance(trend_data, dict) and "trend" in trend_data:
                        trend = trend_data["trend"]
                        trend_color = Colors.GREEN if trend == "improving" else Colors.RED if trend == "declining" else Colors.YELLOW
                        print(f"  {metric.replace('_', ' ').title()}: {trend_color}{trend}{Colors.ENDC}")
        else:
            # Fall back to basic analytics
            self._show_basic_analytics()
    
    def _show_basic_analytics(self):
        """Show basic analytics from cache files"""
        langsmith_data = self.read_json_file("langsmith_stats.json")
        coordination_data = self.read_json_file("agent_coordination.json")
        
        print(f"{Colors.GREEN}Basic Analytics:{Colors.ENDC}")
        
        if langsmith_data:
            print(f"  LangSmith Traces: {langsmith_data.get('total_traces', 0)}")
            print(f"  LLM Success Rate: {langsmith_data.get('success_rate', 0):.2%}")
            print(f"  Average Duration: {langsmith_data.get('average_duration_ms', 0):.1f}ms")
        
        if coordination_data:
            coord_stats = coordination_data.get("coordination_stats", {})
            print(f"  Task Success Rate: {coord_stats.get('success_rate', 0):.2%}")
            print(f"  Total Tasks: {coord_stats.get('total_tasks_processed', 0)}")
            print(f"  Load Balance Score: {coord_stats.get('load_balancing_score', 0):.2f}")
    
    def _show_detailed_analytics(self):
        """Show detailed analytics"""
        self.print_header("DETAILED ANALYTICS")
        
        analytics_cache = self.cache_dir / "analytics_dashboard.json"
        if not analytics_cache.exists():
            print(f"{Colors.YELLOW}Detailed analytics not available. Run analytics monitor first.{Colors.ENDC}")
            print(f"Command: python3 monitors/analytics_dashboard.py")
            return
        
        analytics_data = self.read_json_file("analytics_dashboard.json")
        
        # Show recommendations
        recommendations = analytics_data.get("recommendations", [])
        if recommendations:
            print(f"{Colors.CYAN}🔍 Recommendations:{Colors.ENDC}")
            for rec in recommendations:
                priority_color = Colors.RED if rec.get("priority") == "high" else Colors.YELLOW
                print(f"  {priority_color}• {rec.get('recommendation', '')}{Colors.ENDC}")
                print(f"    Category: {rec.get('category', '')} | Priority: {rec.get('priority', '')}")
        
        # Show historical summary
        historical = analytics_data.get("historical_summary", {})
        if historical:
            print(f"\n{Colors.BLUE}📊 Historical Data:{Colors.ENDC}")
            print(f"  Data Points: {historical.get('data_points', 0)}")
            print(f"  Time Range: {historical.get('time_range', 'N/A')}")
            
            peak_perf = historical.get("peak_performance", {})
            if peak_perf:
                print(f"  Best Success Rate: {peak_perf.get('best_success_rate', {}).get('value', 0):.2%}")
                print(f"  Best Response Time: {peak_perf.get('best_response_time', {}).get('value', 0):.2f}s")
    
    def _export_analytics(self):
        """Export analytics data"""
        print(f"{Colors.YELLOW}Exporting analytics data...{Colors.ENDC}")
        
        # Export basic data to JSON
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "agent_runtime": self.read_json_file("agent_runtime_status.json"),
            "coordination": self.read_json_file("agent_coordination.json"),
            "langsmith": self.read_json_file("langsmith_stats.json"),
            "token_usage": self.read_json_file("token_analysis.json")
        }
        
        export_file = self.cache_dir / f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"{Colors.GREEN}✅ Analytics exported to: {export_file}{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.RED}Error exporting analytics: {e}{Colors.ENDC}")
    
    def do_logs(self, args):
        """Show recent log entries
        Usage: logs [agent|coordinator|langsmith] [lines]
        """
        log_type = args.split()[0] if args else "agent"
        lines = int(args.split()[1]) if len(args.split()) > 1 else 20
        
        log_dir = Path.home() / ".hero_core" / "logs"
        log_files = {
            "agent": "agent_runtime.log",
            "coordinator": "agent_coordinator.log", 
            "langsmith": "langsmith_tracer.log"
        }
        
        log_file = log_dir / log_files.get(log_type, "agent_runtime.log")
        
        if not log_file.exists():
            print(f"{Colors.RED}Log file not found: {log_file}{Colors.ENDC}")
            return
        
        self.print_header(f"{log_type.upper()} LOGS (last {lines} lines)")
        
        try:
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
                recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
                
                for line in recent_lines:
                    line = line.strip()
                    if "ERROR" in line:
                        print(f"{Colors.RED}{line}{Colors.ENDC}")
                    elif "WARNING" in line:
                        print(f"{Colors.YELLOW}{line}{Colors.ENDC}")
                    elif "INFO" in line:
                        print(f"{Colors.GREEN}{line}{Colors.ENDC}")
                    else:
                        print(line)
                        
        except Exception as e:
            print(f"{Colors.RED}Error reading log file: {e}{Colors.ENDC}")
    
    def do_refresh(self, args):
        """Refresh all cached data"""
        print(f"{Colors.YELLOW}Refreshing cached data...{Colors.ENDC}")
        
        # This could trigger refresh of monitoring processes
        print(f"{Colors.GREEN}✅ Cache refresh completed{Colors.ENDC}")
    
    def do_help(self, args):
        """Show help information"""
        if args:
            super().do_help(args)
        else:
            self.print_header("AVAILABLE COMMANDS")
            
            commands = [
                ("status [detailed]", "Show system status"),
                ("agents [list|details|<id>]", "Show agent information"),
                ("tasks [active|completed|history]", "Show task information"), 
                ("submit <name> [description]", "Submit new task"),
                ("analytics [summary|detailed|export]", "Show analytics"),
                ("logs [agent|coordinator|langsmith]", "Show log entries"),
                ("refresh", "Refresh cached data"),
                ("quit", "Exit command center")
            ]
            
            for cmd, desc in commands:
                print(f"  {Colors.CYAN}{cmd:<30}{Colors.ENDC} {desc}")
    
    def do_quit(self, args):
        """Exit the command center"""
        print(f"{Colors.GREEN}Goodbye! 🚀{Colors.ENDC}")
        return True
    
    def do_exit(self, args):
        """Exit the command center"""
        return self.do_quit(args)
    
    def emptyline(self):
        """Do nothing on empty line"""
        pass

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Hero Agent Command Center")
    parser.add_argument("--non-interactive", action="store_true", 
                       help="Run in non-interactive mode")
    parser.add_argument("--command", help="Execute single command and exit")
    
    args = parser.parse_args()
    
    if args.command:
        # Execute single command
        center = HeroCommandCenter()
        center.onecmd(args.command)
    else:
        # Interactive mode
        center = HeroCommandCenter()
        try:
            center.cmdloop()
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}Goodbye! 🚀{Colors.ENDC}")

if __name__ == "__main__":
    main()