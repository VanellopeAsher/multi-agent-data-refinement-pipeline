import json
from typing import List, Tuple
from src.agents.base import BaseAgent
from src.pipeline.schemas import GraphUpdate, ReviewedGraphUpdate, NodeUpdate, EdgeUpdate
from src.graph_store.base_store import BaseGraphStore


class ReviewAgent(BaseAgent):
    """Validates graph updates and filters low-confidence changes."""
    
    def __init__(self, graph_store: BaseGraphStore, confidence_threshold: float = 0.6):
        super().__init__(graph_store, 'reviewagent')
        self.confidence_threshold = confidence_threshold
    
    def validate_node_update(self, node_update: NodeUpdate) -> Tuple[bool, float, str]:
        # Check if node exists
        existing_node = self.graph_store.get_node(node_update.node_id)
        
        if node_update.operation == 'create':
            if existing_node:
                return False, 0.0, "Node already exists"
            return True, 0.8, "New node creation"
        
        elif node_update.operation == 'update':
            if not existing_node:
                return False, 0.0, "Node does not exist"
            
            # Validate field updates
            for field, value in node_update.fields.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    return False, 0.0, f"Invalid value for field {field}"
            
            return True, 0.7, "Field update"
        
        elif node_update.operation == 'merge':
            if not existing_node:
                return False, 0.0, "Source node does not exist"
            if not node_update.merge_with:
                return False, 0.0, "Missing merge target"
            
            target_node = self.graph_store.get_node(node_update.merge_with)
            if not target_node:
                return False, 0.0, "Target node does not exist"
            
            return True, 0.6, "Node merge"
        
        elif node_update.operation == 'delete':
            if not existing_node:
                return False, 0.0, "Node does not exist"
            return True, 0.5, "Node deletion"
        
        return False, 0.0, "Unknown operation"
    
    def validate_edge_update(self, edge_update: EdgeUpdate) -> Tuple[bool, float, str]:
        """
        Validate an edge update.
        
        Args:
            edge_update: Edge update to validate
            
        Returns:
            Tuple of (is_valid, confidence, reason)
        """
        # Check if nodes exist
        src_node = self.graph_store.get_node(edge_update.src_id)
        dst_node = self.graph_store.get_node(edge_update.dst_id)
        
        if not src_node:
            return False, 0.0, f"Source node {edge_update.src_id} does not exist"
        if not dst_node:
            return False, 0.0, f"Destination node {edge_update.dst_id} does not exist"
        
        if edge_update.operation == 'create':
            return True, 0.7, "New edge creation"
        elif edge_update.operation == 'update':
            return True, 0.6, "Edge property update"
        elif edge_update.operation == 'delete':
            return True, 0.5, "Edge deletion"
        
        return False, 0.0, "Unknown operation"
    
    def run(self, graph_update: GraphUpdate) -> ReviewedGraphUpdate:
        """
        Review and validate graph updates.
        
        Args:
            graph_update: Tentative graph update
            
        Returns:
            Reviewed graph update with filtered updates
        """
        reviewed_update = ReviewedGraphUpdate()
        
        # Validate node updates
        for node_update in graph_update.node_updates:
            is_valid, confidence, reason = self.validate_node_update(node_update)
            
            if is_valid and confidence >= self.confidence_threshold:
                reviewed_update.node_updates.append(node_update)
            elif is_valid and confidence < self.confidence_threshold:
                reviewed_update.pending_human.append({
                    'type': 'node_update',
                    'update': node_update.dict(),
                    'confidence': confidence,
                    'reason': reason
                })
            else:
                reviewed_update.rejected_updates.append({
                    'type': 'node_update',
                    'update': node_update.dict(),
                    'reason': reason
                })
        
        # Validate edge updates
        for edge_update in graph_update.edge_updates:
            is_valid, confidence, reason = self.validate_edge_update(edge_update)
            
            if is_valid and confidence >= self.confidence_threshold:
                reviewed_update.edge_updates.append(edge_update)
            elif is_valid and confidence < self.confidence_threshold:
                reviewed_update.pending_human.append({
                    'type': 'edge_update',
                    'update': edge_update.dict(),
                    'confidence': confidence,
                    'reason': reason
                })
            else:
                reviewed_update.rejected_updates.append({
                    'type': 'edge_update',
                    'update': edge_update.dict(),
                    'reason': reason
                })
        
        # Use LLM for additional validation
        if graph_update.node_updates or graph_update.edge_updates:
            prompt = f"""
            Review the following graph updates for correctness and completeness:
            
            Node Updates:
            {json.dumps([u.dict() for u in graph_update.node_updates[:5]], indent=2)[:1000]}
            
            Edge Updates:
            {json.dumps([u.dict() for u in graph_update.edge_updates[:5]], indent=2)[:1000]}
            
            Identify any potential issues:
            1. Inconsistent data types
            2. Invalid relationships
            3. Missing required fields
            4. Semantic errors
            
            Return JSON object with validation results.
            """
            
            try:
                llm_response = self.call_llm(prompt, temperature=0.2)
                # Parse LLM response for additional validation
                # (Simplified - in production would parse JSON properly)
            except Exception as e:
                print(f"Error in LLM-based review: {e}")
        
        return reviewed_update

