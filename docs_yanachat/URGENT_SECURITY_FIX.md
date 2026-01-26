# 🚨 URGENT - Procédure Suppression Clé API Exposée

**Date** : 26 janvier 2026  
**Problème** : Clé API Mistral exposée dans commit sur branche `dev03`  
**Statut repo** : ✅ Privé (première protection effectuée)

---

## ⚡ ACTIONS IMMÉDIATES (Dans l'ordre)

### 1. RÉVOQUER LA CLÉ API MISTRAL (PRIORITÉ ABSOLUE)

```bash
# Aller sur https://console.mistral.ai/api-keys/
# 1. Se connecter à votre compte Mistral
# 2. Aller dans "API Keys"
# 3. Trouver la clé exposée : XBc7LdqT8mVB7DPeieV7KP4ZE3Geoz2R
# 4. Cliquer sur "Delete" ou "Revoke"
# 5. Générer une NOUVELLE clé
# 6. Copier la nouvelle clé (elle ne sera affichée qu'une fois)
```

**⚠️ FAIRE MAINTENANT avant de continuer !**

---

### 2. METTRE À JOUR .env LOCAL

```bash
# Ouvrir .env
nano .env

# Remplacer l'ancienne clé par la nouvelle
MISTRAL_API_KEY=VOTRE_NOUVELLE_CLE_ICI
```

---

### 3. SUPPRIMER LE COMMIT LOCALEMENT ET SUR GITHUB

#### Option A : Supprimer le dernier commit (si c'est le dernier)

```powershell
# Vérifier l'historique
git log --oneline -5

# Si le commit avec la clé est le dernier :
git reset --hard HEAD~1

# Forcer le push sur GitHub (ATTENTION : destructif)
git push origin dev03 --force
```

#### Option B : Supprimer un commit spécifique (rebase interactif)

```powershell
# Trouver le commit avec la clé
git log --oneline --all | Select-String "DEPLOYMENT_HTTPS"

# Exemple de sortie :
# abc123d Add HTTPS deployment guide

# Lancer rebase interactif (remplacer N par nombre de commits à voir)
git rebase -i HEAD~5

# Un éditeur s'ouvre avec la liste des commits :
# pick abc123d Add HTTPS deployment guide
# pick def456e Other commit
#
# Remplacer "pick" par "drop" pour le commit à supprimer :
# drop abc123d Add HTTPS deployment guide
# pick def456e Other commit
#
# Sauvegarder et quitter l'éditeur

# Forcer le push
git push origin dev03 --force
```

#### Option C : Réécrire l'historique avec filter-branch (AVANCÉ)

```powershell
# Supprimer le fichier de TOUT l'historique
git filter-branch --force --index-filter `
  "git rm --cached --ignore-unmatch docs_yanachat/DEPLOYMENT_HTTPS.md" `
  --prune-empty --tag-name-filter cat -- --all

# Forcer le push de toutes les branches
git push origin --force --all
```

---

### 4. VÉRIFIER LA SUPPRESSION SUR GITHUB

```bash
# Aller sur https://github.com/Xavier973/YanaChat-V2
# Naviguer dans "Commits" de la branche dev03
# Vérifier que le commit n'apparaît plus
```

⚠️ **IMPORTANT** : GitHub peut garder le commit accessible via son hash pendant quelques heures/jours dans le cache. C'est pour ça qu'il FAUT révoquer la clé immédiatement.

---

### 5. NETTOYER LE DÉPÔT LOCAL

```powershell
# Supprimer les références orphelines
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

### 6. CRÉER UN NOUVEAU COMMIT PROPRE

```powershell
# Vérifier que DEPLOYMENT_HTTPS.md a bien la clé exemple
git diff docs_yanachat/DEPLOYMENT_HTTPS.md

# Ajouter le fichier corrigé
git add docs_yanachat/DEPLOYMENT_HTTPS.md

# Commit avec message explicite
git commit -m "fix: Remove exposed API key from deployment guide"

# Push normal
git push origin dev03
```

---

## 🔒 PRÉVENTION FUTURE

### 1. Ajouter git-secrets (recommandé)

```powershell
# Installer git-secrets
# Via Chocolatey (Windows)
choco install git-secrets

# Configurer pour bloquer les patterns de clés
git secrets --install
git secrets --register-aws
git secrets --add 'MISTRAL_API_KEY=[A-Za-z0-9]{32,}'
```

### 2. Utiliser un pre-commit hook

Créer `.git/hooks/pre-commit` :

```bash
#!/bin/sh
# Bloquer commit si clé API détectée

if git diff --cached | grep -E 'MISTRAL_API_KEY=[A-Za-z0-9]{20,}'; then
    echo "❌ ERREUR: Clé API détectée dans le commit !"
    echo "Remplacer par une valeur exemple avant de commiter."
    exit 1
fi
```

```powershell
# Rendre exécutable (Git Bash)
chmod +x .git/hooks/pre-commit
```

### 3. Vérifier .gitignore

```bash
# S'assurer que .env est bien ignoré
cat .gitignore | Select-String ".env"

# Si absent, ajouter :
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: Ensure .env is gitignored"
```

---

## ✅ CHECKLIST DE SÉCURITÉ

- [ ] Clé API Mistral révoquée sur console.mistral.ai
- [ ] Nouvelle clé API générée
- [ ] `.env` local mis à jour avec nouvelle clé
- [ ] Commit supprimé localement (`git reset` ou `git rebase`)
- [ ] Commit supprimé sur GitHub (`git push --force`)
- [ ] Historique nettoyé (`git gc --prune=now`)
- [ ] Nouveau commit propre créé
- [ ] Vérification GitHub : commit n'apparaît plus
- [ ] git-secrets installé (optionnel mais recommandé)
- [ ] pre-commit hook configuré (optionnel)

---

## 📊 Timeline Recommandée

**Immédiat (maintenant)** :
1. Révoquer clé API (5 min)
2. Générer nouvelle clé (1 min)

**Sous 30 minutes** :
3. Mettre à jour .env local (1 min)
4. Supprimer commit local + force push (5 min)
5. Vérifier suppression GitHub (2 min)

**Sous 1 heure** :
6. Installer git-secrets (10 min)
7. Configurer pre-commit hook (5 min)

---

## 🆘 EN CAS DE PROBLÈME

**Si force push bloqué** :
```powershell
# Vérifier protections de branche
# Sur GitHub : Settings > Branches > Branch protection rules
# Désactiver temporairement "Require linear history" si activé
```

**Si commit toujours visible sur GitHub après 1h** :
- Contacter GitHub Support pour purge du cache
- Ou créer une nouvelle branche propre :
  ```powershell
  git checkout -b dev04
  git push origin dev04
  # Supprimer dev03 sur GitHub via interface web
  ```

**Si nouvelle clé API ne fonctionne pas** :
```bash
# Tester avec curl
curl https://api.mistral.ai/v1/models -H "Authorization: Bearer VOTRE_NOUVELLE_CLE"
```

---

## 📝 Leçon Apprise

**Ne JAMAIS** :
- Copier-coller de vraies valeurs dans des fichiers de documentation
- Commiter des fichiers `.env`
- Partager des clés API, même en repo privé

**TOUJOURS** :
- Utiliser des valeurs exemple (`votre_cle_api_ici`, `example.com`)
- Vérifier `git diff` avant chaque commit
- Configurer git-secrets sur tous les projets sensibles

---

**Contact Mistral Support** : https://console.mistral.ai/support  
**Documentation GitHub - Remove sensitive data** : https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
