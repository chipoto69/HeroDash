#!/usr/bin/env python3
"""
Hero Analytics Dashboard Monitor
Aggregates data from all Hero monitoring sources and generates comprehensive analytics
"""

import json
import csv
import sqlite3
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import statistics
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AnalyticsDashboard")

@dataclass
class KPISnapshot:
    """Key Performance Indicator snapshot"""
    timestamp: str
    active_agents: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    avg_response_time: float
    total_tokens: int
    avg_tokens_per_task: float
    system_uptime: int
    cpu_usage: float
    memory_usage: float
    langsmith_traces: int
    nats_messages: int

@dataclass
class AgentMetrics:
    """Individual agent performance metrics"""
    agent_id: str
    agent_type: str
    status: str
    tasks_completed: int
    avg_response_time: float
    success_rate: float
    total_tokens: int
    uptime: int
    last_activity: str

@dataclass
class TaskAnalytics:
    """Task execution analytics"""
    task_id: str
    task_type: str
    agent_id: str
    start_time: str
    end_time: Optional[str]
    duration: Optional[float]
    status: str
    tokens_used: int
    success: bool

class HeroAnalyticsAggregator:
    """Aggregate analytics data from all Hero monitoring sources"""
    
    def __init__(self, cache_dir: Path = None, db_path: Path = None):
        self.cache_dir = cache_dir or Path.home() / ".hero_core" / "cache"
        self.db_path = db_path or Path.home() / ".hero_core" / "analytics.db"
        self.analytics_cache = self.cache_dir / "analytics_dashboard.json"
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        logger.info(f"Analytics aggregator initialized - Cache: {self.cache_dir}, DB: {self.db_path}")
    
    def init_database(self):
        """Initialize SQLite database for historical data"""
        with sqlite3.connect(self.db_path) as conn:
            # KPI snapshots table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kpi_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    active_agents INTEGER,
                    total_tasks INTEGER,
                    completed_tasks INTEGER,
                    failed_tasks INTEGER,
                    success_rate REAL,
                    avg_response_time REAL,
                    total_tokens INTEGER,
                    avg_tokens_per_task REAL,
                    system_uptime INTEGER,
                    cpu_usage REAL,
                    memory_usage REAL,
                    langsmith_traces INTEGER,
                    nats_messages INTEGER
                )
            ''')
            
            # Agent metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    agent_type TEXT,
                    status TEXT,
                    tasks_completed INTEGER,
                    avg_response_time REAL,
                    success_rate REAL,
                    total_tokens INTEGER,
                    uptime INTEGER,
                    last_activity TEXT
                )
            ''')
            
            # Task analytics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS task_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    task_type TEXT,
                    agent_id TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration REAL,
                    status TEXT,
                    tokens_used INTEGER,
                    success BOOLEAN
                )
            ''')
            
            # Create indexes for better query performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_kpi_timestamp ON kpi_snapshots(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON agent_metrics(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_task_timestamp ON task_analytics(start_time)')
            
            conn.commit()
        
        logger.info("Database initialized successfully")
    
    def read_json_file(self, filename: str) -> Dict[str, Any]:
        """Read JSON file with error handling"""
        file_path = self.cache_dir / filename
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
        return {}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics from all sources"""
        metrics = {
            "agent_runtime": self.read_json_file("agent_runtime_status.json"),
            "coordination": self.read_json_file("agent_coordination.json"),
            "langsmith": self.read_json_file("langsmith_stats.json"),
            "token_usage": self.read_json_file("token_analysis.json"),
            "github_activity": self.read_json_file("github_activity.json"),
            "claude_usage": self.read_json_file("claude_usage.json"),
            "code_activity": self.read_json_file("code_activity.json")
        }
        return metrics
    
    def calculate_kpi_snapshot(self) -> KPISnapshot:
        """Calculate current KPI snapshot"""
        metrics = self.get_system_metrics()
        
        # Extract key metrics
        runtime = metrics.get("agent_runtime", {})
        coordination = metrics.get("coordination", {})
        langsmith = metrics.get("langsmith", {})
        token_usage = metrics.get("token_usage", {})
        
        # Calculate KPIs
        agents = runtime.get("agents", {})
        active_agents = len([a for a in agents.values() if a.get("status") == "active"])
        
        coord_stats = coordination.get("coordination_stats", {})
        total_tasks = coord_stats.get("total_tasks_processed", 0)
        success_rate = coord_stats.get("success_rate", 0.0)
        avg_duration = coord_stats.get("average_task_duration", 0.0)
        
        langsmith_traces = langsmith.get("total_traces", 0)
        
        # Token metrics
        tokens = token_usage.get("total_tokens", 0)
        avg_tokens_per_task = tokens / max(total_tasks, 1)
        
        # System metrics
        uptime = runtime.get("runtime_stats", {}).get("uptime_seconds", 0)
        
        # Task status
        task_stats = coordination.get("tasks", {})
        completed_tasks = task_stats.get("completed", 0)
        failed_tasks = total_tasks - completed_tasks if total_tasks > completed_tasks else 0
        
        return KPISnapshot(
            timestamp=datetime.now().isoformat(),
            active_agents=active_agents,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            success_rate=success_rate,
            avg_response_time=avg_duration,
            total_tokens=tokens,
            avg_tokens_per_task=avg_tokens_per_task,
            system_uptime=uptime,
            cpu_usage=0.0,  # Could integrate with psutil
            memory_usage=0.0,  # Could integrate with psutil
            langsmith_traces=langsmith_traces,
            nats_messages=0  # Could integrate with NATS monitoring
        )
    
    def get_agent_metrics(self) -> List[AgentMetrics]:
        """Get metrics for individual agents"""
        metrics = self.get_system_metrics()
        runtime = metrics.get("agent_runtime", {})
        agents = runtime.get("agents", {})
        
        agent_metrics = []
        for agent_id, agent_data in agents.items():
            metric = AgentMetrics(
                agent_id=agent_id,
                agent_type=agent_data.get("agent_type", "unknown"),
                status=agent_data.get("status", "unknown"),
                tasks_completed=agent_data.get("performance", {}).get("tasks_completed", 0),
                avg_response_time=agent_data.get("performance", {}).get("avg_response_time", 0.0),
                success_rate=agent_data.get("performance", {}).get("success_rate", 0.0),
                total_tokens=agent_data.get("performance", {}).get("total_tokens", 0),
                uptime=0,  # Could calculate from heartbeat
                last_activity=agent_data.get("last_heartbeat", "")
            )
            agent_metrics.append(metric)
        
        return agent_metrics
    
    def store_kpi_snapshot(self, snapshot: KPISnapshot):
        """Store KPI snapshot in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO kpi_snapshots (
                    timestamp, active_agents, total_tasks, completed_tasks, failed_tasks,
                    success_rate, avg_response_time, total_tokens, avg_tokens_per_task,
                    system_uptime, cpu_usage, memory_usage, langsmith_traces, nats_messages
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.timestamp, snapshot.active_agents, snapshot.total_tasks,
                snapshot.completed_tasks, snapshot.failed_tasks, snapshot.success_rate,
                snapshot.avg_response_time, snapshot.total_tokens, snapshot.avg_tokens_per_task,
                snapshot.system_uptime, snapshot.cpu_usage, snapshot.memory_usage,
                snapshot.langsmith_traces, snapshot.nats_messages
            ))
            conn.commit()
    
    def store_agent_metrics(self, metrics_list: List[AgentMetrics]):
        """Store agent metrics in database"""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for metric in metrics_list:
                conn.execute('''
                    INSERT INTO agent_metrics (
                        timestamp, agent_id, agent_type, status, tasks_completed,
                        avg_response_time, success_rate, total_tokens, uptime, last_activity
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, metric.agent_id, metric.agent_type, metric.status,
                    metric.tasks_completed, metric.avg_response_time, metric.success_rate,
                    metric.total_tokens, metric.uptime, metric.last_activity
                ))
            conn.commit()
    
    def get_historical_kpis(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical KPI data"""
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM kpi_snapshots 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', (since,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def calculate_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Calculate performance trends"""
        historical_data = self.get_historical_kpis(hours)
        
        if len(historical_data) < 2:
            return {"error": "Not enough historical data"}
        
        # Extract metrics for trend calculation
        success_rates = [d['success_rate'] for d in historical_data if d['success_rate'] is not None]
        response_times = [d['avg_response_time'] for d in historical_data if d['avg_response_time'] is not None]
        task_counts = [d['total_tasks'] for d in historical_data if d['total_tasks'] is not None]
        
        trends = {}
        
        if success_rates:
            current_sr = success_rates[0]
            avg_sr = statistics.mean(success_rates)
            trends['success_rate'] = {
                'current': current_sr,
                'average': avg_sr,
                'trend': 'improving' if current_sr > avg_sr else 'declining' if current_sr < avg_sr else 'stable'
            }
        
        if response_times:
            current_rt = response_times[0]
            avg_rt = statistics.mean(response_times)
            trends['response_time'] = {
                'current': current_rt,
                'average': avg_rt,
                'trend': 'improving' if current_rt < avg_rt else 'declining' if current_rt > avg_rt else 'stable'
            }
        
        if len(task_counts) >= 2:
            recent_tasks = sum(task_counts[:3]) / 3 if len(task_counts) >= 3 else task_counts[0]
            older_tasks = sum(task_counts[-3:]) / 3 if len(task_counts) >= 3 else task_counts[-1]
            trends['task_volume'] = {
                'recent_average': recent_tasks,
                'older_average': older_tasks,
                'trend': 'increasing' if recent_tasks > older_tasks else 'decreasing' if recent_tasks < older_tasks else 'stable'
            }
        
        return trends
    
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        current_kpi = self.calculate_kpi_snapshot()
        agent_metrics = self.get_agent_metrics()
        trends = self.calculate_trends()
        historical_data = self.get_historical_kpis(24)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_period": "24_hours",
            "current_metrics": asdict(current_kpi),
            "agent_breakdown": [asdict(metric) for metric in agent_metrics],
            "performance_trends": trends,
            "historical_summary": {
                "data_points": len(historical_data),
                "time_range": f"{len(historical_data)} snapshots over 24 hours",
                "peak_performance": self._find_peak_performance(historical_data),
                "bottlenecks": self._identify_bottlenecks(historical_data)
            },
            "recommendations": self._generate_recommendations(current_kpi, trends)
        }
        
        return report
    
    def _find_peak_performance(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Find peak performance periods"""
        if not historical_data:
            return {}
        
        best_success_rate = max(historical_data, key=lambda x: x.get('success_rate', 0))
        best_response_time = min(historical_data, key=lambda x: x.get('avg_response_time', float('inf')))
        
        return {
            "best_success_rate": {
                "value": best_success_rate.get('success_rate'),
                "timestamp": best_success_rate.get('timestamp')
            },
            "best_response_time": {
                "value": best_response_time.get('avg_response_time'),
                "timestamp": best_response_time.get('timestamp')
            }
        }
    
    def _identify_bottlenecks(self, historical_data: List[Dict]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        if not historical_data:
            return bottlenecks
        
        # Check for low success rates
        low_success_periods = [d for d in historical_data if d.get('success_rate', 1.0) < 0.9]
        if low_success_periods:
            bottlenecks.append({
                "type": "low_success_rate",
                "description": f"Success rate below 90% for {len(low_success_periods)} periods",
                "severity": "high" if len(low_success_periods) > 5 else "medium"
            })
        
        # Check for high response times
        avg_response_time = statistics.mean([d.get('avg_response_time', 0) for d in historical_data])
        high_response_periods = [d for d in historical_data if d.get('avg_response_time', 0) > avg_response_time * 1.5]
        if high_response_periods:
            bottlenecks.append({
                "type": "high_response_time",
                "description": f"Response time 50% above average for {len(high_response_periods)} periods",
                "severity": "medium"
            })
        
        return bottlenecks
    
    def _generate_recommendations(self, current_kpi: KPISnapshot, trends: Dict) -> List[Dict[str, str]]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Success rate recommendations
        if current_kpi.success_rate < 0.95:
            recommendations.append({
                "category": "reliability",
                "priority": "high",
                "recommendation": "Success rate is below 95%. Review error logs and implement retry mechanisms."
            })
        
        # Response time recommendations
        if current_kpi.avg_response_time > 5.0:
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "recommendation": "Average response time exceeds 5 seconds. Consider optimizing LLM calls or adding more agents."
            })
        
        # Agent utilization recommendations
        if current_kpi.active_agents < 2:
            recommendations.append({
                "category": "scaling",
                "priority": "medium",
                "recommendation": "Only one agent active. Consider starting additional agents for redundancy."
            })
        
        # Trend-based recommendations
        if trends.get('response_time', {}).get('trend') == 'declining':
            recommendations.append({
                "category": "performance",
                "priority": "medium",
                "recommendation": "Response times are trending upward. Monitor system load and consider scaling."
            })
        
        return recommendations
    
    def export_to_csv(self, filename: str, hours: int = 24):
        """Export analytics data to CSV"""
        historical_data = self.get_historical_kpis(hours)
        
        csv_path = self.cache_dir / filename
        with open(csv_path, 'w', newline='') as csvfile:
            if historical_data:
                fieldnames = historical_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(historical_data)
        
        logger.info(f"Analytics data exported to {csv_path}")
        return csv_path
    
    def save_analytics_cache(self, analytics_data: Dict[str, Any]):
        """Save analytics data to cache for dashboard consumption"""
        try:
            with open(self.analytics_cache, 'w') as f:
                json.dump(analytics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving analytics cache: {e}")
    
    async def run_analytics_cycle(self):
        """Run a complete analytics cycle"""
        logger.info("Running analytics cycle...")
        
        # Calculate and store current metrics
        current_kpi = self.calculate_kpi_snapshot()
        self.store_kpi_snapshot(current_kpi)
        
        agent_metrics = self.get_agent_metrics()
        self.store_agent_metrics(agent_metrics)
        
        # Generate comprehensive report
        analytics_report = self.generate_analytics_report()
        
        # Save to cache for dashboard
        self.save_analytics_cache(analytics_report)
        
        logger.info(f"Analytics cycle completed. Active agents: {current_kpi.active_agents}, "
                   f"Success rate: {current_kpi.success_rate:.2%}, "
                   f"Total tasks: {current_kpi.total_tasks}")
        
        return analytics_report

async def main():
    """Main analytics monitoring loop"""
    aggregator = HeroAnalyticsAggregator()
    
    logger.info("🔍 Hero Analytics Dashboard Monitor started")
    logger.info(f"📊 Data storage: {aggregator.db_path}")
    logger.info(f"📁 Cache directory: {aggregator.cache_dir}")
    
    # Run initial analytics cycle
    initial_report = await aggregator.run_analytics_cycle()
    
    print("📈 Initial Analytics Report:")
    print(f"  Active Agents: {initial_report['current_metrics']['active_agents']}")
    print(f"  Success Rate: {initial_report['current_metrics']['success_rate']:.2%}")
    print(f"  Total Tasks: {initial_report['current_metrics']['total_tasks']}")
    print(f"  LangSmith Traces: {initial_report['current_metrics']['langsmith_traces']}")
    print()
    
    # Export CSV report
    csv_path = aggregator.export_to_csv("hero_analytics_export.csv")
    print(f"📁 Analytics exported to: {csv_path}")
    
    # Continuous monitoring loop
    try:
        while True:
            await asyncio.sleep(30)  # Run every 30 seconds
            await aggregator.run_analytics_cycle()
            
    except KeyboardInterrupt:
        logger.info("Analytics monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error in analytics monitoring: {e}")

if __name__ == "__main__":
    asyncio.run(main())