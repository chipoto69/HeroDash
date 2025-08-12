#!/usr/bin/env python3
"""
Hero Command Centre - Real-Time Web Dashboard
Interactive web interface for monitoring AI agents, analytics, and system performance
"""

import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# Cache directory for Hero data
CACHE_DIR = Path.home() / ".hero_core" / "cache"
LOG_DIR = Path.home() / ".hero_core" / "logs"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebDashboard")

# FastAPI app
app = FastAPI(title="Hero Command Centre", description="AI Agent Analytics Dashboard")

# Templates and static files
templates = Jinja2Templates(directory="web_templates")

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = WebSocketManager()

class DashboardDataAggregator:
    """Aggregate data from various Hero monitoring sources"""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.last_update = datetime.now()
        
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
    
    def get_agent_runtime_status(self) -> Dict[str, Any]:
        """Get agent runtime status"""
        return self.read_json_file("agent_runtime_status.json")
    
    def get_agent_coordination(self) -> Dict[str, Any]:
        """Get agent coordination data"""
        return self.read_json_file("agent_coordination.json")
    
    def get_langsmith_stats(self) -> Dict[str, Any]:
        """Get LangSmith tracing statistics"""
        return self.read_json_file("langsmith_stats.json")
    
    def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage analytics"""
        return self.read_json_file("token_analysis.json")
    
    def get_agents_status(self) -> Dict[str, Any]:
        """Get individual agent status files"""
        agents_data = {}
        
        # Read all agent status files
        for file_path in self.cache_dir.glob("agent_*_status.json"):
            agent_id = file_path.stem.replace("agent_", "").replace("_status", "")
            agents_data[agent_id] = self.read_json_file(file_path.name)
            
        return agents_data
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate real-time performance metrics"""
        runtime_data = self.get_agent_runtime_status()
        coordination_data = self.get_agent_coordination()
        langsmith_data = self.get_langsmith_stats()
        
        metrics = {
            "system_health": {
                "status": "healthy",
                "uptime_seconds": runtime_data.get("runtime_stats", {}).get("uptime_seconds", 0),
                "total_agents": len(runtime_data.get("agents", {})),
                "active_agents": len([a for a in runtime_data.get("agents", {}).values() if a.get("status") == "active"]),
            },
            "task_performance": {
                "total_tasks": coordination_data.get("coordination_stats", {}).get("total_tasks_processed", 0),
                "success_rate": coordination_data.get("coordination_stats", {}).get("success_rate", 0),
                "avg_duration": coordination_data.get("coordination_stats", {}).get("average_task_duration", 0),
                "queue_length": coordination_data.get("tasks", {}).get("queue_length", 0),
            },
            "llm_performance": {
                "total_traces": langsmith_data.get("total_traces", 0),
                "success_rate": langsmith_data.get("success_rate", 0),
                "avg_duration": langsmith_data.get("average_duration_ms", 0),
                "active_traces": langsmith_data.get("active_traces", 0),
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    def get_task_queue_analysis(self) -> Dict[str, Any]:
        """Analyze task queue and distribution"""
        coordination_data = self.get_agent_coordination()
        
        analysis = {
            "queue_stats": coordination_data.get("tasks", {}),
            "agent_distribution": coordination_data.get("agents", {}),
            "recent_activity": coordination_data.get("recent_activity", [])[:10],
            "load_balancing": {
                "score": coordination_data.get("coordination_stats", {}).get("load_balancing_score", 0),
                "distribution": "balanced"  # Could be calculated
            }
        }
        
        return analysis
    
    def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """Get all dashboard data in one comprehensive object"""
        return {
            "overview": {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "refresh_interval": 2000  # milliseconds
            },
            "agents": {
                "runtime_status": self.get_agent_runtime_status(),
                "coordination": self.get_agent_coordination(),
                "individual_status": self.get_agents_status()
            },
            "performance": self.get_performance_metrics(),
            "tasks": self.get_task_queue_analysis(),
            "llm_integration": {
                "langsmith": self.get_langsmith_stats(),
                "token_usage": self.get_token_usage()
            },
            "system_health": {
                "nats_connected": True,  # Could check actual NATS status
                "cache_healthy": self.cache_dir.exists(),
                "logs_accessible": LOG_DIR.exists()
            }
        }

# Initialize data aggregator
aggregator = DashboardDataAggregator()

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    initial_data = aggregator.get_comprehensive_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "initial_data": json.dumps(initial_data, indent=2)
    })

@app.get("/api/status")
async def get_system_status():
    """Get current system status"""
    return aggregator.get_comprehensive_dashboard_data()

@app.get("/api/agents")
async def get_agents_data():
    """Get detailed agent information"""
    return {
        "runtime_status": aggregator.get_agent_runtime_status(),
        "coordination": aggregator.get_agent_coordination(),
        "individual_agents": aggregator.get_agents_status()
    }

@app.get("/api/performance")
async def get_performance_data():
    """Get performance metrics"""
    return aggregator.get_performance_metrics()

@app.get("/api/tasks")
async def get_tasks_data():
    """Get task queue and activity data"""
    return aggregator.get_task_queue_analysis()

@app.get("/api/analytics")
async def get_analytics_data():
    """Get comprehensive analytics data"""
    return {
        "langsmith": aggregator.get_langsmith_stats(),
        "token_usage": aggregator.get_token_usage(),
        "performance_history": [],  # Could implement historical data
        "trends": {}  # Could calculate trends
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send updates every 2 seconds
            data = aggregator.get_comprehensive_dashboard_data()
            await manager.broadcast({
                "type": "dashboard_update",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/agent/{agent_id}/action")
async def agent_action(agent_id: str, action: dict):
    """Perform action on specific agent"""
    # This could integrate with the agent runtime to send commands
    logger.info(f"Action requested for agent {agent_id}: {action}")
    return {"status": "action_queued", "agent_id": agent_id, "action": action}

@app.get("/api/logs")
async def get_recent_logs():
    """Get recent log entries"""
    logs = []
    log_files = ["agent_runtime.log", "agent_coordinator.log", "langsmith_tracer.log"]
    
    for log_file in log_files:
        log_path = LOG_DIR / log_file
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:] if len(lines) > 50 else lines
                    logs.extend([{
                        "source": log_file,
                        "content": line.strip(),
                        "timestamp": datetime.now().isoformat()
                    } for line in recent_lines if line.strip()])
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
    
    return {"logs": logs}

# Background task to broadcast updates
async def background_broadcaster():
    """Background task to send periodic updates"""
    while True:
        try:
            if manager.active_connections:
                data = aggregator.get_comprehensive_dashboard_data()
                await manager.broadcast({
                    "type": "background_update",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error in background broadcaster: {e}")
        
        await asyncio.sleep(5)  # Update every 5 seconds

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(background_broadcaster())
    logger.info("Hero Command Centre Web Dashboard started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Hero Command Centre Web Dashboard shutting down")

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    templates_dir = Path("web_templates")
    templates_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting Hero Command Centre Web Dashboard")
    print("📊 Real-time agent analytics and monitoring")
    print("🌐 Access at: http://localhost:8080")
    print("📈 WebSocket updates enabled")
    print()
    
    uvicorn.run(
        "web_dashboard:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )