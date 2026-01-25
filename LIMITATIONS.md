# Limitations Connues - YanaChat V2

## 1. Rate Limiting API Mistral

### Problème
Lors de tests avec plusieurs requêtes consécutives, l'API Mistral retourne des erreurs **429 (Rate Limit Exceeded)**.

### Symptômes
```jsonl
{"response": "Erreur: Limite de requêtes atteinte.", "latency_ms": 7273}
```

### Cause
L'API Mistral impose des **limites de débit** :
- **Conversations API (web_search)** : Plus stricte, ~5-10 requêtes/minute
- **Chat Completions API** : Plus permissive, ~20-30 requêtes/minute

### Solutions Implémentées

✅ **Retry automatique avec backoff exponentiel**
- 1ère tentative : Attente 5 secondes
- 2ème tentative : Attente 10 secondes  
- 3ème tentative : Attente 20 secondes

✅ **Délai entre tests augmenté**
- Délai par défaut : `2 secondes` (au lieu de 1s)
- Recommandé pour web_search : `3-5 secondes`

### Utilisation Tests

```bash
# Délai standard (2s, risque de rate limit si beaucoup de requêtes)
python tests/test_yaml_queries.py

# Délai augmenté pour éviter rate limit (recommandé)
python tests/test_yaml_queries.py --delay 3.0

# Sans web_search (rate limit moins strict)
python tests/test_yaml_queries.py --no-web-search --delay 1.5
```

### Recommendations
- **Tests longs** : Utilisez `--delay 3` ou plus
- **Production** : Implémenter un queue system pour lisser le trafic
- **Plan API** : Passer à un plan payant pour des limites plus élevées

---

## 2. Sources Web Search Non Disponibles

### Problème
Les sources utilisées lors de la recherche web (`web_search=true`) **ne sont pas retournées** dans les logs.

### Cause Technique
L'API **Mistral Conversations** (utilisée pour le web_search) ne retourne **pas les URLs des sources** dans sa réponse. 

Structure de la réponse API :
```json
{
  "outputs": [
    {
      "type": "tool.execution",
      "name": "web_search",
      "arguments": {"query": "horaires mairie Cayenne"},
      "info": {}  // ❌ Vide - pas de résultats de recherche
    },
    {
      "type": "message.output",
      "content": "La réponse générée..."
    }
  ]
}
```

Le champ `info` dans `tool.execution` est **toujours vide**. Mistral utilise les résultats de recherche en interne pour générer la réponse, mais ne les expose pas via l'API.

### Impact
- Dans `logs/interactions.jsonl` : `"sources": []` même avec `"web_search": true`
- Impossible de tracker quelles URLs ont été consultées
- Pas de citations/références automatiques

### Solutions Possibles

#### Option 1 : Accepter la limitation (actuel)
✅ **Avantages** :
- Simple à implémenter
- API rapide et fiable
- Réponses de qualité avec informations à jour

❌ **Inconvénients** :
- Pas de traçabilité des sources
- Impossible de vérifier les infos

#### Option 2 : Migrer vers API Messages + Tool Calls Manuels
Utiliser `POST /v1/messages` avec `tools=[{"type": "web_search"}]` et gérer manuellement les tool calls.

✅ **Avantages** :
- Accès aux sources web
- Contrôle total sur le flux

❌ **Inconvénients** :
- Plus complexe à implémenter (boucle de tool calls)
- Latence accrue (plusieurs roundtrips API)
- Code plus fragile

#### Option 3 : Simuler les sources avec extraction
Parser la réponse pour extraire les URLs mentionnées dans le texte.

✅ **Avantages** :
- Pas de changement d'API
- Sources partielles disponibles

❌ **Inconvénients** :
- Incomplet (toutes les sources ne sont pas citées)
- Parsing fragile (regex sur texte naturel)

### Décision Actuelle
**Option 1** : On accepte la limitation. Le web_search améliore la qualité des réponses (infos à jour), même sans sources exposées.

### Workaround Utilisateur
Pour vérifier une information :
1. Relancer la même requête avec `web_search=false` pour voir la différence
2. Demander explicitement "Donne-moi les sources" dans la query
3. Vérifier manuellement sur les sites locaux (.gf, médias guyanais)

---

**Dernière mise à jour** : 25 janvier 2026  
**API Version** : Mistral Conversations v1
