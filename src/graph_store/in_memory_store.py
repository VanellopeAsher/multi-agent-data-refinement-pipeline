"""
In-memory graph store for debugging/testing.
"""
import json
from typing import List, Dict, Any, Optional
from src.graph_store.base_store import BaseGraphStore


class InMemoryGraphStore(BaseGraphStore):
    """In-memory implementation of graph storage for testing."""
    
    def __init__(self):
        """Initialize in-memory graph."""
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._node_counter = 0
    
    def upsert_node(self, labels: List[str], fields: Dict[str, Any]) -> str:
        """
        Upsert a node in memory.
        
        Args:
            labels: List of node labels
            fields: Dictionary of node properties
            
        Returns:
            Node ID
        """
        node_id = fields.get('id', None)
        if not node_id:
            self._node_counter += 1
            node_id = f"node_{self._node_counter}"
            fields['id'] = node_id
        
        node_data = {
            'id': node_id,
            'labels': labels,
            **fields
        }
        self.nodes[node_id] = node_data
        return node_id
    
    def add_edge(
        self,
        src_id: str,
        rel_type: str,
        dst_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add an edge between two nodes.
        
        Args:
            src_id: Source node ID
            rel_type: Relationship type
            dst_id: Destination node ID
            properties: Optional edge properties
            
        Returns:
            True if successful
        """
        if src_id not in self.nodes or dst_id not in self.nodes:
            return False
        
        edge = {
            'src_id': src_id,
            'rel_type': rel_type,
            'dst_id': dst_id,
            'properties': properties or {}
        }
        self.edges.append(edge)
        return True
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node dictionary or None
        """
        return self.nodes.get(node_id)
    
    def query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a simple query (limited support for in-memory).
        
        Note: This is a simplified implementation. For complex queries,
        use Neo4jGraphStore instead.
        
        Args:
            cypher: Cypher query (limited support)
            parameters: Optional query parameters
            
        Returns:
            List of result dictionaries
        """
        # Very basic query support for testing
        if 'MATCH (n)' in cypher and 'RETURN' in cypher:
            if 'labels(n)' in cypher and 'properties(n)' in cypher:
                return [
                    {'labels': node['labels'], 'props': {k: v for k, v in node.items() if k != 'labels'}}
                    for node in self.nodes.values()
                ]
            elif 'n' in cypher:
                return [{'n': node} for node in self.nodes.values()]
        
        # Edge query
        if 'MATCH (a)-[r]->(b)' in cypher:
            return [
                {
                    'src_id': edge['src_id'],
                    'rel_type': edge['rel_type'],
                    'dst_id': edge['dst_id'],
                    'props': edge['properties']
                }
                for edge in self.edges
            ]
        
        return []
    
    def export_snapshot(self, path: str) -> bool:
        """
        Export graph snapshot to JSON file.
        
        Args:
            path: Output file path
            
        Returns:
            True if successful
        """
        try:
            nodes = [
                {
                    'labels': node.get('labels', []),
                    'props': {k: v for k, v in node.items() if k != 'labels'}
                }
                for node in self.nodes.values()
            ]
            
            edges = [
                {
                    'src_id': edge['src_id'],
                    'rel_type': edge['rel_type'],
                    'dst_id': edge['dst_id'],
                    'props': edge['properties']
                }
                for edge in self.edges
            ]
            
            snapshot = {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting snapshot: {e}")
            return False
    
    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            True if successful
        """
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Remove edges connected to this node
            self.edges = [
                e for e in self.edges
                if e['src_id'] != node_id and e['dst_id'] != node_id
            ]
            return True
        return False
    
    def delete_edge(self, src_id: str, rel_type: str, dst_id: str) -> bool:
        """
        Delete an edge.
        
        Args:
            src_id: Source node ID
            rel_type: Relationship type
            dst_id: Destination node ID
            
        Returns:
            True if successful
        """
        initial_count = len(self.edges)
        self.edges = [
            e for e in self.edges
            if not (e['src_id'] == src_id and e['rel_type'] == rel_type and e['dst_id'] == dst_id)
        ]
        return len(self.edges) < initial_count
    
    def close(self):
        """Close in-memory store (no-op)."""
        pass

