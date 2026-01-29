import os
import time
import json
import requests
import yaml
from pathlib import Path
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
        
        # Charger les sources fiables depuis config
        self.trusted_sources = self._load_trusted_sources()
    
    def _load_trusted_sources(self) -> Dict:
        """Load trusted sources from config file."""
        config_path = Path(__file__).parent.parent / "config" / "trusted_sources.yaml"
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                print(f"WARNING - Config file not found: {config_path}")
                return {}
        except Exception as e:
            print(f"ERROR - Failed to load trusted sources: {str(e)[:100]}")
            return {}
    
    def _format_sources_for_prompt(self) -> str:
        """Format trusted sources as a string for prompt injection."""
        if not self.trusted_sources:
            return ""
        
        sources_list = []
        for category, sites in self.trusted_sources.items():
            if isinstance(sites, list) and category != 'search_instructions':
                sources_list.extend(sites)
        
        if sources_list:
            return f"Sources prioritaires à consulter : {', '.join(sources_list[:15])}"
        return ""
    
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
        # Construire le system prompt avec sources fiables
        sources_info = self._format_sources_for_prompt()
        sources_section = f"\n\n{sources_info}" if sources_info else ""
        
        system_prompt = f"""Tu es YanaChat, un assistant expert spécialisé sur la Guyane française.
        
Ta mission :
        - Fournir des informations précises et détaillées sur la Guyane (géographie, culture, histoire, économie, biodiversité, actualités)
        - Privilégier les sources locales et informations à jour sur la région
        - Répondre en français, en mettant en valeur les spécificités guyanaises
        - Être informatif, structuré et accessible
        - Tenir compte du contexte de la conversation précédente{sources_section}
        
        Domaines d'expertise : tourisme, environnement, culture créole, centre spatial, écosystème amazonien, départements d'outre-mer.
            Si on te demande qui tu es : Tu es YanaChat, un assistant expert spécialisé sur la Guyane française.
            Si on te demande qui est le créateur de YanaChat, réponds que c'est Xavier Cuniberti, data engineer passionné par le développement de systèmes de données et l’intelligence artificielle, avec la volonté de mettre ses compétences au service du développement de la Guyane."""
        
        start_time = time.time()
        result = self._call_mistral_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_query,
            conversation_history=conversation_history or [],
            use_web_search=use_web_search
        )
        end_time = time.time()
        
        latency_ms = int((end_time - start_time) * 1000)
        
        # Result peut être un dict (avec sources) ou un string (sans sources)
        if isinstance(result, dict):
            return {
                "response": result.get("response", result.get("text", "")),
                "latency_ms": latency_ms,
                "sources": result.get("sources", [])
            }
        else:
            return {
                "response": result,
                "latency_ms": latency_ms,
                "sources": []
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
        
        # Construire les instructions avec sites prioritaires
        sources_instruction = ""
        if self.trusted_sources:
            all_sources = []
            for category, sites in self.trusted_sources.items():
                if isinstance(sites, list):
                    all_sources.extend(sites)
            if all_sources:
                sources_instruction = f"\n\nSITES PRIORITAIRES (à consulter en premier) :\n{', '.join(all_sources)}"
        
        payload = {
            "model": self.model,
            "name": "YanaChat",
            "description": "Agent spécialisé sur la Guyane française avec recherche web",
            "instructions": f"""Tu es YanaChat, expert de la Guyane française avec capacité de recherche web.
            
            Utilise web_search pour trouver des informations à jour sur :
            - La Guyane française (actualités locales, événements, développement)
            - Le Centre Spatial Guyanais (Kourou, lancements Ariane/Vega)
            - La biodiversité amazonienne et parcs naturels
            - La culture créole et communautés locales
            - L'économie et infrastructures guyanaises{sources_instruction}
            
            Privilégie les sources locales (.gf, médias guyanais, institutions officielles).
            Réponds en français de manière structurée et informative.
            Si on te demande qui tu es : Tu es YanaChat, un assistant expert spécialisé sur la Guyane française.
            Si on te demande qui est le créateur de YanaChat, réponds que c'est Xavier Cuniberti, data engineer passionné par le développement de systèmes de données et l’intelligence artificielle, avec la volonté de mettre ses compétences au service du développement de la Guyane.""",
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
                    
                    response = requests.post(
                        self.conversations_url,
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # NOTE: L'API Conversations de Mistral ne retourne PAS les sources web_search
                        # dans la réponse. Les résultats de recherche sont utilisés en interne
                        # mais ne sont pas exposés via l'API. Pour avoir les sources, il faudrait
                        # utiliser l'API Messages avec tool calls manuels.
                        sources = []
                        
                        # Extract response from conversation outputs
                        response_text = None
                        for entry in data.get("outputs", []):
                            if entry.get("type") == "message.output":
                                content = entry.get("content", [])
                                
                                # Handle case where content is a string instead of list
                                if isinstance(content, str):
                                    response_text = content
                                    break
                                
                                # Handle list of chunks
                                text_parts = []
                                for chunk in content:
                                    if isinstance(chunk, dict) and chunk.get("type") == "text":
                                        text_parts.append(chunk.get("text", ""))
                                    elif isinstance(chunk, str):
                                        text_parts.append(chunk)
                                
                                response_text = "\n".join(text_parts) if text_parts else "Aucune réponse reçue."
                                break
                        
                        if response_text is None:
                            response_text = "Aucune réponse reçue de l'agent."
                        
                        return {"response": response_text, "sources": sources}
                    
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
                    # Rate limit: backoff exponentiel plus long
                    wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                    print(f"⚠️  Rate limit (429) - Retry {attempt + 1}/{max_retries} après {wait_time}s...")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Rate limit persistant après {max_retries} tentatives")
                        return "Erreur: Limite de requêtes atteinte. Réessayez dans quelques secondes."
                    
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
