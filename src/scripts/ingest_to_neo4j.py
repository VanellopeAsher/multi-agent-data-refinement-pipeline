import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingestion.ingest_papers import PaperIngester


def main():
    print("=" * 60)
    print("Stage 1: Initial Graph Construction")
    print("=" * 60)
    
    ingester = PaperIngester()
    try:
        stats = ingester.ingest_all()
        
        print("\n" + "=" * 60)
        print("Stage 1 Complete!")
        print("=" * 60)
        print(f"Initial graph created in Neo4j")
        print(f"  Papers: {stats['papers']}")
        print(f"  Authors: {stats['authors']}")
        print(f"  Concepts: {stats['concepts']}")
        print(f"  Resources: {stats['resources']}")
        print(f"  Edges: {stats['edges']}")
    finally:
        ingester.close()


if __name__ == "__main__":
    main()

