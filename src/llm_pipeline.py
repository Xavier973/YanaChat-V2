import os
import time
import requests
from typing import Dict
from requests.exceptions import Timeout, RequestException
from dotenv import load_dotenv

load_dotenv()


class LLMPipeline:
    """Mistral API interface with robust retry and timeout handling."""
    
    def __init__(self):
        """Initialize with API credentials from .env"""
        self.api_url = os.getenv("MISTRAL_API_URL")
        self.api_key = os.getenv("MISTRAL_API_KEY")
        # self.model = "mistral-large-latest"
        # self.model = "mistral-small-2506"
        # self.model = "mistral-medium-2508"
        self.model = "ministral-14b-2512"
        if not self.api_url or not self.api_key:
            raise ValueError("MISTRAL_API_URL and MISTRAL_API_KEY must be set in .env")
    
    def generate(self, user_query: str) -> Dict:
        """
        Generate response via Mistral API.
        
        Args:
            user_query: User's question or prompt
            
        Returns:
            Dict with 'response' and 'latency_ms' keys
        """
        system_prompt = "Tu es un assistant expert et utile. Génère des réponses informées, structurées et détaillées."
        
        start_time = time.time()
        response_text = self._call_mistral_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_query
        )
        end_time = time.time()
        
        latency_ms = int((end_time - start_time) * 1000)
        
        return {
            "response": response_text,
            "latency_ms": latency_ms
        }
    
    def _call_mistral_with_retry(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """
        Call Mistral API with exponential backoff retry.
        
        Retry strategy: 2s, 4s, 8s backoff on timeout
        Timeout: 60 seconds per request
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User's query
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response text or fallback message on failure
        """
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7
                    },
                    timeout=60
                )
                response.raise_for_status()
                
                return response.json()["choices"][0]["message"]["content"]
                
            except Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return "Désolé, la requête a dépassé le délai d'attente. Veuillez réessayer."
                    
            except RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return f"Désolé, une erreur s'est produite: {str(e)[:100]}"
        
        return "Désolé, service indisponible."
