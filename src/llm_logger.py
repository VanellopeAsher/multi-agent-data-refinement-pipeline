"""
Logs token usage for each agent.
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from src.config import AGENT_LOGS_DIR, GLOBAL_LOGS_DIR, INPUT_COST_PER_M_TOKENS, OUTPUT_COST_PER_M_TOKENS


class LLMLogger:
    """Logger for tracking LLM token usage per agent."""
    
    def __init__(self, agent_name: str):
        """
        Initialize logger for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'diagnoseagent', 'searchagent')
        """
        self.agent_name = agent_name.lower()
        self.log_file = os.path.join(AGENT_LOGS_DIR, f"{self.agent_name}_llm_log.json")
        self.global_log_file = os.path.join(GLOBAL_LOGS_DIR, "llm_usage_log.json")
        
    def log_usage(
        self,
        prompt: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        model_name: Optional[str] = None,
        platform: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log token usage for a single LLM call.
        
        Args:
            prompt: The input prompt
            response: The LLM response
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            total_tokens: Total tokens used
            model_name: Model name used
            platform: Platform used
            metadata: Additional metadata to log
        """
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_M_TOKENS
        output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_M_TOKENS
        total_cost = input_cost + output_cost
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "model_name": model_name,
            "platform": platform,
            "prompt": prompt[:500] if len(prompt) > 500 else prompt,  # Truncate long prompts
            "response": response[:500] if len(response) > 500 else response,  # Truncate long responses
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "metadata": metadata or {}
        }
        
        # Log to agent-specific file
        self._append_to_file(self.log_file, log_entry)
        
        # Log to global file
        self._append_to_file(self.global_log_file, log_entry)
    
    def _append_to_file(self, filepath: str, entry: Dict[str, Any]):
        """Append log entry to JSON file."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {"records": []}
        else:
            data = {"records": []}
        
        if "records" not in data:
            data["records"] = []
        
        data["records"].append(entry)
        
        # Update summary
        if "summary" not in data:
            data["summary"] = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost": 0.0
            }
        
        data["summary"]["total_input_tokens"] += entry["input_tokens"]
        data["summary"]["total_output_tokens"] += entry["output_tokens"]
        data["summary"]["total_cost"] = round(
            data["summary"]["total_cost"] + entry["total_cost"], 6
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

