# Fonctionnalité de Signalement de Conversations

## Vue d'ensemble

Cette fonctionnalité permet aux utilisateurs de YanaChat de signaler des conversations problématiques directement depuis l'interface web. Les signalements sont envoyés par email au développeur.

## Architecture

```
Frontend (UI)                Backend (FastAPI)              Email
─────────────────           ──────────────────             ───────
                                                            
┌─────────────────┐         ┌──────────────────┐          ┌─────────┐
│ Bouton "⚠️      │         │  POST /api/report│          │ SMTP    │
│ Signaler"       │────────▶│                  │─────────▶│ Gmail   │
│                 │         │  - session_id    │          │         │
│ Modal avec:     │         │  - user_message  │          │ Envoie  │
│ - Textarea      │         │  - conversation[]│          │ vers    │
│ - Bouton Envoyer│         │                  │          │ REPORT_ │
└─────────────────┘         └──────────────────┘          │ EMAIL   │
                                                           └─────────┘
```

## Composants Implémentés

### 1. Backend - FastAPI (`app/main.py`)

#### Endpoint `/api/report`

**Request:**
```json
{
  "session_id": "session_1234567890_abc123",
  "user_message": "La réponse était incorrecte",
  "conversation": [
    {"role": "user", "content": "Question..."},
    {"role": "assistant", "content": "Réponse..."}
  ]
}
```

**Response (succès):**
```json
{
  "status": "ok",
  "message": "Report sent successfully"
}
```

**Response (SMTP non configuré):**
```json
{
  "status": "error",
  "message": "SMTP not configured. Please set SMTP_USER and SMTP_PASSWORD in .env"
}
```

### 2. Frontend - UI (`app/static/index.html`)

#### Bouton dans le Header
- Positionné à côté de "🔄 Nouvelle conversation"
- Style rouge pour indiquer une action importante
- Icône ⚠️ pour la visibilité

#### Modal de Signalement
- Titre explicatif
- Textarea pour description du problème
- Boutons "Annuler" et "Envoyer"
- Validation du contenu avant envoi

#### Tracking de la Conversation
- Fonction `trackMessage()` enregistre chaque message
- Variable `conversationHistory[]` stocke l'historique complet
- Reset lors de "Nouvelle conversation"

### 3. Configuration - Variables d'Environnement

Variables requises dans `.env` :

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=votre_app_password_gmail
REPORT_EMAIL=x.cuniberti@gmail.com
```

## Flux Utilisateur

1. **Utilisateur converse** avec YanaChat
2. **Détecte un problème** (réponse incorrecte, inappropriée, etc.)
3. **Clique sur "⚠️ Signaler"**
4. **Modal s'ouvre** avec textarea
5. **Décrit le problème** dans le champ texte
6. **Clique "Envoyer"**
7. **Email envoyé** au développeur via SMTP
8. **Confirmation** affichée à l'utilisateur

## Format de l'Email Reçu

```
Objet: [YanaChat] Signalement - Session abc12345

=== SIGNALEMENT YANACHAT ===

Session ID: session_1234567890_abc123

MESSAGE UTILISATEUR:
La réponse sur la capitale était complètement fausse.

=============================
CONVERSATION COMPLÈTE:
=============================

**USER**: Quelle est la capitale de la Guyane française ?

**ASSISTANT**: Paris est la capitale de la Guyane.

**USER**: Tu es sûr ?

**ASSISTANT**: Oui, c'est Paris.

=============================
Envoyé automatiquement depuis YanaChat V2
```

## Avantages de cette Implémentation

✅ **Simple** : Pas de base de données nécessaire  
✅ **Fiable** : Email SMTP standard (Gmail, Outlook, etc.)  
✅ **Traçable** : Emails conservés dans boîte mail  
✅ **Non-bloquant** : Fonctionne même si SMTP non configuré (fallback)  
✅ **Privacy-first** : Utilisateur conscient de ce qui est envoyé  
✅ **Contexte complet** : Toute la conversation incluse dans le signalement

## Gestion des Erreurs

### 1. SMTP non configuré
- Message : "Service de signalement non configuré. Veuillez contacter directement : x.cuniberti@gmail.com"
- L'application continue de fonctionner normalement

### 2. Aucune conversation
- Alert : "Aucune conversation à signaler. Commencez par poser une question."
- Modal ne s'ouvre pas

### 3. Description vide
- Alert : "Veuillez décrire le problème avant d'envoyer."
- Email non envoyé

### 4. Erreur SMTP (auth, network, etc.)
- Alert : "❌ Erreur lors de l'envoi : [détails]"
- Utilisateur informé du problème

## Évolutions Possibles

### Court terme
- [ ] Capturer automatiquement le contexte technique (user-agent, timestamp)
- [ ] Ajouter un champ "Type de problème" (dropdown)
- [ ] Limiter la taille de la conversation envoyée (ex: derniers 10 messages)

### Moyen terme
- [ ] Stocker les signalements dans une base de données (PostgreSQL)
- [ ] Dashboard admin pour visualiser les signalements
- [ ] Catégorisation automatique via LLM

### Long terme
- [ ] Système de tickets avec suivi
- [ ] Feedback loop : notifier l'utilisateur quand le problème est résolu
- [ ] Analytics : identifier patterns de problèmes récurrents

## Sécurité

⚠️ **Points d'attention** :
- **App Password Gmail** : Ne jamais utiliser le mot de passe principal
- **Rate limiting** : À implémenter si abus détectés
- **Validation** : Sanitize user input avant envoi email
- **HTTPS** : Obligatoire en production pour protéger les données

## Tests

### Test manuel
1. Démarrer YanaChat : `uvicorn app.main:app --reload`
2. Ouvrir http://localhost:8000
3. Poser 2-3 questions
4. Cliquer "⚠️ Signaler"
5. Remplir le formulaire
6. Vérifier réception email

### Test sans SMTP configuré
1. Commenter les variables SMTP dans `.env`
2. Redémarrer l'app
3. Tenter un signalement
4. Vérifier message d'erreur graceful

## Documentation Associée

- [SMTP_CONFIGURATION.md](./SMTP_CONFIGURATION.md) : Guide de configuration SMTP détaillé
- [.env.example](../.env.example) : Template de configuration

## Auteur

Fonctionnalité développée pour YanaChat V2  
Contact : x.cuniberti@gmail.com
