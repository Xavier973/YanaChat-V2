# YanaChat V2 — Instructions pour Copilot

**Stack** : FastAPI + Mistral LLM + JSONL Logging  
**Langue** : Français (FR)  
**État** : Projet de blueprint - à implémenter

---

## Objectif

Construire un chatbot qui génère des réponses **détaillées et structurées** via l'API Mistral, avec logging systématique en JSONL pour audit.

---

## Architecture Minimale

```
Requête utilisateur
    ↓
FastAPI POST /api/chat
    ↓
LLMPipeline (Mistral API)
    ↓
ChatHandler (orchestration + logging)
    ↓
Réponse JSON + JSONL log
```

**Credenciales** : `.env` contient `MISTRAL_API_KEY` et `MISTRAL_API_URL`

---

## Structure à Implémenter

```
YanaChat_V2/
├── app/
│   ├── main.py               # FastAPI app + endpoints
│   └── static/index.html     # UI basique
├── src/
│   ├── llm_pipeline.py       # Classe LLMPipeline (API Mistral)
│   ├── chat_handler.py       # Classe ChatHandler (orch + logging)
│   └── __init__.py
├── logs/
│   └── interactions.jsonl    # Append-only audit log
├── tests/
│   └── run_tests.py          # Tests d'intégration
├── .env                      # Secrets (git-ignored)
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Composants Clés

### 1. `src/llm_pipeline.py` — LLMPipeline

**Responsabilité** : Interface Mistral API avec timeout robuste et retry.

```python
class LLMPipeline:
    def __init__(self):
        self.api_url = os.getenv("MISTRAL_API_URL")
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model = "mistral-large-latest"
    
    def generate(self, user_query: str) -> Dict:
        """Génère réponse via Mistral. Returns {'response': str, 'latency_ms': int}"""
        return self._call_mistral_with_retry(
            system_prompt="Tu es un assistant expert et utile.",
            user_prompt=user_query
        )
    
    def _call_mistral_with_retry(self, system_prompt: str, user_prompt: str):
        """Retry avec backoff exponentiel (2s, 4s, 8s). Timeout=60s."""
        for attempt in range(3):
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": [...], "temperature": 0.7},
                    timeout=60
                )
                return response.json()["choices"][0]["message"]["content"]
            except Timeout:
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return "Désolé, service indisponible."  # Fallback
```

### 2. `src/chat_handler.py` — ChatHandler

**Responsabilité** : Orchestration (LLM + logging JSONL).

```python
class ChatHandler:
    def __init__(self):
        self.llm_pipeline = LLMPipeline()
        self.log_path = Path("logs/interactions.jsonl")
        self.log_path.parent.mkdir(exist_ok=True)
    
    def handle_query(self, user_query: str, session_id: str = None) -> Dict:
        """1. Génère via Mistral 2. Log JSONL 3. Retour JSON"""
        result = self.llm_pipeline.generate(user_query)
        self._log_interaction(user_query, result, session_id or "anonymous")
        return result
    
    def _log_interaction(self, query: str, response: Dict, session_id: str):
        """Append JSON line à interactions.jsonl"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "model": self.llm_pipeline.model,  # mistral-large-latest
            "query": query,
            "response": response["response"][:500],  # Truncate long responses
            "latency_ms": response.get("latency_ms", 0)
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
```

### 3. `app/main.py` — FastAPI

**Endpoints** :
- `POST /api/chat` : `{"query": str, "session_id"?: str}` → `{"response": str}`
- `GET /health` : `{"status": "ok"}`

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="YanaChat V2")
handler = ChatHandler()

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    return {"response": handler.handle_query(request.query, request.session_id)}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## Patterns Obligatoires

| Pattern | Détail |
|---------|--------|
| **Timeout Mistral** | Minimum **60 secondes**. API peut être lente. |
| **Retry exponentiel** | 3 tentatives max: backoff 2s, 4s, 8s. |
| **Fallback** | Toujours retourner une réponse, jamais exception. |
| **Logging JSONL** | 1 ligne JSON = 1 interaction. Append-only. |
| **Session tracking** | `session_id` optionnel pour regrouper requêtes utilisateur. |

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

# Test simple
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Bonjour"}'

# Lire logs
Get-Content logs/interactions.jsonl | ConvertFrom-Json -Stream | Select-Object -Last 1
```

---

## Checklist Implementation

- [ ] Créer structure `app/`, `src/`, `logs/`, `tests/`
- [ ] Implémenter `LLMPipeline` avec retry/timeout
- [ ] Implémenter `ChatHandler` avec logging JSONL
- [ ] Endpoints FastAPI (`/api/chat`, `/health`)
- [ ] `app/static/index.html` (UI basique)
- [ ] `requirements.txt` : fastapi, requests, python-dotenv
- [ ] `docker-compose.yml`
- [ ] Tests d'intégration
- [ ] `.env.example` et `README.md`

---

## Points Critiques

1. **Ne pas reformuler** : Mistral génère, on ne post-process pas la réponse.
2. **Crash prevention** : Fallback `"Désolé, service indisponible."` en cas d'erreur.
3. **Timeouts généreux** : Mistral est slow, 60s c'est minimum.
4. **Audit via logging** : Chaque interaction doit être en JSONL pour debug/stats.

