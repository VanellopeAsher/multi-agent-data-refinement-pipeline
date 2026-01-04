from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class BaseGraphStore(ABC):
    """Abstract base class for graph storage."""
    
    @abstractmethod
    def upsert_node(self, labels: List[str], fields: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    def add_edge(
        self,
        src_id: str,
        rel_type: str,
        dst_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def export_snapshot(self, path: str) -> bool:
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        pass
    
    @abstractmethod
    def delete_edge(self, src_id: str, rel_type: str, dst_id: str) -> bool:
        pass
    
    @abstractmethod
    def close(self):
        pass

