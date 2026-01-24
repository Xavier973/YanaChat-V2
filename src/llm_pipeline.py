import os
import time
import json
import requests
from typing import Dict
from requests.exceptions import Timeout, RequestException
from dotenv import load_dotenv

load_dotenv()


class LLMPipeline:
    """Mistral API interface with robust retry and timeout handling."""
    
    def __init__(self):
        """Initialize with API credentials from .env"""
        self.chat_url = "https://api.mistral.ai/v1/chat/completions"
        self.agents_url = "https://api.mistral.ai/v1/agents"
        self.conversations_url = "https://api.mistral.ai/v1/conversations"
        self.api_key = os.getenv("MISTRAL_API_KEY")
        # self.model = "mistral-large-latest"
        self.model = "mistral-small-2506"
        # self.model = "mistral-medium-2508"
        # self.model = "ministral-14b-2512"
        
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY must be set in .env")
        
        # Cache pour l'agent de websearch (créé une seule fois)
        self._websearch_agent_id = None
    
    def generate(self, user_query: str, conversation_history: list = None, use_web_search: bool = False) -> Dict:
        """
        Generate response via Mistral API with conversation history.
        
        Args:
            user_query: User's question or prompt
            conversation_history: List of previous messages [{"role": "user"/"assistant", "content": str}]
            use_web_search: Enable web search for up-to-date information
            
        Returns:
            Dict with 'response' and 'latency_ms' keys
        """
        system_prompt = """Tu es YanaChat, un assistant expert spécialisé sur la Guyane française.
        
Ta mission :
        - Fournir des informations précises et détaillées sur la Guyane (géographie, culture, histoire, économie, biodiversité, actualités)
        - Privilégier les sources locales et informations à jour sur la région
        - Répondre en français, en mettant en valeur les spécificités guyanaises
        - Être informatif, structuré et accessible
        - Tenir compte du contexte de la conversation précédente
        
        Domaines d'expertise : tourisme, environnement, culture créole, centre spatial, écosystème amazonien, départements d'outre-mer."""
        
        start_time = time.time()
        response_text = self._call_mistral_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_query,
            conversation_history=conversation_history or [],
            use_web_search=use_web_search
        )
        end_time = time.time()
        
        latency_ms = int((end_time - start_time) * 1000)
        
        return {
            "response": response_text,
            "latency_ms": latency_ms
        }
    
    def _get_or_create_websearch_agent(self) -> str:
        """
        Get or create a websearch agent using Mistral Agents API.
        Agent is cached for reuse across multiple requests.
        
        Returns:
            Agent ID string
        """
        if self._websearch_agent_id:
            return self._websearch_agent_id
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "name": "YanaChat Guyane Websearch Agent",
            "description": "Agent spécialisé sur la Guyane française avec recherche web",
            "instructions": """Tu es YanaChat, expert de la Guyane française avec capacité de recherche web.
            
            Utilise web_search pour trouver des informations à jour sur :
            - La Guyane française (actualités locales, événements, développement)
            - Le Centre Spatial Guyanais (Kourou, lancements Ariane/Vega)
            - La biodiversité amazonienne et parcs naturels
            - La culture créole et communautés locales
            - L'économie et infrastructures guyanaises
            
            Privilégie les sources locales (.gf, médias guyanais, institutions officielles).
            Réponds en français de manière structurée et informative.""",
            "tools": [{"type": "web_search"}],
            "completion_args": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.95
            }
        }
        
        try:
            response = requests.post(
                self.agents_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self._websearch_agent_id = data["id"]
                print(f"DEBUG - Created websearch agent: {self._websearch_agent_id}")
                return self._websearch_agent_id
            else:
                print(f"ERROR - Failed to create agent: {response.status_code} {response.text[:500]}")
                raise Exception(f"Agent creation failed: {response.status_code}")
                
        except Exception as e:
            print(f"ERROR - Agent creation exception: {str(e)[:100]}")
            raise
    
    def _call_mistral_with_retry(self, system_prompt: str, user_prompt: str, conversation_history: list = None, use_web_search: bool = False, max_retries: int = 3) -> str:
        """
        Call Mistral API with exponential backoff retry and conversation history.
        
        Uses Conversations API when web_search is enabled, otherwise uses Chat Completions.
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User's query
            conversation_history: Previous messages in the conversation
            use_web_search: Enable web search via Agents/Conversations API
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response text or fallback message on failure
        """
        conversation_history = conversation_history or []
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                if use_web_search:
                    # Use Agents/Conversations API for web search
                    agent_id = self._get_or_create_websearch_agent()
                    
                    payload = {
                        "agent_id": agent_id,
                        "inputs": [{"role": "user", "content": user_prompt}]
                    }
                    
                    print(f"DEBUG - Websearch conversation (agent_id={agent_id})")
                    
                    response = requests.post(
                        self.conversations_url,
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"DEBUG - Conversation response keys: {list(data.keys())}")
                        
                        # Extract response from conversation outputs (not "entries")
                        for entry in data.get("outputs", []):
                            if entry.get("type") == "message.output":
                                content = entry.get("content", [])
                                
                                # Handle case where content is a string instead of list
                                if isinstance(content, str):
                                    print(f"DEBUG - Content is string, length: {len(content)}")
                                    return content
                                
                                # Handle list of chunks
                                text_parts = []
                                for chunk in content:
                                    if isinstance(chunk, dict) and chunk.get("type") == "text":
                                        text_parts.append(chunk.get("text", ""))
                                    elif isinstance(chunk, str):
                                        text_parts.append(chunk)
                                
                                result = "\n".join(text_parts) if text_parts else "Aucune réponse reçue."
                                print(f"DEBUG - Extracted text length: {len(result)}")
                                return result
                        return "Aucune réponse reçue de l'agent."
                    
                else:
                    # Standard Chat Completions API avec historique
                    messages = [{"role": "system", "content": system_prompt}]
                    
                    # Ajouter l'historique de conversation
                    messages.extend(conversation_history)
                    
                    # Ajouter le message actuel de l'utilisateur
                    messages.append({"role": "user", "content": user_prompt})
                    
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 2048
                    }
                    
                    response = requests.post(
                        self.chat_url,
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                
                # Common error handling for both paths
                if response.status_code == 400:
                    error_msg = response.json().get("message", "Bad request")
                    print(f"ERROR 400: {error_msg}")
                    return f"Erreur API: {error_msg}"
                    
                elif response.status_code == 401:
                    return "Erreur: Clé API invalide."
                    
                elif response.status_code == 422:
                    error_msg = response.text[:200]
                    print(f"ERROR 422: {error_msg}")
                    # Retry without web search if it failed
                    if use_web_search:
                        print("Retrying without web search...")
                        return self._call_mistral_with_retry(system_prompt, user_prompt, conversation_history, use_web_search=False, max_retries=1)
                    return f"Erreur de validation: {error_msg}"
                    
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        print(f"Rate limit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return "Erreur: Limite de requêtes atteinte."
                    
                else:
                    print(f"HTTP {response.status_code}: {response.text[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return f"Erreur HTTP {response.status_code}"
                    
            except Timeout:
                print(f"Timeout attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Désolé, délai d'attente dépassé."
                
            except RequestException as e:
                print(f"Network error: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"Erreur réseau: {str(e)[:100]}"
            
            except Exception as e:
                print(f"Unexpected error: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"Erreur inattendue: {str(e)[:100]}"
        
        return "Désolé, service indisponible."
