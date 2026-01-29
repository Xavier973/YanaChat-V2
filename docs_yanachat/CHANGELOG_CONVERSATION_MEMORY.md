# Changements - Implémentation de la Mémoire de Conversation

## Date: 24 janvier 2026

### Objectif
Ajouter la capacité au chatbot de retenir le contexte des conversations précédentes au sein d'une même session.

---

## Fichiers Modifiés

### 1. `src/chat_handler.py`
**Changements:**
- ✅ Ajout de `self.conversation_history: Dict[str, List[Dict[str, str]]]` pour stocker l'historique par session
- ✅ Modification de `handle_query()` pour récupérer et stocker l'historique
- ✅ Ajout de `clear_session_history(session_id)` pour effacer l'historique d'une session
- ✅ Ajout de `get_session_history(session_id)` pour récupérer l'historique
- ✅ Passage de `conversation_history` à `LLMPipeline.generate()`
- ✅ Calcul de `history_length` en mémoire (non persisté dans le JSONL)

**Impact:**
- Chaque session maintient son propre historique indépendant
- L'historique est ajouté automatiquement à chaque requête

### 2. `src/llm_pipeline.py`
**Changements:**
- ✅ Modification de `generate()` pour accepter `conversation_history` en paramètre
- ✅ Modification de `_call_mistral_with_retry()` pour accepter `conversation_history`
- ✅ Construction du tableau `messages` incluant: system_prompt + historique + nouveau message
- ✅ Mise à jour du system_prompt avec instruction de "tenir compte du contexte précédent"
- ✅ Correction de l'appel récursif pour inclure `conversation_history`

**Impact:**
- Mistral API reçoit maintenant tout le contexte de la conversation
- Format: `[{role: "system", content: ...}, {role: "user", content: ...}, {role: "assistant", content: ...}, ...]`

### 3. `app/main.py`
**Changements:**
- ✅ Ajout de `ClearHistoryRequest` model Pydantic
- ✅ Ajout de l'endpoint `POST /api/clear_history` pour effacer l'historique
- ✅ Ajout de l'endpoint `GET /api/history/{session_id}` pour récupérer l'historique
- ✅ Documentation des nouveaux endpoints

**Impact:**
- API permet maintenant de gérer l'historique de conversation
- 3 nouveaux endpoints disponibles

### 4. `app/static/index.html`
**Changements:**
- ✅ Ajout du style `.header-actions` et `.clear-btn`
- ✅ Ajout du bouton "🔄 Nouvelle conversation" dans le header
- ✅ Implémentation de la fonction `clearConversation()` avec appel à l'API
- ✅ Confirmation utilisateur avant effacement
- ✅ Effacement de l'UI + message de confirmation

**Impact:**
- UI permet maintenant de démarrer une nouvelle conversation
- L'utilisateur peut effacer le contexte à tout moment

### 5. `.github/copilot-instructions.md`
**Changements:**
- ✅ Mise à jour de l'architecture avec flux de mémoire
- ✅ Documentation du stockage d'historique dans `ChatHandler`
- ✅ Ajout des nouveaux endpoints dans la section FastAPI
- ✅ Ajout de la section "Mémoire de conversation"
- ✅ Documentation du format des messages

**Impact:**
- Les développeurs et AI agents comprennent la nouvelle fonctionnalité

---

## Nouveaux Fichiers

### 6. `tests/test_conversation_memory.py` ✨ NOUVEAU
**Contenu:**
- Test de rétention du contexte (prénom, lieu)
- Test d'isolation des sessions (Alice vs Bob)
- Test d'effacement de l'historique
- Test de perte de contexte après effacement

**Utilisation:**
```bash
python tests/test_conversation_memory.py
```

### 7. `CONVERSATION_MEMORY.md` ✨ NOUVEAU
**Contenu:**
- Documentation complète de la fonctionnalité
- Exemples d'utilisation API
- Exemples de conversations contextuelles
- Bonnes pratiques (génération session_id, nettoyage)
- Limitations actuelles (in-memory, pas de persistance)
- Suggestions pour production (Redis, PostgreSQL, MongoDB)
- FAQ

---

## API Endpoints

### Nouveaux endpoints

#### 1. `POST /api/clear_history`
```bash
curl -X POST http://localhost:8000/api/clear_history \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user_123"}'
```
**Réponse:**
```json
{
  "status": "ok",
  "message": "History cleared for session: user_123"
}
```

#### 2. `GET /api/history/{session_id}`
```bash
curl http://localhost:8000/api/history/user_123
```
**Réponse:**
```json
{
  "session_id": "user_123",
  "history": [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour! Comment..."}
  ],
  "message_count": 2
}
```

### Endpoint modifié

#### `POST /api/chat` (INCHANGÉ côté API, comportement enrichi)
Le endpoint utilise maintenant automatiquement l'historique de conversation.

---

## Comportement

### Avant
```
User: Je m'appelle Julien.
Bot: Bonjour Julien! ...

User: Quel est mon prénom ?
Bot: Je ne sais pas, vous ne me l'avez pas dit.
```

### Après ✅
```
User: Je m'appelle Julien.
Bot: Bonjour Julien! ...

User: Quel est mon prénom ?
Bot: Votre prénom est Julien.
```

---

## Structure de données

### Stockage in-memory
```python
conversation_history = {
    "session_1769195236644_7z5ifocm5": [
        {"role": "user", "content": "Bonjour"},
        {"role": "assistant", "content": "Bonjour! Comment puis-je..."},
        {"role": "user", "content": "Parle-moi de la Guyane"},
        {"role": "assistant", "content": "La Guyane française..."}
    ],
    "session_1769195236645_8a9kl0xpm": [
        {"role": "user", "content": "Salut"},
        {"role": "assistant", "content": "Salut! ..."}
    ]
}
```

### Format des messages pour Mistral API
```python
[
    {"role": "system", "content": "Tu es YanaChat, assistant expert..."},
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour! Comment puis-je..."},
    {"role": "user", "content": "Quel est mon prénom ?"}  # ← Nouveau message
]
```

---

## Tests

### Commandes de test

```bash
# Test import
python -c "from src.chat_handler import ChatHandler; h = ChatHandler(); print('✓ OK')"

# Test complet de mémoire
python tests/test_conversation_memory.py

# Test API manuel
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Je m'\''appelle Julien", "session_id": "test_123"}'

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Quel est mon prénom ?", "session_id": "test_123"}'
```

---

## Logging

### Champs JSONL actuels
```json
{
  "timestamp": "2026-01-24T20:00:00.000000",
  "session_id": "user_123",
  "model": "mistral-small-2506",
  "web_search": false,
  "query": "Quel est mon prénom ?",
  "response": "Votre prénom est Julien.",
  "latency_ms": 1234,
  "sources": []
}
```

Note : `history_length` est disponible en mémoire pendant la requête, mais n'est pas encore écrit dans le JSONL.

---

## Limitations connues

### 1. Stockage in-memory
- ❌ Perte de données au redémarrage du serveur
- ❌ Pas de partage entre instances (scalabilité limitée)
- ❌ Risque de memory leak si sessions non nettoyées

### 2. Pas de limite de taille d'historique
- ⚠️ L'historique peut grandir indéfiniment
- ⚠️ Peut dépasser les limites de tokens Mistral (contexte window)

### 3. Web search + historique
- ⚠️ Agents API ne supporte peut-être pas l'historique de la même manière
- À tester et documenter

---

## Prochaines étapes (optionnel)

### Court terme
- [ ] Implémenter limite de taille d'historique (ex: 50 messages max)
- [ ] Implémenter fenêtre glissante (garder N derniers échanges)
- [ ] Tester web_search avec historique

### Moyen terme
- [ ] Migration vers Redis pour persistance
- [ ] Ajout de TTL (expiration automatique des sessions)
- [ ] Métriques: nombre de sessions actives, taille moyenne historique

### Long terme
- [ ] Base de données relationnelle pour historiques durables
- [ ] Export/import d'historique
- [ ] Recherche sémantique dans l'historique

---

## Résumé

### Lignes de code modifiées
- **chat_handler.py**: ~50 lignes ajoutées
- **llm_pipeline.py**: ~20 lignes modifiées
- **main.py**: ~40 lignes ajoutées
- **index.html**: ~40 lignes ajoutées
- **test_conversation_memory.py**: ~180 lignes (nouveau)
- **CONVERSATION_MEMORY.md**: ~300 lignes (nouveau)
- **copilot-instructions.md**: ~30 lignes modifiées

### Impact
✅ **Fonctionnalité majeure ajoutée**: Mémoire de conversation  
✅ **Zéro breaking changes**: Compatible avec clients existants  
✅ **Testable**: Suite de tests dédiée  
✅ **Documenté**: README complet + instructions Copilot  
✅ **UI améliorée**: Bouton "Nouvelle conversation"  

### Temps estimé
- Implémentation: ~2h
- Tests: ~30min
- Documentation: ~1h
- **Total**: ~3h30
