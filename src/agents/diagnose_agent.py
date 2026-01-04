import json
from typing import List
from src.agents.base import BaseAgent
from src.pipeline.schemas import RefinementIssue
from src.graph_store.base_store import BaseGraphStore


class DiagnoseAgent(BaseAgent):
    """Detects structural issues in the knowledge graph."""
    
    def __init__(self, graph_store: BaseGraphStore):
        super().__init__(graph_store, 'diagnoseagent')
    
    def run(self) -> List[RefinementIssue]:
        issues = []
        
        # Query graph for potential issues
        # 1. Papers with missing fields
        missing_fields_query = """
        MATCH (p:Paper)
        WHERE p.title IS NULL OR p.title = '' OR 
              p.year IS NULL OR 
              p.venue IS NULL OR p.venue = ''
        RETURN p.id as id, labels(p) as labels, properties(p) as props
        LIMIT 100
        """
        missing_nodes = self.graph_store.query(missing_fields_query)
        
        for node in missing_nodes:
            props = node.get('props', {})
            missing_fields = []
            if not props.get('title'):
                missing_fields.append('title')
            if not props.get('year'):
                missing_fields.append('year')
            if not props.get('venue'):
                missing_fields.append('venue')
            
            issues.append(RefinementIssue(
                issue_type='missing_field',
                entity_type='Paper',
                entity_id=props.get('id', ''),
                description=f"Missing fields: {', '.join(missing_fields)}",
                severity='high' if 'title' in missing_fields else 'medium',
                metadata={'missing_fields': missing_fields}
            ))
        
        # 2. Authors without affiliations
        authors_query = """
        MATCH (a:Author)
        WHERE a.affiliation IS NULL OR a.affiliation = ''
        RETURN a.id as id, properties(a) as props
        LIMIT 100
        """
        author_nodes = self.graph_store.query(authors_query)
        
        for node in author_nodes:
            props = node.get('props', {})
            issues.append(RefinementIssue(
                issue_type='missing_field',
                entity_type='Author',
                entity_id=props.get('id', ''),
                description="Missing affiliation",
                severity='low',
                metadata={}
            ))
        
        # 3. Papers without concepts
        no_concepts_query = """
        MATCH (p:Paper)
        WHERE NOT (p)-[:CENTERS_ON]->(:Concept)
        RETURN p.id as id, properties(p) as props
        LIMIT 100
        """
        papers_no_concepts = self.graph_store.query(no_concepts_query)
        
        for node in papers_no_concepts:
            props = node.get('props', {})
            issues.append(RefinementIssue(
                issue_type='missing_relationship',
                entity_type='Paper',
                entity_id=props.get('id', ''),
                description="Paper has no concepts",
                severity='medium',
                metadata={}
            ))
        
        # 4. CITES edges without citation_context
        cites_query = """
        MATCH (p1:Paper)-[r:CITES]->(p2:Paper)
        WHERE r.citation_context IS NULL OR r.citation_context = ''
        RETURN p1.id as src_id, p2.id as dst_id, properties(r) as props
        LIMIT 100
        """
        cites_edges = self.graph_store.query(cites_query)
        
        for edge in cites_edges:
            issues.append(RefinementIssue(
                issue_type='missing_field',
                entity_type='Edge',
                entity_id=f"{edge['src_id']}-CITES-{edge['dst_id']}",
                description="CITES edge missing citation_context",
                severity='medium',
                metadata={
                    'src_id': edge['src_id'],
                    'dst_id': edge['dst_id'],
                    'rel_type': 'CITES'
                }
            ))
        
        # Use LLM to detect more complex issues
        if issues:
            prompt = f"""
            Analyze the following graph issues and identify any additional problems:
            
            {json.dumps([issue.dict() for issue in issues[:20]], indent=2)}
            
            Identify:
            1. Duplicate nodes (same entity with different IDs)
            2. Inconsistent author names
            3. Missing resources (datasets/models mentioned but not in graph)
            4. Malformed relationships
            
            Return JSON array of additional RefinementIssue objects.
            """
            
            try:
                llm_response = self.call_llm(prompt, temperature=0.3)
                # Parse LLM response for additional issues
                # (Simplified - in production would parse JSON properly)
            except Exception as e:
                print(f"Error in LLM-based diagnosis: {e}")
        
        return issues

