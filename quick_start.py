"""
Quick start script to verify system setup and run basic tests.
"""
import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment is properly configured."""
    print("=" * 60)
    print("Environment Check")
    print("=" * 60)
    
    issues = []
    
    # Check .env file
    if not os.path.exists('.env'):
        issues.append("❌ .env file not found. Please create it from .env.example")
    else:
        print("✅ .env file exists")
    
    # Check required directories
    required_dirs = [
        'data/raw',
        'data/pdfs',
        'data/intermediate',
        'data/refined',
        'logs/agents',
        'logs/global'
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
        else:
            print(f"✅ Directory exists: {dir_path}")
    
    # Check Python packages
    print("\nChecking Python packages...")
    required_packages = [
        'dotenv',
        'openai',
        'requests',
        'neo4j',
        'pydantic',
        'PyPDF2'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            elif package == 'PyPDF2':
                __import__('PyPDF2')
            else:
                __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} not installed")
    
    if missing_packages:
        issues.append(f"Missing packages: {', '.join(missing_packages)}")
        print(f"\n⚠️  Install missing packages: pip install {' '.join(missing_packages)}")
    
    # Check environment variables
    print("\nChecking environment variables...")
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'MODEL_NAME',
        'PLATFORM',
        'NEO4J_URI',
        'NEO4J_USER',
        'NEO4J_PASSWORD'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} is set")
        else:
            issues.append(f"{var} not set in .env")
            print(f"❌ {var} not set")
    
    # Summary
    print("\n" + "=" * 60)
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before running the pipeline.")
        return False
    else:
        print("✅ Environment check passed!")
        return True

def test_imports():
    """Test if all modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Imports")
    print("=" * 60)
    
    modules = [
        'src.config',
        'src.utils',
        'src.llm_logger',
        'src.graph_store.base_store',
        'src.graph_store.neo4j_store',
        'src.graph_store.in_memory_store',
        'src.data_collection.openalex_fetcher',
        'src.data_collection.arxiv_fetcher',
        'src.ingestion.schema_mapping',
        'src.ingestion.ingest_papers',
        'src.pipeline.schemas',
        'src.pipeline.orchestrator',
        'src.agents.base',
        'src.agents.diagnose_agent',
        'src.agents.search_agent',
        'src.agents.normalization_agent',
        'src.agents.coding_agent',
        'src.agents.review_agent',
        'src.evaluation.metrics',
        'src.evaluation.run_evaluation'
    ]
    
    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")
            failed.append(module)
    
    if failed:
        print(f"\n⚠️  Failed to import {len(failed)} modules")
        return False
    else:
        print("\n✅ All modules imported successfully!")
        return True

def test_graph_store():
    """Test graph store functionality."""
    print("\n" + "=" * 60)
    print("Testing Graph Store")
    print("=" * 60)
    
    try:
        from src.graph_store.in_memory_store import InMemoryGraphStore
        
        store = InMemoryGraphStore()
        
        # Test node creation
        node_id = store.upsert_node(['Paper'], {'id': 'test1', 'title': 'Test Paper'})
        print(f"✅ Created node: {node_id}")
        
        # Test node retrieval
        node = store.get_node('test1')
        if node and node.get('title') == 'Test Paper':
            print("✅ Node retrieval works")
        else:
            print("❌ Node retrieval failed")
            return False
        
        # Test edge creation
        node_id2 = store.upsert_node(['Paper'], {'id': 'test2', 'title': 'Test Paper 2'})
        result = store.add_edge('test1', 'CITES', 'test2')
        if result:
            print("✅ Edge creation works")
        else:
            print("❌ Edge creation failed")
            return False
        
        # Test query
        nodes = store.query("MATCH (n) RETURN n")
        if len(nodes) >= 2:
            print(f"✅ Query works ({len(nodes)} nodes found)")
        else:
            print("❌ Query failed")
            return False
        
        store.close()
        print("✅ Graph store tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Graph store test failed: {e}")
        return False

def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("Multi-Agent Refinement Pipeline - Quick Start Check")
    print("=" * 60)
    
    results = []
    
    # Environment check
    results.append(("Environment", check_environment()))
    
    # Import test
    results.append(("Imports", test_imports()))
    
    # Graph store test
    results.append(("Graph Store", test_graph_store()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Run Stage 0: python -m src.scripts.prepare_data")
        print("  2. Run Stage 1: python -m src.scripts.ingest_to_neo4j")
        print("  3. Run Stage 2: python -m src.scripts.run_refinement_pipeline")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
    print("=" * 60)

if __name__ == "__main__":
    main()

