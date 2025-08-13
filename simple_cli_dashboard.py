#!/usr/bin/env python3
"""
Simple CLI Dashboard for Hero Command Centre
Real-time display of agent status and coordination data
"""

import json
import os
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

class CLIDashboard:
    def __init__(self):
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.running = True
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        self.running = False
        
    def read_json_file(self, filename):
        """Read JSON file with error handling"""
        file_path = self.cache_dir / filename
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            return {}
        return {}
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def display_header(self):
        """Display dashboard header"""
        print("╭─" + "─" * 68 + "─╮")
        print("│" + " " * 12 + "🚀 HERO COMMAND CENTRE - LIVE DASHBOARD" + " " * 15 + "│")
        print("│" + " " * 15 + f"Port: 8080 │ {datetime.now().strftime('%H:%M:%S')}" + " " * 20 + "│")
        print("├─" + "─" * 68 + "─┤")
        
    def display_chimera_team(self, agent_data):
        """Display Chimera Project team status"""
        agents = agent_data.get('agents', {})
        project_info = agent_data.get('project_info', {})
        
        print(f"│ 🎯 PROJECT: {project_info.get('name', 'Architecture Upgrade')}" + " " * 20 + "│")
        print(f"│ Phase: {project_info.get('phase', 'implementation').title()}" + " " * 40 + "│")
        print("│" + " " * 70 + "│")
        
        # Team Lead
        architect = None
        for agent_id, agent in agents.items():
            if agent.get('pid') == 1181:
                architect = agent
                break
                
        if architect:
            status_color = "🟢" if architect['status'] == 'active' else "🟡" if architect['status'] == 'busy' else "🔴"
            print(f"│ 👑 TEAM LEAD: {architect['agent_name']} (PID {architect['pid']})" + " " * 15 + "│")
            print(f"│    Status: {status_color} {architect['status'].upper()}" + " " * 35 + "│")
            print(f"│    Tasks: {architect['performance']['tasks_completed']}/1 Complete" + " " * 30 + "│")
            print("│" + " " * 70 + "│")
        
        # Coding Team
        coders = []
        for agent_id, agent in agents.items():
            if agent.get('pid') in [88050, 57730]:
                coders.append(agent)
                
        if coders:
            print("│ ⚡ CODING TEAM:" + " " * 52 + "│")
            for coder in coders:
                status_color = "🟢" if coder['status'] == 'active' else "🟡" if coder['status'] == 'busy' else "🔴"
                task = coder.get('current_task', 'Ready for tasks')[:25]
                print(f"│   {status_color} {coder['agent_name']} (PID {coder['pid']}): {task}" + " " * (25 - len(task)) + "│")
            print("│" + " " * 70 + "│")
        
        # Support Team
        support = []
        for agent_id, agent in agents.items():
            if agent.get('pid') in [89852, 95867]:
                support.append(agent)
                
        if support:
            print("│ 🔧 SUPPORT TEAM:" + " " * 50 + "│")
            for member in support:
                status_color = "🟢" if member['status'] == 'active' else "🟡" if member['status'] == 'busy' else "🔴"
                task = member.get('current_task', 'Ready')[:25]
                print(f"│   {status_color} {member['agent_name']} (PID {member['pid']}): {task}" + " " * (25 - len(task)) + "│")
            print("│" + " " * 70 + "│")
            
    def display_metrics(self, langsmith_data, coordination_data):
        """Display performance metrics"""
        success_rate = langsmith_data.get('success_rate', 0) * 100
        total_traces = langsmith_data.get('total_traces', 0)
        session_duration = langsmith_data.get('session_duration', '0:00:00')
        
        coord_stats = coordination_data.get('coordination_stats', {})
        load_balance = coord_stats.get('load_balancing_score', 0) * 100
        
        print("│ 📊 PERFORMANCE METRICS:" + " " * 44 + "│")
        print(f"│   Success Rate: {success_rate:.1f}% │ Total Traces: {total_traces}" + " " * 20 + "│")
        print(f"│   Session: {session_duration} │ Load Balance: {load_balance:.0f}%" + " " * 15 + "│")
        
    def display_footer(self):
        """Display dashboard footer"""
        print("╰─" + "─" * 68 + "─╯")
        print("Press Ctrl+C to exit")
        
    def run(self):
        """Main dashboard loop"""
        print("Starting Hero Command Centre CLI Dashboard...")
        print("Monitoring live agent data...")
        time.sleep(2)
        
        while self.running:
            try:
                self.clear_screen()
                
                # Read data
                agent_data = self.read_json_file("agent_runtime_status.json")
                coordination_data = self.read_json_file("agent_coordination.json")
                langsmith_data = self.read_json_file("langsmith_stats.json")
                
                # Display dashboard
                self.display_header()
                self.display_chimera_team(agent_data)
                self.display_metrics(langsmith_data, coordination_data)
                self.display_footer()
                
                # Update every 5 seconds
                time.sleep(5)
                
            except Exception as e:
                print(f"Error updating dashboard: {e}")
                time.sleep(5)
                
        print("\nDashboard stopped.")

if __name__ == "__main__":
    dashboard = CLIDashboard()
    dashboard.run()