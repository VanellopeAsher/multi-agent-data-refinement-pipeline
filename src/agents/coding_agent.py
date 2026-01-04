import json
from typing import List
from src.agents.base import BaseAgent
from src.pipeline.schemas import NormalizedUpdate, GraphUpdate, NodeUpdate, EdgeUpdate
from src.graph_store.base_store import BaseGraphStore


class CodingAgent(BaseAgent):
    """Converts validated evidence into graph-level patches."""
    
    def __init__(self, graph_store: BaseGraphStore):
        super().__init__(graph_store, 'codingagent')
    
    def run(self, normalized_updates: List[NormalizedUpdate]) -> GraphUpdate:
        graph_update = GraphUpdate()
        
        # Group updates by entity
        entity_updates = {}
        for update in normalized_updates:
            entity_id = update.entity_id
            if entity_id not in entity_updates:
                entity_updates[entity_id] = []
            entity_updates[entity_id].append(update)
        
        # Process each entity
        for entity_id, updates in entity_updates.items():
            entity = self.graph_store.get_node(entity_id)
            if not entity:
                continue
            
            # Determine entity type
            entity_type = updates[0].entity_type
            
            # Collect field updates
            field_updates = {}
            for update in updates:
                field = update.metadata.get('field', '')
                if field:
                    field_updates[field] = update.normalized_value
            
            # Create node update
            if field_updates:
                node_update = NodeUpdate(
                    operation='update',
                    node_type=entity_type,
                    node_id=entity_id,
                    fields=field_updates
                )
                graph_update.node_updates.append(node_update)
            
            # Handle special cases
            for update in updates:
                if update.entity_type == 'Edge' and 'citation_context' in update.metadata.get('field', ''):
                    # Update CITES edge with citation context
                    # Need to find the edge
                    src_id = update.metadata.get('src_id', '')
                    dst_id = update.metadata.get('dst_id', '')
                    if src_id and dst_id:
                        edge_update = EdgeUpdate(
                            operation='update',
                            src_id=src_id,
                            rel_type='CITES',
                            dst_id=dst_id,
                            properties={
                                'citation_context': update.normalized_value,
                                'sentiment': 'neutral'  # Could be extracted from context
                            }
                        )
                        graph_update.edge_updates.append(edge_update)
        
        # Use LLM to identify additional updates (e.g., resource extraction)
        if normalized_updates:
            prompt = f"""
            Based on the following normalized updates, identify additional graph updates:
            1. New resources (datasets/models/tools) mentioned in papers
            2. Missing USES edges between papers and resources
            3. Duplicate nodes that should be merged
            
            Normalized Updates:
            {json.dumps([u.dict() for u in normalized_updates[:10]], indent=2)[:2000]}
            
            Return JSON array of additional NodeUpdate and EdgeUpdate objects.
            """
            
            try:
                llm_response = self.call_llm(prompt, temperature=0.3)
                # Parse LLM response for additional updates
                # (Simplified - in production would parse JSON properly)
            except Exception as e:
                print(f"Error in LLM-based coding: {e}")
        
        return graph_update

