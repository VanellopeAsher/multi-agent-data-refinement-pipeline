import json
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from src.graph_store.base_store import BaseGraphStore
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE


class Neo4jGraphStore(BaseGraphStore):
    """Neo4j implementation of graph storage."""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None, database: Optional[str] = None):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.database = database or NEO4J_DATABASE
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def upsert_node(self, labels: List[str], fields: Dict[str, Any]) -> str:
        label_str = ':'.join(labels)
        
        node_id = fields.get('id', None)
        
        if node_id:
            cypher = f"""
            MERGE (n:{label_str} {{id: $id}})
            SET n += $props
            RETURN id(n) as internal_id, n.id as node_id
            """
            parameters = {
                'id': node_id,
                'props': {k: v for k, v in fields.items() if k != 'id'}
            }
        else:
            # Create new node
            cypher = f"""
            CREATE (n:{label_str})
            SET n = $props
            RETURN id(n) as internal_id, n.id as node_id
            """
            parameters = {'props': fields}
        
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, parameters)
            record = result.single()
            if record:
                return record['node_id'] or str(record['internal_id'])
            return str(record['internal_id']) if record else ""
    
    def add_edge(
        self,
        src_id: str,
        rel_type: str,
        dst_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        props_str = ""
        if properties:
            props_str = " SET r = $props"
        
        cypher = f"""
        MATCH (a), (b)
        WHERE (a.id = $src_id OR id(a) = $src_id)
        AND (b.id = $dst_id OR id(b) = $dst_id)
        MERGE (a)-[r:{rel_type}]->(b)
        {props_str}
        RETURN r
        """
        
        parameters = {
            'src_id': src_id,
            'dst_id': dst_id,
            'props': properties or {}
        }
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, parameters)
                return result.single() is not None
        except Exception as e:
            print(f"Error adding edge: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        cypher = """
        MATCH (n)
        WHERE (n.id = $node_id OR id(n) = $node_id)
        RETURN n
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, {'node_id': node_id})
            record = result.single()
            if record:
                node = record['n']
                return dict(node)
            return None
    
    def query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, parameters or {})
            return [dict(record) for record in result]
    
    def export_snapshot(self, path: str) -> bool:
        try:
            nodes_query = """
            MATCH (n)
            RETURN labels(n) as labels, properties(n) as props
            """
            nodes = self.query(nodes_query)
            
            # Export all edges
            edges_query = """
            MATCH (a)-[r]->(b)
            RETURN 
                CASE WHEN a.id IS NOT NULL THEN a.id ELSE toString(id(a)) END as src_id,
                type(r) as rel_type,
                CASE WHEN b.id IS NOT NULL THEN b.id ELSE toString(id(b)) END as dst_id,
                properties(r) as props
            """
            edges = self.query(edges_query)
            
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
        cypher = """
        MATCH (n)
        WHERE (n.id = $node_id OR id(n) = $node_id)
        DETACH DELETE n
        RETURN count(n) as deleted
        """
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, {'node_id': node_id})
                record = result.single()
                return record['deleted'] > 0 if record else False
        except Exception as e:
            print(f"Error deleting node: {e}")
            return False
    
    def delete_edge(self, src_id: str, rel_type: str, dst_id: str) -> bool:
        cypher = f"""
        MATCH (a)-[r:{rel_type}]->(b)
        WHERE (a.id = $src_id OR id(a) = $src_id)
        AND (b.id = $dst_id OR id(b) = $dst_id)
        DELETE r
        RETURN count(r) as deleted
        """
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(cypher, {
                    'src_id': src_id,
                    'dst_id': dst_id
                })
                record = result.single()
                return record['deleted'] > 0 if record else False
        except Exception as e:
            print(f"Error deleting edge: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()

