# Guide RAG (Retrieval-Augmented Generation)

## 🎯 Concept en une phrase
Le RAG **injecte des documents pertinents** dans le prompt avant d'interroger le LLM, pour que ses réponses soient basées sur **vos données** plutôt que sa connaissance générale.

---

## 📊 Architecture RAG Standard

```
┌─────────────────┐
│ Question User   │ "Quels sont les horaires de la mairie de Cayenne ?"
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  1. VECTORISATION de la question        │
│  Embedding → [0.234, -0.891, 0.445...]  │
└────────┬────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  2. RECHERCHE dans la base vectorielle   │
│  Trouve les 3-5 docs les plus similaires │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  3. RÉCUPÉRATION des docs pertinents     │
│  • doc_tourisme_cayenne.pdf (score: 0.92)│
│  • horaires_mairies.txt (score: 0.87)    │
│  • guide_guyane.md (score: 0.75)         │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  4. INJECTION dans le prompt             │
│  System: "Voici les documents..."        │
│  Context: [contenu des 3 docs]           │
│  User: "Quels sont les horaires..."      │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  5. LLM génère la réponse                │
│  Basée sur les docs fournis              │
└──────────────────────────────────────────┘
```

---

## 🔧 Étapes d'Implémentation (pour YanaChat)

### Phase 1 : Préparation des Documents (1-2h)

**1. Collecter des documents fiables sur la Guyane**
```
docs_guyane/
├── tourisme/
│   ├── cayenne_guide.md
│   ├── iles_salut.md
│   └── plages_guyane.txt
├── administration/
│   ├── horaires_mairies.md
│   └── demarches_prefecture.txt
├── culture/
│   ├── carnaval.md
│   └── cuisine_creole.md
└── nature/
    ├── parc_amazonien.md
    └── faune_guyane.txt
```

**2. Chunking (découper en morceaux)**
- **Pourquoi** : Les embeddings fonctionnent mieux sur ~200-500 mots
- **Comment** : Découper par paragraphe ou section
```python
# Exemple : doc de 5000 mots → 10 chunks de 500 mots
chunk_1 = "La ville de Cayenne est la capitale..."
chunk_2 = "Les horaires de la mairie sont: Lundi 8h-16h..."
```

### Phase 2 : Vectorisation (30 min setup)

**3. Générer des embeddings**
```python
from mistralai import Mistral

# Utiliser l'API Mistral Embeddings (GRATUIT jusqu'à 1M tokens/mois)
client = Mistral(api_key="votre_clé")

text = "La ville de Cayenne est la capitale..."
embedding = client.embeddings.create(
    model="mistral-embed",  # Modèle d'embedding Mistral
    inputs=[text]
)
# Retourne: [0.234, -0.891, 0.445, ...] (1024 dimensions)
```

**4. Stocker dans une base vectorielle**

**Option A : Simple (fichier local)** ✅ Recommandé pour MVP
```python
import json
import numpy as np

# Stocker dans un JSON
vector_db = {
    "chunks": [
        {
            "id": "doc1_chunk1",
            "text": "La ville de Cayenne...",
            "embedding": [0.234, -0.891, ...],
            "metadata": {"source": "cayenne_guide.md", "section": "intro"}
        },
        # ...
    ]
}

with open("vector_db.json", "w") as f:
    json.dump(vector_db, f)
```

**Option B : Professionnel (FAISS, ChromaDB, Qdrant)**
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("guyane_docs")

collection.add(
    documents=["La ville de Cayenne..."],
    embeddings=[[0.234, -0.891, ...]],
    ids=["doc1_chunk1"]
)
```

### Phase 3 : Recherche de Similarité (30 min)

**5. Comparer la question avec la base**
```python
def find_relevant_chunks(query: str, top_k: int = 3):
    # 1. Vectoriser la question
    query_embedding = client.embeddings.create(
        model="mistral-embed",
        inputs=[query]
    ).data[0].embedding
    
    # 2. Calculer similarité cosinus avec tous les chunks
    similarities = []
    for chunk in vector_db["chunks"]:
        score = cosine_similarity(query_embedding, chunk["embedding"])
        similarities.append((score, chunk))
    
    # 3. Retourner les top_k plus similaires
    similarities.sort(reverse=True, key=lambda x: x[0])
    return [chunk for score, chunk in similarities[:top_k]]
```

### Phase 4 : Intégration avec YanaChat (1h)

**6. Modifier `llm_pipeline.py`**
```python
class LLMPipeline:
    def __init__(self):
        # ... code existant ...
        self.rag_engine = RAGEngine()  # Nouveau
    
    def generate(self, user_query: str, use_web_search: bool = False, use_rag: bool = True):
        # Récupérer contexte pertinent
        if use_rag:
            relevant_docs = self.rag_engine.find_relevant_chunks(user_query, top_k=3)
            context = "\n\n".join([doc["text"] for doc in relevant_docs])
        else:
            context = ""
        
        # Modifier le system prompt
        system_prompt = f"""Tu es YanaChat, expert sur la Guyane française.

CONTEXTE FOURNI (sources fiables) :
{context}

Réponds UNIQUEMENT en te basant sur le CONTEXTE ci-dessus.
Si l'info n'est pas dans le contexte, dis "Je n'ai pas cette information dans mes sources"."""
        
        # ... appel Mistral comme avant ...
```

---

## 📦 Stack Technique Recommandée

### Option 1 : Simple (MVP rapide - 4h total) ✅
```
├── Embeddings : mistral-embed (API Mistral gratuite)
├── Stockage : JSON local (vector_db.json)
├── Recherche : NumPy cosine_similarity
├── Documents : 20-30 fichiers markdown
```

**Avantages** :
- ✅ Rapide à implémenter
- ✅ Pas de dépendance externe
- ✅ Gratuit (mistral-embed)
- ✅ Facile à débugger

**Inconvénients** :
- ❌ Recherche lente (>1000 docs)
- ❌ Pas de cache optimisé

### Option 2 : Professionnel (2-3 jours)
```
├── Embeddings : mistral-embed OU OpenAI text-embedding-3
├── Vector DB : ChromaDB (local) OU Qdrant Cloud
├── Orchestration : LangChain OU LlamaIndex
├── Documents : 100+ fichiers avec metadata
```

**Avantages** :
- ✅ Recherche ultra-rapide
- ✅ Scalable (millions de docs)
- ✅ Filtres avancés (metadata)
- ✅ Frameworks robustes

---

## 💰 Coûts Estimés

| Composant | Option Gratuite | Option Payante |
|-----------|----------------|----------------|
| **Embeddings** | Mistral Embed (1M tokens/mois gratuit) | OpenAI ($0.13/1M tokens) |
| **Vector DB** | JSON local / ChromaDB local | Qdrant Cloud ($25/mois) |
| **Docs** | Scraping manuel | Services API ($$$) |
| **TOTAL MVP** | **0€/mois** ✅ | ~$30-50/mois |

---

## 🎯 Pour YanaChat : Plan d'Action Concret

### Option Rapide (Recommandée pour MVP)

**Jour 1 (4h)** :
1. Créer `docs_guyane/` avec 20-30 fichiers MD sur :
   - Cayenne (mairies, tourisme, transports)
   - Îles du Salut
   - Kourou + CSG
   - Parc Amazonien
   - Culture créole
   
2. Script `scripts/build_rag.py` :
   ```python
   # Lit tous les .md
   # Génère embeddings avec mistral-embed
   # Sauvegarde dans vector_db.json
   ```

3. Classe `src/rag_engine.py` :
   ```python
   class RAGEngine:
       def find_relevant_chunks(query, top_k=3)
       def load_vector_db()
   ```

4. Modifier `src/llm_pipeline.py` pour injecter contexte

**Jour 2 (2h)** :
- Tests sur 30 questions types
- Ajustement du prompt
- Documentation

**Résultat** : Réponses fiables sur 80-90% des questions courantes Guyane ✅

---

## ⚖️ RAG vs Web Search (pour YanaChat)

| Critère | RAG | Web Search |
|---------|-----|------------|
| **Fiabilité** | ✅ 95% (vos docs) | ⚠️ 60% (sources aléatoires) |
| **Latence** | ✅ 0.2s | ❌ 3-5s |
| **Coût** | ✅ Gratuit (après setup) | ❌ Appels API |
| **Infos à jour** | ⚠️ Statique | ✅ Temps réel |
| **Meilleur pour** | Savoirs établis | Événements actuels |

**Solution hybride** ✨ :
```python
if "horaires" in query or "tarifs" in query:
    use_web_search = True  # Infos changeantes
else:
    use_rag = True  # Savoirs stables (géographie, histoire, etc.)
```

---

## ❓ FAQ

**Q : Combien de documents minimum ?**  
A : 20-30 docs bien rédigés > 500 docs de mauvaise qualité

**Q : Le RAG rend-il le web search obsolète ?**  
A : Non, ils sont complémentaires (RAG = base stable, websearch = actualités)

**Q : Ça ralentit les réponses ?**  
A : +0.2s avec recherche vectorielle locale (imperceptible)

**Q : Faut-il régénérer les embeddings à chaque requête ?**  
A : Non ! Embeddings des docs = 1 fois. Embedding de la question = à chaque fois.

---

## 🚀 Prochaines Étapes

Pour implémenter le RAG dans YanaChat :
1. Créer la structure `docs_guyane/` avec exemples
2. Script `build_rag.py` complet
3. Classe `RAGEngine` prête à l'emploi
4. Tests automatisés
