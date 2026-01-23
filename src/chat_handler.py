import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.llm_pipeline import LLMPipeline


class ChatHandler:
    """Orchestration layer: LLM + JSONL logging."""
    
    def __init__(self):
        """Initialize LLM pipeline and logging setup."""
        self.llm_pipeline = LLMPipeline()
        self.log_path = Path("logs/interactions.jsonl")
        self.log_path.parent.mkdir(exist_ok=True)
    
    def handle_query(self, user_query: str, session_id: Optional[str] = None) -> Dict:
        """
        Handle user query: LLM generation + JSONL logging.
        
        Args:
            user_query: User's input text
            session_id: Optional session identifier for grouping queries
            
        Returns:
            Dict with 'response' key containing the LLM's response
        """
        # Generate response via Mistral
        result = self.llm_pipeline.generate(user_query)
        
        # Log interaction
        self._log_interaction(
            query=user_query,
            response=result,
            session_id=session_id or "anonymous"
        )
        
        return result
    
    def _log_interaction(self, query: str, response: Dict, session_id: str) -> None:
        """
        Append interaction to JSONL audit log.
        
        Logs:
            - timestamp: ISO format datetime
            - session_id: User session identifier
            - model: LLM model used
            - query: User's question
            - response: LLM's response (truncated to 500 chars)
            - latency_ms: Request latency in milliseconds
            
        Args:
            query: User's input
            response: LLM response dict
            session_id: Session identifier
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "model": self.llm_pipeline.model,
            "query": query,
            "response": response.get("response", "")[:500],
            "latency_ms": response.get("latency_ms", 0)
        }
        
        try:
            with open(self.log_path, "a", encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except IOError as e:
            print(f"Warning: Could not write to log file: {e}")
