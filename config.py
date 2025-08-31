#!/usr/bin/env python3
"""
Centralized configuration for Hero Dashboard
Replaces hardcoded paths and sensitive data with environment variables
"""

import os
from pathlib import Path

class Config:
    """Centralized configuration management"""
    
    # Base directories - use environment variables or sensible defaults
    HERO_DASHBOARD_DIR = os.environ.get('HERO_DASHBOARD_DIR', str(Path.home() / "Hero_dashboard"))
    CHIMERA_BASE = os.environ.get('CHIMERA_BASE', str(Path.home() / "q3" / "Frontline"))
    GRAPHITI_BASE = os.environ.get('GRAPHITI_BASE', str(Path.home() / "q3" / "0_MEMORY" / "graphiti"))
    
    # GitHub configuration
    GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
    
    # Neo4j configuration
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    
    # LangSmith configuration
    LANGSMITH_API_KEY = os.environ.get('LANGSMITH_API_KEY')
    LANGSMITH_ENDPOINT = os.environ.get('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com')
    LANGSMITH_PROJECT = os.environ.get('LANGSMITH_PROJECT', 'hero-command-centre')
    
    # Cache directories
    HERO_CACHE = Path.home() / ".hero_core" / "cache"
    HERO_DASHBOARD_CACHE = Path.home() / ".hero_dashboard"
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        missing = []
        
        if not cls.GITHUB_USERNAME:
            missing.append("GITHUB_USERNAME")
        
        if not cls.NEO4J_PASSWORD:
            missing.append("NEO4J_PASSWORD")
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def get_monitor_path(cls, monitor_name):
        """Get full path to a monitor script"""
        return str(Path(cls.HERO_DASHBOARD_DIR) / "monitors" / monitor_name)
    
    @classmethod
    def get_script_path(cls, script_name):
        """Get full path to a script"""
        return str(Path(cls.HERO_DASHBOARD_DIR) / script_name)

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please set the required environment variables before running the application.")