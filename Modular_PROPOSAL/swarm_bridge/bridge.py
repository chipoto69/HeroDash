#!/usr/bin/env python3
"""
Swarm Bridge - Non-invasive integration with existing AI agents
Connects your running agents to the swarm without any code changes
"""

import asyncio
import json
import os
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swarm_core import Swarm, Agent, Message, MessageType, SwarmConfig, Protocol

class SwarmBridge:
    """
    Main bridge for connecting existing AI agents to the swarm
    Works with Claude, LangChain, Qwen, and any process-based agents
    """
    
    def __init__(self, transport: str = "nats", transport_url: str = "nats://localhost:4222"):
        self.config = SwarmConfig(
            transport=transport,
            transport_url=transport_url,
            heartbeat_interval=30
        )
        self.swarm = Swarm(self.config)
        self.monitors = {}
        self.process_agents = {}
        self.file_watchers = {}
        self.running = False
        
        # Cache directory for Hero Dashboard compatibility
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Start the bridge"""
        await self.swarm.start()
        self.running = True
        print("🌉 Swarm Bridge started")
        
    async def stop(self):
        """Stop the bridge"""
        self.running = False
        await self.swarm.stop()
        print("🌉 Swarm Bridge stopped")
        
    # === Claude Integration ===
    
    async def attach_claude_instance(self, 
                                    instance_id: str,
                                    working_dir: Optional[str] = None,
                                    monitor_files: bool = True):
        """
        Attach a Claude Code instance to the swarm
        Monitors its activity without any modifications
        """
        print(f"🤖 Attaching Claude instance: {instance_id}")
        
        agent = ClaudeAgent(instance_id, working_dir, monitor_files)
        await self.swarm.add_agent(agent)
        self.process_agents[instance_id] = agent
        
        # Start monitoring
        if monitor_files and working_dir:
            await self._start_file_monitor(instance_id, working_dir)
        
        return agent
    
    # === LangChain/LangSmith Integration ===
    
    async def attach_langchain_agent(self,
                                    agent_name: str,
                                    project_name: Optional[str] = None,
                                    monitor_traces: bool = True):
        """
        Attach a LangChain agent via LangSmith tracing
        """
        print(f"🦜 Attaching LangChain agent: {agent_name}")
        
        agent = LangChainAgent(agent_name, project_name)
        await self.swarm.add_agent(agent)
        self.process_agents[agent_name] = agent
        
        if monitor_traces:
            await self._start_trace_monitor(agent_name, project_name)
        
        return agent
    
    # === Process-based Agent Integration ===
    
    async def attach_process(self,
                            process_name: str,
                            pid: Optional[int] = None,
                            command_pattern: Optional[str] = None):
        """
        Attach any running process as an agent
        Can find process by PID or command pattern
        """
        # Find process
        if pid:
            try:
                process = psutil.Process(pid)
            except psutil.NoSuchProcess:
                print(f"❌ Process {pid} not found")
                return None
        elif command_pattern:
            process = self._find_process(command_pattern)
            if not process:
                print(f"❌ No process matching '{command_pattern}'")
                return None
        else:
            print("❌ Need either PID or command pattern")
            return None
        
        print(f"🔧 Attaching process: {process_name} (PID: {process.pid})")
        
        agent = ProcessAgent(process_name, process)
        await self.swarm.add_agent(agent)
        self.process_agents[process_name] = agent
        
        return agent
    
    # === File-based Integration ===
    
    async def watch_json_cache(self, 
                               cache_path: Optional[Path] = None,
                               agent_name: str = "cache_monitor"):
        """
        Watch JSON cache files (Hero Dashboard compatible)
        Publishes changes to swarm
        """
        cache_path = cache_path or self.cache_dir
        print(f"📁 Watching cache directory: {cache_path}")
        
        watcher = CacheWatcherAgent(agent_name, cache_path)
        await self.swarm.add_agent(watcher)
        self.file_watchers[agent_name] = watcher
        
        # Start watching
        asyncio.create_task(watcher.start_watching())
        
        return watcher
    
    # === Auto-discovery ===
    
    async def auto_discover_agents(self) -> List[Dict[str, Any]]:
        """
        Automatically discover running AI agents
        """
        discovered = []
        
        # Common AI agent process patterns
        patterns = [
            ("claude", r"claude|ccm"),
            ("langchain", r"langgraph|langsmith"),
            ("qwen", r"qwen"),
            ("ollama", r"ollama"),
            ("openai", r"openai|gpt"),
            ("chimera", r"chimera"),
            ("autogen", r"autogen"),
            ("crewai", r"crewai")
        ]
        
        for name, pattern in patterns:
            processes = self._find_all_processes(pattern)
            for proc in processes:
                discovered.append({
                    "type": name,
                    "pid": proc.pid,
                    "name": proc.name(),
                    "cmdline": " ".join(proc.cmdline()[:3])
                })
        
        print(f"🔍 Discovered {len(discovered)} AI agents")
        return discovered
    
    async def attach_all_discovered(self):
        """
        Attach all discovered agents automatically
        """
        discovered = await self.auto_discover_agents()
        
        for agent_info in discovered:
            agent_id = f"{agent_info['type']}_{agent_info['pid']}"
            await self.attach_process(
                agent_id,
                pid=agent_info['pid']
            )
        
        print(f"✅ Attached {len(discovered)} agents to swarm")
    
    # === Helper methods ===
    
    def _find_process(self, pattern: str) -> Optional[psutil.Process]:
        """Find process by command pattern"""
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline'] or [])
                if regex.search(cmdline) or regex.search(proc.info['name']):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return None
    
    def _find_all_processes(self, pattern: str) -> List[psutil.Process]:
        """Find all processes matching pattern"""
        import re
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = " ".join(proc.info['cmdline'] or [])
                if regex.search(cmdline) or regex.search(proc.info['name']):
                    matches.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return matches
    
    async def _start_file_monitor(self, agent_id: str, directory: str):
        """Start monitoring files in directory"""
        # Implementation in file_watcher.py
        pass
    
    async def _start_trace_monitor(self, agent_name: str, project: str):
        """Start monitoring LangSmith traces"""
        # Implementation in langsmith_monitor.py
        pass

# === Agent Implementations ===

class ClaudeAgent(Agent):
    """
    Agent wrapper for Claude instances
    """
    
    def __init__(self, instance_id: str, working_dir: Optional[str] = None, 
                 monitor_files: bool = True):
        super().__init__(f"claude_{instance_id}")
        self.instance_id = instance_id
        self.working_dir = working_dir
        self.monitor_files = monitor_files
        self._capabilities = ["code", "analysis", "reasoning", "conversation"]
        
    async def process(self, message: Message) -> Optional[Message]:
        """
        Process messages for Claude instance
        Could inject via file or API if Claude adds support
        """
        if message.type == MessageType.TASK:
            # For now, log the task
            print(f"📝 Task for Claude {self.instance_id}: {message.data}")
            
            # Could write to a file that Claude monitors
            if self.working_dir:
                task_file = Path(self.working_dir) / ".swarm_tasks.json"
                with open(task_file, "w") as f:
                    json.dump(message.to_dict(), f)
            
            # Return acknowledgment
            return Protocol.result(
                self.id,
                message.from_agent,
                message.id,
                {"status": "received", "instance": self.instance_id}
            )
        
        return None
    
    async def capabilities(self) -> List[str]:
        return self._capabilities

class LangChainAgent(Agent):
    """
    Agent wrapper for LangChain/LangGraph agents
    """
    
    def __init__(self, agent_name: str, project: Optional[str] = None):
        super().__init__(f"langchain_{agent_name}")
        self.agent_name = agent_name
        self.project = project
        self._capabilities = ["orchestration", "chains", "tools", "memory"]
        
    async def process(self, message: Message) -> Optional[Message]:
        """
        Process messages for LangChain agent
        """
        if message.type == MessageType.TASK:
            # Could trigger LangChain via API or file
            print(f"🦜 Task for LangChain {self.agent_name}: {message.data}")
            
            return Protocol.result(
                self.id,
                message.from_agent,
                message.id,
                {"status": "received", "agent": self.agent_name}
            )
        
        return None

class ProcessAgent(Agent):
    """
    Generic agent wrapper for any process
    """
    
    def __init__(self, name: str, process: psutil.Process):
        super().__init__(f"process_{name}")
        self.name = name
        self.process = process
        self._capabilities = ["process", "monitoring"]
        
    async def process(self, message: Message) -> Optional[Message]:
        """
        Process messages for wrapped process
        """
        if message.type == MessageType.TASK:
            # Could send signals or write to stdin
            print(f"⚙️ Task for process {self.name} (PID {self.process.pid}): {message.data}")
            
            return Protocol.result(
                self.id,
                message.from_agent,
                message.id,
                {"status": "received", "pid": self.process.pid}
            )
        
        return None
    
    async def health(self) -> Dict[str, Any]:
        """Report process health"""
        try:
            if self.process.is_running():
                return {
                    "status": "healthy",
                    "pid": self.process.pid,
                    "cpu": self.process.cpu_percent(),
                    "memory": self.process.memory_info().rss / 1024 / 1024
                }
        except:
            pass
        
        return {"status": "unhealthy", "pid": self.process.pid}

class CacheWatcherAgent(Agent):
    """
    Agent that watches cache files and publishes changes
    """
    
    def __init__(self, name: str, cache_dir: Path):
        super().__init__(f"watcher_{name}")
        self.cache_dir = cache_dir
        self.last_mtimes = {}
        self._capabilities = ["monitoring", "cache", "files"]
        
    async def start_watching(self):
        """Watch for file changes"""
        while True:
            try:
                for json_file in self.cache_dir.glob("*.json"):
                    mtime = json_file.stat().st_mtime
                    
                    if json_file not in self.last_mtimes or mtime > self.last_mtimes[json_file]:
                        # File changed
                        self.last_mtimes[json_file] = mtime
                        
                        # Read and broadcast
                        try:
                            with open(json_file) as f:
                                data = json.load(f)
                            
                            # Broadcast change
                            await self.swarm.broadcast(
                                self.id,
                                {
                                    "event": "cache_update",
                                    "file": str(json_file),
                                    "data": data
                                }
                            )
                        except:
                            pass
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"❌ Watcher error: {e}")
                await asyncio.sleep(5)
    
    async def process(self, message: Message) -> Optional[Message]:
        """Process messages"""
        return None