# Configuration SMTP pour le Signalement de Conversations

## Vue d'ensemble

YanaChat V2 permet aux utilisateurs de signaler des conversations problématiques via email. Cette fonctionnalité nécessite une configuration SMTP.

## Configuration avec Gmail (Recommandé)

### 1. Créer un App Password Gmail

1. Aller sur [Google Account - App Passwords](https://myaccount.google.com/apppasswords)
2. Se connecter avec votre compte Gmail
3. Sélectionner "Mail" et "Autre (nom personnalisé)"
4. Entrer "YanaChat" comme nom
5. Copier le mot de passe généré (16 caractères)

### 2. Configurer le `.env`

Décommenter et remplir les variables suivantes dans `.env` :

```env
# ------------------------------------------------------------------------------
# EMAIL SMTP - Signalement de conversations problématiques
# ------------------------------------------------------------------------------
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App Password Gmail
REPORT_EMAIL=x.cuniberti@gmail.com  # Email destinataire des signalements
```

### 3. Tester la configuration

Lancer le serveur et cliquer sur "⚠️ Signaler" dans l'interface.

Si vous recevez l'erreur "SMTP not configured", vérifiez que :
- Les variables `SMTP_USER` et `SMTP_PASSWORD` sont définies dans `.env`
- Le fichier `.env` est bien chargé par l'application
- L'App Password Gmail est correct (16 caractères sans espaces)

## Alternatives à Gmail

### Outlook / Office 365

```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=votre.email@outlook.com
SMTP_PASSWORD=votre_mot_de_passe
```

### SendGrid (Service professionnel)

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=votre_api_key_sendgrid
```

### Mailgun

```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@votre-domaine.mailgun.org
SMTP_PASSWORD=votre_password_mailgun
```

## Format de l'email envoyé

```
Objet: [YanaChat] Signalement - Session abc12345

=== SIGNALEMENT YANACHAT ===

Session ID: session_1234567890_abc123

MESSAGE UTILISATEUR:
La réponse était incorrecte et contenait des informations fausses.

=============================
CONVERSATION COMPLÈTE:
=============================

**USER**: Quelle est la capitale de la Guyane ?

**ASSISTANT**: Paris est la capitale de la Guyane.

=============================
Envoyé automatiquement depuis YanaChat V2
```

## Sécurité

⚠️ **Important** :
- Ne jamais commit le fichier `.env` avec les vraies valeurs
- Utiliser des App Passwords, jamais le mot de passe principal
- Vérifier que `.env` est dans `.gitignore`

## Désactiver temporairement le SMTP

Si vous ne voulez pas configurer SMTP immédiatement :

1. Laisser les variables SMTP commentées dans `.env`
2. L'utilisateur recevra un message : "Service de signalement non configuré. Veuillez contacter directement : x.cuniberti@gmail.com"
3. Le système continuera de fonctionner normalement

## Troubleshooting

### Erreur "SMTP not configured"
→ Variables `SMTP_USER` ou `SMTP_PASSWORD` non définies dans `.env`

### Erreur "Authentication failed"
→ App Password Gmail incorrect ou compte non autorisé

### Erreur "Connection timeout"
→ Port 587 bloqué par le pare-feu ou mauvais `SMTP_HOST`

### Email non reçu
→ Vérifier spam/courrier indésirable
→ Vérifier que `REPORT_EMAIL` est correct
