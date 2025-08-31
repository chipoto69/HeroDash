#!/usr/bin/env python3

"""
Graphiti Knowledge Graph Monitor
Real-time monitoring and statistics for Graphiti temporal knowledge graphs
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j driver not installed. Install with: pip install neo4j")

class GraphitiMonitor:
    def __init__(self):
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD')
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable must be set")
        self.driver = None
        self.stats_file = Path.home() / ".hero_dashboard" / "graphiti_stats.json"
        self.stats_file.parent.mkdir(exist_ok=True)
        
    def connect(self) -> bool:
        """Connect to Neo4j database"""
        if not NEO4J_AVAILABLE:
            return False
            
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            return False
    
    def get_node_counts(self) -> Dict[str, int]:
        """Get counts of different node types"""
        if not self.driver:
            return {}
            
        counts = {
            "entities": 0,
            "episodes": 0,
            "communities": 0,
            "total": 0
        }
        
        try:
            with self.driver.session() as session:
                # Count Entity nodes
                result = session.run(
                    "MATCH (n:Entity) RETURN count(n) as count"
                )
                counts["entities"] = result.single()["count"]
                
                # Count Episodic nodes
                result = session.run(
                    "MATCH (n:Episodic) RETURN count(n) as count"
                )
                counts["episodes"] = result.single()["count"]
                
                # Count Community nodes
                result = session.run(
                    "MATCH (n:Community) RETURN count(n) as count"
                )
                counts["communities"] = result.single()["count"]
                
                # Total nodes
                result = session.run(
                    "MATCH (n) RETURN count(n) as count"
                )
                counts["total"] = result.single()["count"]
                
        except Exception as e:
            print(f"Error getting node counts: {e}")
            
        return counts
    
    def get_edge_counts(self) -> Dict[str, int]:
        """Get counts of different edge types"""
        if not self.driver:
            return {}
            
        counts = {
            "entity_edges": 0,
            "episodic_edges": 0,
            "community_edges": 0,
            "total": 0
        }
        
        try:
            with self.driver.session() as session:
                # Count different relationship types
                result = session.run(
                    """
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                    """
                )
                
                for record in result:
                    rel_type = record["rel_type"]
                    count = record["count"]
                    
                    if "ENTITY" in rel_type:
                        counts["entity_edges"] += count
                    elif "EPISODE" in rel_type or "EPISODIC" in rel_type:
                        counts["episodic_edges"] += count
                    elif "COMMUNITY" in rel_type:
                        counts["community_edges"] += count
                    
                    counts["total"] += count
                    
        except Exception as e:
            print(f"Error getting edge counts: {e}")
            
        return counts
    
    def get_recent_activity(self, hours: int = 24) -> Dict[str, any]:
        """Get recent activity in the graph"""
        if not self.driver:
            return {}
            
        activity = {
            "recent_episodes": 0,
            "recent_entities": 0,
            "recent_edges": 0,
            "last_update": None
        }
        
        try:
            with self.driver.session() as session:
                # Get recent episodes (last N hours)
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                # Count recent episodic nodes
                result = session.run(
                    """
                    MATCH (n:Episodic)
                    WHERE n.created_at >= $cutoff
                    RETURN count(n) as count
                    """,
                    cutoff=cutoff_time.isoformat()
                )
                activity["recent_episodes"] = result.single()["count"]
                
                # Get most recent update time
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.created_at IS NOT NULL
                    RETURN max(n.created_at) as last_update
                    """
                )
                record = result.single()
                if record and record["last_update"]:
                    activity["last_update"] = record["last_update"]
                    
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            
        return activity
    
    def get_entity_statistics(self) -> Dict[str, any]:
        """Get statistics about entities"""
        if not self.driver:
            return {}
            
        stats = {
            "unique_entities": 0,
            "entity_types": [],
            "most_connected": [],
            "avg_connections": 0
        }
        
        try:
            with self.driver.session() as session:
                # Get entity types
                result = session.run(
                    """
                    MATCH (n:Entity)
                    RETURN DISTINCT n.entity_type as type, count(n) as count
                    ORDER BY count DESC
                    LIMIT 10
                    """
                )
                
                stats["entity_types"] = [
                    {"type": r["type"], "count": r["count"]} 
                    for r in result if r["type"]
                ]
                
                # Get most connected entities
                result = session.run(
                    """
                    MATCH (n:Entity)-[r]-()
                    RETURN n.name as name, count(r) as connections
                    ORDER BY connections DESC
                    LIMIT 5
                    """
                )
                
                stats["most_connected"] = [
                    {"name": r["name"], "connections": r["connections"]}
                    for r in result if r["name"]
                ]
                
                # Get average connections
                result = session.run(
                    """
                    MATCH (n:Entity)
                    OPTIONAL MATCH (n)-[r]-()
                    WITH n, count(r) as conn_count
                    RETURN avg(conn_count) as avg_connections
                    """
                )
                record = result.single()
                if record:
                    stats["avg_connections"] = round(record["avg_connections"], 2)
                    
        except Exception as e:
            print(f"Error getting entity statistics: {e}")
            
        return stats
    
    def get_memory_timeline(self, days: int = 7) -> List[Dict]:
        """Get memory growth over time"""
        if not self.driver:
            return []
            
        timeline = []
        
        try:
            with self.driver.session() as session:
                for i in range(days):
                    date = datetime.now() - timedelta(days=i)
                    date_str = date.strftime("%Y-%m-%d")
                    
                    result = session.run(
                        """
                        MATCH (n)
                        WHERE date(n.created_at) = date($date)
                        RETURN count(n) as count
                        """,
                        date=date_str
                    )
                    
                    count = result.single()["count"]
                    timeline.append({
                        "date": date_str,
                        "nodes_added": count
                    })
                    
        except Exception as e:
            print(f"Error getting timeline: {e}")
            
        return timeline
    
    def get_graph_health(self) -> Dict[str, any]:
        """Get overall graph health metrics"""
        health = {
            "status": "UNKNOWN",
            "connected": False,
            "index_status": {},
            "warnings": []
        }
        
        if not self.driver:
            health["status"] = "DISCONNECTED"
            return health
            
        try:
            with self.driver.session() as session:
                # Check connection
                session.run("RETURN 1")
                health["connected"] = True
                
                # Check for indexes
                result = session.run("SHOW INDEXES")
                indexes = list(result)
                health["index_status"]["count"] = len(indexes)
                health["index_status"]["active"] = sum(
                    1 for idx in indexes if idx.get("state") == "ONLINE"
                )
                
                # Check for orphaned nodes
                result = session.run(
                    """
                    MATCH (n)
                    WHERE NOT (n)--()
                    RETURN count(n) as orphaned
                    """
                )
                orphaned = result.single()["orphaned"]
                if orphaned > 10:
                    health["warnings"].append(f"{orphaned} orphaned nodes detected")
                
                # Overall status
                if health["connected"] and health["index_status"]["active"] > 0:
                    health["status"] = "HEALTHY"
                elif health["connected"]:
                    health["status"] = "DEGRADED"
                else:
                    health["status"] = "UNHEALTHY"
                    
        except Exception as e:
            health["status"] = "ERROR"
            health["warnings"].append(str(e))
            
        return health
    
    def save_stats(self, stats: Dict):
        """Save statistics to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving stats: {e}")
    
    def collect_all_stats(self) -> Dict:
        """Collect all statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "connection": {
                "uri": self.neo4j_uri,
                "connected": self.driver is not None
            },
            "nodes": self.get_node_counts(),
            "edges": self.get_edge_counts(),
            "recent_activity": self.get_recent_activity(24),
            "entities": self.get_entity_statistics(),
            "health": self.get_graph_health(),
            "timeline": self.get_memory_timeline(7)
        }
        
        return stats
    
    def print_summary(self):
        """Print a summary of the graph status"""
        if not self.connect():
            print("❌ Cannot connect to Neo4j")
            return
            
        stats = self.collect_all_stats()
        
        print("\n" + "="*60)
        print("GRAPHITI KNOWLEDGE GRAPH STATUS")
        print("="*60)
        
        # Connection status
        health = stats["health"]
        status_icon = "🟢" if health["status"] == "HEALTHY" else "🟡" if health["status"] == "DEGRADED" else "🔴"
        print(f"\n{status_icon} Status: {health['status']}")
        print(f"📍 URI: {self.neo4j_uri}")
        
        # Node counts
        nodes = stats["nodes"]
        print(f"\n📊 NODES:")
        print(f"  • Entities: {nodes.get('entities', 0):,}")
        print(f"  • Episodes: {nodes.get('episodes', 0):,}")
        print(f"  • Communities: {nodes.get('communities', 0):,}")
        print(f"  • Total: {nodes.get('total', 0):,}")
        
        # Edge counts
        edges = stats["edges"]
        print(f"\n🔗 EDGES:")
        print(f"  • Entity Relations: {edges.get('entity_edges', 0):,}")
        print(f"  • Episodic Links: {edges.get('episodic_edges', 0):,}")
        print(f"  • Community Bonds: {edges.get('community_edges', 0):,}")
        print(f"  • Total: {edges.get('total', 0):,}")
        
        # Recent activity
        activity = stats["recent_activity"]
        print(f"\n⚡ RECENT ACTIVITY (24h):")
        print(f"  • New Episodes: {activity.get('recent_episodes', 0)}")
        if activity.get('last_update'):
            print(f"  • Last Update: {activity['last_update']}")
        
        # Entity statistics
        entities = stats["entities"]
        if entities.get("entity_types"):
            print(f"\n🏷️ TOP ENTITY TYPES:")
            for et in entities["entity_types"][:5]:
                print(f"  • {et['type']}: {et['count']}")
        
        if entities.get("most_connected"):
            print(f"\n🌟 MOST CONNECTED ENTITIES:")
            for mc in entities["most_connected"][:3]:
                print(f"  • {mc['name']}: {mc['connections']} connections")
        
        # Warnings
        if health.get("warnings"):
            print(f"\n⚠️ WARNINGS:")
            for warning in health["warnings"]:
                print(f"  • {warning}")
        
        print("\n" + "="*60)
        
        # Save stats
        self.save_stats(stats)
        print(f"📁 Stats saved to: {self.stats_file}")
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()

def main():
    monitor = GraphitiMonitor()
    
    try:
        monitor.print_summary()
    finally:
        monitor.close()

if __name__ == "__main__":
    main()