# YanaChat V2 — Instructions pour Copilot

**Stack** : FastAPI + Mistral LLM + JSONL Logging  
**Langue** : Français (FR)  
**État** : ✅ Implémenté et fonctionnel

---

## Objectif

Chatbot **YanaChat** spécialisé sur la **Guyane française**, générant des réponses détaillées via l'API Mistral (chat + agents API), avec logging double (JSONL + readable) pour audit.

---

## Architecture Implémentée

```
Requête utilisateur (web_search optionnel)
    ↓
FastAPI POST /api/chat
    ↓
ChatHandler (récupère historique par session_id)
    ↓
LLMPipeline (messages = system + historique + nouveau message)
    ↓
    ├─ Mode standard : Mistral Chat Completions API
    └─ Mode websearch : Mistral Agents API (cached agent)
    ↓
Stockage de l'échange dans historique
    ↓
Double logging (JSONL + .log lisible)
    ↓
Réponse JSON
```

**Credentials** : `.env` contient `MISTRAL_API_KEY` (obligatoire)

**Mémoire de conversation** : Historique stocké en mémoire par `session_id`, permet conversations contextuelles

---

## Structure Actuelle

```
YanaChat_V2/
├── app/
│   ├── main.py               # FastAPI app (endpoints: /api/chat, /health, /)
│   └── static/index.html     # UI web interactive
├── src/
│   ├── llm_pipeline.py       # Classe LLMPipeline (2 modes: chat + agents)
│   ├── chat_handler.py       # Classe ChatHandler (orch + double logging)
│   └── __init__.py
├── logs/
│   ├── interactions.jsonl    # Append-only audit log (machine-readable)
│   └── interactions.log      # Human-readable log (avec indentation)
├── tests/
│   ├── run_tests.py          # Tests d'intégration
│   ├── test_api_key.py       # Validation .env
│   └── test_queries.yaml     # Queries de test structurées
├── docs_markdown/            # Doc Mistral (référence locale)
├── .env                      # Secrets (git-ignored)
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Composants Clés IMPLÉMENTÉS

### 1. `src/llm_pipeline.py` — LLMPipeline

**Responsabilité** : Interface Mistral API avec **2 modes** (chat + agents) et retry robuste.

```python
class LLMPipeline:
    def __init__(self):
        self.chat_url = "https://api.mistral.ai/v1/chat/completions"
        self.agents_url = "https://api.mistral.ai/v1/agents"
        self.model = "mistral-small-2506"  # Modèle actuel
        self._websearch_agent_id = None   # Cache pour agent websearch
    
    def generate(self, user_query: str, use_web_search: bool = False) -> Dict:
        """Génère réponse via Mistral (chat OU agents avec websearch)."""
        system_prompt = """Tu es YanaChat, assistant expert sur la Guyane française.
        Domaines: tourisme, CSG Kourou, biodiversité amazonienne, culture créole."""
        
        if use_web_search:
            return self._call_agents_api(user_query)  # Agents API
        else:
            return self._call_mistral_with_retry(     # Chat API
                system_prompt=system_prompt, 
                user_prompt=user_query
            )
    
    def _get_or_create_websearch_agent(self) -> str:
        """Lazy creation + cache d'un agent Mistral avec web_search tool."""
        # Agent créé 1 fois, réutilisé pour toutes les requêtes websearch
```

**Patterns critiques** :
- **Timeout** : 60s pour chat, 90s pour agents (API plus lente)
- **Retry exponentiel** : 3 tentatives (backoff 2s, 4s, 8s)
- **Fallback** : `"Désolé, service indisponible."` jamais d'exception levée
- **Model switching** : Commentaires inline pour tester d'autres modèles

### 2. `src/chat_handler.py` — ChatHandler

**Responsabilité** : Orchestration (LLM + **double logging** + **mémoire de conversation**).

```python
class ChatHandler:
    def __init__(self):
        self.llm_pipeline = LLMPipeline()
        self.log_path = Path("logs/interactions.jsonl")
        self.log_path.parent.mkdir(exist_ok=True)
        
        # Stockage de l'historique par session_id
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def handle_query(self, user_query: str, session_id: str = None, use_web_search: bool = False) -> Dict:
        """1. Récupère historique 2. Génère via Mistral 3. Stocke échange 4. Log"""
        session_id = session_id or "anonymous"
        
        # Récupérer historique
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        # Générer réponse avec contexte
        result = self.llm_pipeline.generate(
            user_query, 
            conversation_history=self.conversation_history[session_id],
            use_web_search=use_web_search
        )
        
        # Stocker l'échange
        self.conversation_history[session_id].append({"role": "user", "content": user_query})
        self.conversation_history[session_id].append({"role": "assistant", "content": result["response"]})
        
        # Logging...
        return result
    
    def clear_session_history(self, session_id: str):
        """Efface l'historique d'une session."""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
```

**Mémoire de conversation** :
- **Stockage in-memory** : `Dict[session_id, List[messages]]`
- **Format messages** : `{"role": "user"/"assistant", "content": str}`
- **Gestion sessions** : Auto-créée à première requête, effaçable via API

### 3. `app/main.py` — FastAPI

**Endpoints** :
- `POST /api/chat` : `{"query": str, "session_id"?: str, "web_search"?: bool}` → `{"response": str}`
- `GET /health` : `{"status": "ok", "service": "YanaChat V2"}`
- `POST /api/clear_history` : `{"session_id": str}` → Efface l'historique d'une session
- `GET /api/history/{session_id}` : Récupère l'historique d'une session
- `GET /` : Serve `app/static/index.html` (UI interactive)

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="YanaChat V2")
handler = ChatHandler()

# Mount static UI (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve UI (avec fallback HTML si fichier manquant)."""
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Endpoint principal chat (supporte web_search optionnel)."""
    result = handler.handle_query(
        request.query, 
        request.session_id,
        use_web_search=request.web_search
    )
    return {"response": result["response"]}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "YanaChat V2"}
```

**Note** : `web_search=True` active Mistral Agents API avec tool web_search.

---

## Patterns Obligatoires

| Pattern | Détail |
|---------|--------|
| **Timeout Mistral** | Minimum **60 secondes**. API peut être lente. |
| **Retry exponentiel** | 3 tentatives max: backoff 2s, 4s, 8s. |
| **Fallback** | Toujours retourner une réponse, jamais exception. |
| **Logging JSONL** | 1 ligne JSON = 1 interaction. Append-only. |
| **Session tracking** | `session_id` optionnel pour regrouper requêtes utilisateur. |
| **Web search mode** | `use_web_search=True` → Mistral Agents API avec lazy agent cache |

---

## Developer Commands

```bash
# Setup local
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Lancer (dev)
uvicorn app.main:app --reload --port 8000
# UI: http://localhost:8000

# Docker
docker compose up --build

# Test API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Que faire à Cayenne?", "web_search": false}'

# Lire logs (dernier entry)
Get-Content logs/interactions.jsonl | ConvertFrom-Json -Stream | Select-Object -Last 1

# Lancer tests d'intégration
python tests/run_tests.py

# Vérifier .env
python tests/test_api_key.py
```

---

## Checklist Implementation

- [x] Structure `app/`, `src/`, `logs/`, `tests/`
- [x] `LLMPipeline` avec retry/timeout + 2 modes (chat/agents)
- [x] `ChatHandler` avec double logging (JSONL + readable)
- [x] Endpoints FastAPI (`/api/chat`, `/health`, `/`)
- [x] `app/static/index.html` (UI web)
- [x] `requirements.txt` : fastapi, uvicorn, requests, python-dotenv, pydantic
- [x] `docker-compose.yml` avec volumes logs/
- [x] Tests d'intégration (`run_tests.py`, `test_api_key.py`)
- [x] `.env` avec `MISTRAL_API_KEY`

---

## Points Critiques

1. **Ne pas reformuler** : Mistral génère, on ne post-process pas la réponse.
2. **Crash prevention** : Fallback `"Désolé, service indisponible."` en cas d'erreur.
3. **Timeouts généreux** : Mistral est slow, 60s c'est minimum.
4. **Audit via logging** : Chaque interaction doit être en JSONL pour debug/stats.
5. **Agent caching** : `_websearch_agent_id` est cached pour éviter création répétée (agents API est lent).
6. **Model selection** : `self.model` dans `LLMPipeline.__init__` (voir commentaires inline pour tester d'autres modèles).
7. **Error handling** : Toutes les API calls retournent fallback, jamais raise exception vers FastAPI.

## Points Critiques

1. **Ne pas reformuler** : Mistral génère, on ne post-process pas la réponse.
2. **Crash prevention** : Fallback `"Désolé, service indisponible."` en cas d'erreur.
3. **Timeouts généreux** : Mistral est slow, 60s c'est minimum.
4. **Audit via logging** : Chaque interaction doit être en JSONL pour debug/stats.

