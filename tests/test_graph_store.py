"""
Tests for graph store module.
"""
import unittest
from src.graph_store.in_memory_store import InMemoryGraphStore


class TestInMemoryGraphStore(unittest.TestCase):
    """Test in-memory graph store."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.store = InMemoryGraphStore()
    
    def test_upsert_node(self):
        """Test node upsertion."""
        node_id = self.store.upsert_node(['Paper'], {
            'id': 'P1',
            'title': 'Test Paper'
        })
        
        self.assertEqual(node_id, 'P1')
        
        node = self.store.get_node('P1')
        self.assertIsNotNone(node)
        self.assertEqual(node['title'], 'Test Paper')
    
    def test_add_edge(self):
        """Test edge addition."""
        src_id = self.store.upsert_node(['Paper'], {'id': 'P1', 'title': 'Paper 1'})
        dst_id = self.store.upsert_node(['Paper'], {'id': 'P2', 'title': 'Paper 2'})
        
        result = self.store.add_edge(src_id, 'CITES', dst_id)
        self.assertTrue(result)
        
        # Query edges
        edges = self.store.query("MATCH (a)-[r]->(b) RETURN r")
        self.assertGreater(len(edges), 0)
    
    def test_export_snapshot(self):
        """Test snapshot export."""
        self.store.upsert_node(['Paper'], {'id': 'P1', 'title': 'Test'})
        self.store.upsert_node(['Paper'], {'id': 'P2', 'title': 'Test 2'})
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            result = self.store.export_snapshot(temp_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(temp_path))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()

