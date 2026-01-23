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
    
    def handle_query(self, user_query: str, session_id: Optional[str] = None, use_web_search: bool = False) -> Dict:
        """
        Handle user query: LLM generation + JSONL logging.
        
        Args:
            user_query: User's input text
            session_id: Optional session identifier for grouping queries
            use_web_search: Enable web search for up-to-date information
            
        Returns:
            Dict with 'response' key containing the LLM's response
        """
        # Generate response via Mistral
        result = self.llm_pipeline.generate(user_query, use_web_search=use_web_search)
        
        # Add web_search flag to result for logging
        result["web_search"] = use_web_search
        
        # Log interaction (JSONL format)
        self._log_interaction(
            query=user_query,
            response=result,
            session_id=session_id or "anonymous"
        )
        
        # Log interaction (readable format)
        self._log_interaction_readable(
            query=user_query,
            response=result
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
            "web_search": response.get("web_search", False),
            "query": query,
            "response": response.get("response", "")[:500],
            "latency_ms": response.get("latency_ms", 0)
        }
        
        try:
            with open(self.log_path, "a", encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except IOError as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def _log_interaction_readable(self, query: str, response: Dict) -> None:
        """
        Append interaction to readable text log for manual evaluation.
        
        Format:
            [timestamp] model | Query: "query" | Latency: Xms
            Réponse:
            response text with indentation
            
            ---
            
        Args:
            query: User's input
            response: LLM response dict
        """
        readable_log_path = Path("logs/interactions.log")
        
        try:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            model = self.llm_pipeline.model
            latency_ms = response.get("latency_ms", 0)
            web_search = response.get("web_search", False)
            response_text = response.get("response", "")
            
            # Format the log entry
            web_indicator = " [WEB SEARCH]" if web_search else ""
            header = f"[{timestamp}] {model}{web_indicator} | Query: \"{query}\" | Latency: {latency_ms}ms\n"
            body = f"Réponse:\n{response_text}\n\n"
            separator = "---\n\n"
            
            with open(readable_log_path, "a", encoding='utf-8') as f:
                f.write(header)
                f.write(body)
                f.write(separator)
                
        except IOError as e:
            print(f"Warning: Could not write to readable log file: {e}")
