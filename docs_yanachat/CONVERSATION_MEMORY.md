# Mémoire de Conversation - YanaChat V2

## Vue d'ensemble

YanaChat V2 maintient automatiquement l'historique de conversation pour chaque `session_id`, permettant des interactions contextuelles naturelles.

## Fonctionnement

### Stockage de l'historique

- **Stockage in-memory** : L'historique est conservé en RAM pendant la durée de vie du serveur
- **Format** : `{"role": "user"/"assistant", "content": str}`
- **Isolation** : Chaque `session_id` a son propre historique indépendant

### Flux de traitement

```
1. Requête arrive avec session_id
2. ChatHandler récupère l'historique pour cette session
3. LLMPipeline reçoit: system_prompt + historique + nouveau message
4. Mistral génère réponse avec contexte complet
5. Échange (user + assistant) ajouté à l'historique
6. Historique mis à jour pour prochaine requête
```

## Utilisation API

### Chat avec contexte

```bash
# Première requête (établit contexte)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Je m'\''appelle Julien et je vis en Guyane.",
    "session_id": "user_123"
  }'

# Deuxième requête (utilise contexte)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quel est mon prénom ?",
    "session_id": "user_123"
  }'
# Réponse attendue: "Votre prénom est Julien."
```

### Récupérer l'historique

```bash
curl http://localhost:8000/api/history/user_123

# Réponse:
{
  "session_id": "user_123",
  "history": [
    {"role": "user", "content": "Je m'appelle Julien..."},
    {"role": "assistant", "content": "Bonjour Julien..."},
    {"role": "user", "content": "Quel est mon prénom ?"},
    {"role": "assistant", "content": "Votre prénom est Julien."}
  ],
  "message_count": 4
}
```

### Effacer l'historique

```bash
curl -X POST http://localhost:8000/api/clear_history \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user_123"}'

# Réponse:
{
  "status": "ok",
  "message": "History cleared for session: user_123"
}
```

## Exemples de conversations contextuelles

### Exemple 1 : Planification de voyage

```
User: Je veux visiter la Guyane pendant 5 jours en juillet.
Bot: [propose itinéraire détaillé]

User: Quel est le meilleur jour pour visiter le CSG ?
Bot: D'après votre itinéraire de 5 jours en juillet, je recommande...
```

### Exemple 2 : Questions de suivi

```
User: Parle-moi du Centre Spatial Guyanais.
Bot: [informations détaillées sur le CSG]

User: Quelles sont les dates de lancement ?
Bot: Pour le Centre Spatial Guyanais dont je viens de parler...

User: Comment réserver une visite ?
Bot: Pour visiter le CSG, vous pouvez...
```

## Gestion des sessions

### Session ID

- **Génération** : Client génère un UUID unique (`session_${timestamp}_${random}`)
- **Persistance** : Tant que le serveur tourne (in-memory)
- **Anonyme** : Si `session_id` omis → stocké sous "anonymous"

### Bonnes pratiques

1. **Générer un session_id unique par utilisateur**
   ```javascript
   const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
   ```

2. **Effacer l'historique périodiquement** (éviter memory leak)
   ```javascript
   // Après déconnexion ou timeout
   fetch('/api/clear_history', {
     method: 'POST',
     body: JSON.stringify({session_id: sessionId})
   });
   ```

3. **Limiter la taille de l'historique** (optionnel, à implémenter si nécessaire)
   - Conserver seulement les N derniers échanges
   - Implémenter un système de fenêtre glissante

## Limitations actuelles

### Stockage in-memory

- ❌ **Perte de données** : Historique perdu au redémarrage du serveur
- ❌ **Scalabilité** : Ne fonctionne pas avec plusieurs instances (pas de partage)
- ✅ **Simplicité** : Pas de base de données nécessaire

### Pour production

Considérer migration vers:
- **Redis** : Cache distribué, TTL automatique
- **PostgreSQL** : Persistance durable, requêtes complexes
- **MongoDB** : Documents flexibles, historiques illimités

## Code interne

### ChatHandler

```python
self.conversation_history: Dict[str, List[Dict[str, str]]] = {}

# Structure:
{
  "user_123": [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour! Comment puis-je..."}
  ],
  "user_456": [...]
}
```

### LLMPipeline

```python
messages = [
    {"role": "system", "content": system_prompt},
    *conversation_history,  # Historique injecté ici
    {"role": "user", "content": user_prompt}
]
```

## Tests

```bash
# Tester la mémoire de conversation
python tests/test_conversation_memory.py

# Tests inclus:
# - Rétention du contexte
# - Isolation des sessions
# - Effacement de l'historique
```

## Logging

Chaque interaction log inclut maintenant:
```json
{
  "timestamp": "2026-01-23T19:00:00.000000",
  "session_id": "user_123",
  "model": "mistral-small-2506",
  "web_search": false,
  "query": "Quel est mon prénom ?",
  "response": "Votre prénom est Julien...",
  "latency_ms": 1234,
  "history_length": 4  // ← Nombre de messages dans l'historique
}
```

## FAQ

**Q: L'historique persiste-t-il après redémarrage du serveur ?**  
R: Non, stockage in-memory uniquement. Pour persistance, migrer vers Redis/DB.

**Q: Quelle est la taille maximale de l'historique ?**  
R: Illimitée actuellement. Implémenter une limite si nécessaire (ex: 50 messages).

**Q: Les sessions sont-elles partagées entre instances ?**  
R: Non, chaque instance a son propre stockage. Utiliser Redis pour partage.

**Q: Peut-on exporter l'historique d'une session ?**  
R: Oui, via `GET /api/history/{session_id}` (retourne JSON complet).

**Q: Le web_search utilise-t-il l'historique ?**  
R: Actuellement non pour Agents API. À implémenter si besoin.
