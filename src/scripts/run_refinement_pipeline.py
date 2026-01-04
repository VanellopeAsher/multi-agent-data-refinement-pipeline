import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.pipeline.orchestrator import MultiAgentRefinementPipeline
from src.graph_store.neo4j_store import Neo4jGraphStore
from src.config import INTERMEDIATE_DIR
from src.exceptions import TavilyQuotaExceededError


def main(round_number: int = 1, resume: bool = True):
    print("=" * 60)
    print(f"Stage 2: Multi-Agent Refinement Pipeline (Round {round_number})")
    print("=" * 60)
    
    graph_store = Neo4jGraphStore()
    try:
        pipeline = MultiAgentRefinementPipeline(graph_store, round_number=round_number)
        results = pipeline.run(resume=resume)
        
        issues_file = os.path.join(INTERMEDIATE_DIR, f"issues_round{round_number}.json")
        with open(issues_file, 'w', encoding='utf-8') as f:
            json.dump(results['issues'], f, ensure_ascii=False, indent=2)
        
        search_file = os.path.join(INTERMEDIATE_DIR, f"search_results_round{round_number}.json")
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(results['search_results'], f, ensure_ascii=False, indent=2)
        
        normalized_file = os.path.join(INTERMEDIATE_DIR, f"normalized_round{round_number}.json")
        with open(normalized_file, 'w', encoding='utf-8') as f:
            json.dump(results['normalized_updates'], f, ensure_ascii=False, indent=2)
        
        updates_file = os.path.join(INTERMEDIATE_DIR, f"graph_updates_round{round_number}.json")
        with open(updates_file, 'w', encoding='utf-8') as f:
            json.dump(results['final_update'], f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print("Stage 2 Complete!")
        print("=" * 60)
        print(f"Refined graph updated in Neo4j")
        print(f"  Issues detected: {results['statistics']['issues_detected']}")
        print(f"  Node updates applied: {results['statistics']['node_updates_applied']}")
        print(f"  Edge updates applied: {results['statistics']['edge_updates_applied']}")
        print(f"\nIntermediate files saved to: data/intermediate/")
    except TavilyQuotaExceededError:
        print("\n⚠️  Pipeline stopped due to Tavily API quota exceeded.")
        print("Please add credits to your Tavily account and run again with --resume flag.")
        sys.exit(1)
    finally:
        graph_store.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run multi-agent refinement pipeline')
    parser.add_argument('--round', type=int, default=1, help='Refinement round number')
    parser.add_argument('--resume', action='store_true', default=True, help='Resume from checkpoint if exists')
    parser.add_argument('--no-resume', dest='resume', action='store_false', help='Do not resume from checkpoint')
    args = parser.parse_args()
    main(round_number=args.round, resume=args.resume)

