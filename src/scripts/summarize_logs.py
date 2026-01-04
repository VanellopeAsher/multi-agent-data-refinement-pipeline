"""
Summarize token usage for all agents.
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import AGENT_LOGS_DIR, GLOBAL_LOGS_DIR


def summarize_agent_logs(agent_name: str) -> dict:
    """
    Summarize logs for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Summary dictionary
    """
    log_file = os.path.join(AGENT_LOGS_DIR, f"{agent_name}_llm_log.json")
    
    if not os.path.exists(log_file):
        return {
            'agent': agent_name,
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    return {
        'agent': agent_name,
        'total_calls': len(data.get('records', [])),
        'total_input_tokens': summary.get('total_input_tokens', 0),
        'total_output_tokens': summary.get('total_output_tokens', 0),
        'total_cost': summary.get('total_cost', 0.0)
    }


def summarize_global_logs() -> dict:
    """
    Summarize global logs.
    
    Returns:
        Global summary dictionary
    """
    log_file = os.path.join(GLOBAL_LOGS_DIR, "llm_usage_log.json")
    
    if not os.path.exists(log_file):
        return {
            'total_calls': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0.0
        }
    
    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    return {
        'total_calls': len(data.get('records', [])),
        'total_input_tokens': summary.get('total_input_tokens', 0),
        'total_output_tokens': summary.get('total_output_tokens', 0),
        'total_cost': summary.get('total_cost', 0.0)
    }


def get_top_prompts(agent_name: str, top_n: int = 5) -> list:
    """
    Get top prompts by token usage for an agent.
    
    Args:
        agent_name: Name of the agent
        top_n: Number of top prompts to return
        
    Returns:
        List of top prompts
    """
    log_file = os.path.join(AGENT_LOGS_DIR, f"{agent_name}_llm_log.json")
    
    if not os.path.exists(log_file):
        return []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data.get('records', [])
    # Sort by total tokens
    sorted_records = sorted(records, key=lambda x: x.get('total_tokens', 0), reverse=True)
    
    return [
        {
            'prompt': r.get('prompt', '')[:200],  # Truncate
            'total_tokens': r.get('total_tokens', 0),
            'cost': r.get('total_cost', 0.0)
        }
        for r in sorted_records[:top_n]
    ]


def main():
    """Generate summary of token usage."""
    print("=" * 60)
    print("Token Usage Summary")
    print("=" * 60)
    
    agents = ['diagnoseagent', 'searchagent', 'normalizationagent', 'codingagent', 'reviewagent']
    
    # Per-agent summaries
    print("\nPer-Agent Summary:")
    print("-" * 60)
    agent_summaries = []
    for agent in agents:
        summary = summarize_agent_logs(agent)
        agent_summaries.append(summary)
        print(f"\n{agent.upper()}:")
        print(f"  Total calls: {summary['total_calls']}")
        print(f"  Input tokens: {summary['total_input_tokens']:,}")
        print(f"  Output tokens: {summary['total_output_tokens']:,}")
        print(f"  Total cost: ¥{summary['total_cost']:.6f}")
    
    # Global summary
    print("\n" + "-" * 60)
    print("Global Summary:")
    print("-" * 60)
    global_summary = summarize_global_logs()
    print(f"Total calls: {global_summary['total_calls']}")
    print(f"Total input tokens: {global_summary['total_input_tokens']:,}")
    print(f"Total output tokens: {global_summary['total_output_tokens']:,}")
    print(f"Total cost: ¥{global_summary['total_cost']:.6f}")
    
    # Top prompts
    print("\n" + "-" * 60)
    print("Top Prompts (by token usage):")
    print("-" * 60)
    for agent in agents:
        top_prompts = get_top_prompts(agent, top_n=3)
        if top_prompts:
            print(f"\n{agent.upper()}:")
            for i, prompt_info in enumerate(top_prompts, 1):
                print(f"  {i}. Tokens: {prompt_info['total_tokens']}, Cost: ¥{prompt_info['cost']:.6f}")
                print(f"     Prompt: {prompt_info['prompt']}...")
    
    # Save summary to file
    summary_data = {
        'agents': agent_summaries,
        'global': global_summary,
        'top_prompts': {agent: get_top_prompts(agent, top_n=5) for agent in agents}
    }
    
    summary_file = os.path.join(GLOBAL_LOGS_DIR, "usage_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")


if __name__ == "__main__":
    main()

