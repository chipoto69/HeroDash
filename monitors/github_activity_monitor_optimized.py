#!/usr/bin/env python3
"""
GitHub Activity Monitor - Fetches contribution graph data
Optimized version with better caching and performance
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error
import time

class GitHubActivityMonitor:
    def __init__(self, username=None):
        self.username = username or os.environ.get('GITHUB_USERNAME', 'rudlord')
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_file = self.cache_dir / "github_activity.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.last_run_time = 0
        self.min_update_interval = 300  # 5 minutes minimum between updates
        
    def get_contributions_svg(self):
        """Fetch GitHub contributions graph (SVG format)"""
        try:
            # GitHub's contribution graph URL
            url = f"https://github.com/{self.username}"
            
            # Try to fetch the page
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode('utf-8')
                
            # Parse contribution data from the HTML
            # GitHub embeds contribution data in the page
            contributions = self._parse_contributions(html)
            return contributions
            
        except Exception as e:
            print(f"Error fetching GitHub data: {e}")
            return None
    
    def _parse_contributions(self, html):
        """Parse contribution data from GitHub HTML"""
        contributions = []
        
        # Look for contribution data in the HTML
        # GitHub uses data-date and data-level attributes
        import re
        
        # Find all contribution squares
        pattern = r'data-date="([^"]+)"[^>]*data-level="([^"]+)"'
        matches = re.findall(pattern, html)
        
        for date_str, level in matches:
            contributions.append({
                "date": date_str,
                "level": int(level),
                "count": self._level_to_count(int(level))
            })
        
        return contributions[-21:] if contributions else []  # Last 21 days
    
    def _level_to_count(self, level):
        """Convert GitHub contribution level to approximate count"""
        # GitHub uses levels 0-4 for contribution intensity
        level_map = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}
        return level_map.get(level, 0)
    
    def get_mock_contributions(self):
        """Generate mock contribution data for 21 days"""
        import random
        
        contributions = []
        today = datetime.now()
        
        for i in range(21):
            date = today - timedelta(days=i)
            level = random.choices([0, 1, 2, 3, 4], weights=[30, 30, 20, 15, 5])[0]
            
            contributions.append({
                "date": date.strftime("%Y-%m-%d"),
                "level": level,
                "count": self._level_to_count(level)
            })
        
        return list(reversed(contributions))
    
    def get_contribution_graph(self):
        """Get ASCII representation of contribution graph"""
        # Try to get real data or use mock
        contributions = self.get_contributions_svg()
        
        if not contributions:
            contributions = self.get_mock_contributions()
        
        # Create ASCII graph
        graph_chars = ["⬜", "🟩", "🟩", "🟩", "🟩"]  # Different intensities
        simple_chars = ["·", "▫", "▪", "◼", "█"]  # Simpler ASCII version
        
        # Build the graph
        graph_data = {
            "contributions": contributions,
            "graph_ascii": "",
            "graph_unicode": "",
            "total_contributions": sum(c["count"] for c in contributions),
            "streak": self._calculate_streak(contributions),
            "most_active_day": self._find_most_active(contributions)
        }
        
        # Create ASCII representations
        for contrib in contributions:
            level = contrib["level"]
            graph_data["graph_ascii"] += simple_chars[level]
            graph_data["graph_unicode"] += graph_chars[level]
        
        return graph_data
    
    def _calculate_streak(self, contributions):
        """Calculate current streak"""
        streak = 0
        for contrib in reversed(contributions):
            if contrib["count"] > 0:
                streak += 1
            else:
                break
        return streak
    
    def _find_most_active(self, contributions):
        """Find most active day in the period"""
        if not contributions:
            return None
        
        most_active = max(contributions, key=lambda x: x["count"])
        return most_active["date"]
    
    def save_data(self, data):
        """Save data to cache"""
        try:
            data["timestamp"] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving GitHub data: {e}")
    
    def load_cached_data(self):
        """Load cached data if recent (< 1 hour old)"""
        try:
            if self.cache_file.exists():
                age = datetime.now().timestamp() - self.cache_file.stat().st_mtime
                if age < 3600:  # 1 hour
                    with open(self.cache_file, 'r') as f:
                        return json.load(f)
        except:
            pass
        return None
    
    def should_update(self):
        """Check if we should update based on time interval"""
        current_time = time.time()
        return (current_time - self.last_run_time) > self.min_update_interval
    
    def get_activity_data(self):
        """Main method to get activity data"""
        # Check if we should update based on time
        if not self.should_update():
            # Try cached data first
            cached = self.load_cached_data()
            if cached:
                return cached
        
        # Get fresh data
        data = self.get_contribution_graph()
        
        # Save to cache
        self.save_data(data)
        
        # Update last run time
        self.last_run_time = time.time()
        
        return data

def main():
    monitor = GitHubActivityMonitor()
    data = monitor.get_activity_data()
    
    # Output only JSON for the dashboard to parse
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()