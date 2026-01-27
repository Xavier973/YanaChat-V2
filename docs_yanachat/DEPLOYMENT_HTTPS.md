# 🚀 Déploiement YanaChat V2 avec HTTPS (Traefik + Let's Encrypt)

**Dernière mise à jour** : 26 janvier 2026  
**Stack** : FastAPI + Traefik + Let's Encrypt  

---

## 📋 Table des Matières

1. [Architecture](#architecture)
2. [Configuration Local (Dev)](#configuration-local-dev)
3. [Configuration Production (VPS)](#configuration-production-vps)
4. [Prérequis VPS](#prérequis-vps)
5. [Déploiement Étape par Étape](#déploiement-étape-par-étape)
6. [Troubleshooting](#troubleshooting)
7. [Sécurité](#sécurité)

---

## Architecture

### Local (HTTP)
```
Navigateur → http://localhost:8000 → FastAPI
```

### Production (HTTPS)
```
Internet → Port 443 (HTTPS) → Traefik → FastAPI (port 8000)
                ↓
         Let's Encrypt (certificats auto-renouvelés)
```

**Avantages Traefik** :
- ✅ Gestion automatique des certificats SSL/TLS (Let's Encrypt)
- ✅ Renouvellement automatique (tous les 90 jours)
- ✅ Redirection HTTP → HTTPS automatique
- ✅ Rate limiting intégré
- ✅ Dashboard de monitoring (optionnel)

---

## Configuration Local (Dev)

### Commandes

```bash
# Lancer en mode développement (HTTP simple)
docker compose -f docker-compose.dev.yml up --build

# Ou avec le fichier par défaut
docker compose up --build
```

**URL** : `http://localhost:8000`

**Features** :
- Hot-reload automatique (code modifié → serveur redémarre)
- Logs en temps réel
- Pas de HTTPS (inutile en local)

---

## Configuration Production (VPS)

### Commandes

```bash
# Lancer en mode production (HTTPS avec Traefik)
docker compose -f docker-compose.prod.yml up -d --build

# Vérifier les logs
docker compose -f docker-compose.prod.yml logs -f

# Arrêter
docker compose -f docker-compose.prod.yml down
```

**URLs** :
- Application : `https://votredomaine.com`
- Dashboard Traefik : `https://traefik.votredomaine.com:8080` (optionnel)

---

## Prérequis VPS

### 1. Infrastructure

- **VPS** avec Docker et Docker Compose installés
- **Nom de domaine** pointant vers l'IP publique du VPS
- **Ports ouverts** : 80, 443 (et 8080 pour dashboard Traefik si activé)

### 2. Configuration DNS

Créer les enregistrements DNS suivants :

```
Type    Nom        Valeur              TTL
A       @          IP_DU_VPS           3600
A       www        IP_DU_VPS           3600
A       traefik    IP_DU_VPS           3600  (optionnel pour dashboard)
```

**Tester la propagation DNS** :
```bash
nslookup votredomaine.com
```

### 3. Firewall VPS

**⚠️ IMPORTANT : Autoriser SSH (port 22) AVANT tout pour éviter de vous bloquer !**

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp    # ⚠️ SSH - OBLIGATOIRE pour ne pas perdre l'accès !
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8080/tcp  # Dashboard Traefik (optionnel, sécuriser)
sudo ufw enable

# iptables (alternative)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT   # SSH
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT   # HTTP
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
```

---

## Déploiement Étape par Étape

### Étape 1 : Préparer le VPS

```bash
# Se connecter au VPS
ssh user@IP_DU_VPS

# Installer Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installer Docker Compose
sudo apt update
sudo apt install docker-compose-plugin

# Vérifier installation
docker --version
docker compose version
```

### Étape 2 : Cloner le Projet

```bash
cd /opt  # ou /home/user/apps
git clone https://github.com/Xavier973/YanaChat-V2.git
cd YanaChat-V2
git checkout main  # ou dev02
```

### Étape 3 : Configurer .env

```bash
# Copier le fichier exemple
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

**Exemple de configuration** :

```env
# Mistral API
MISTRAL_API_KEY=votre clé ici
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions

# Domaines
DOMAIN=yanachat.votredomaine.com
TRAEFIK_DOMAIN=traefik.votredomaine.com

# Let's Encrypt
ACME_EMAIL=votre.email@votredomaine.com

# BasicAuth pour dashboard Traefik (optionnel)
# TRAEFIK_AUTH=admin:$$apr1$$xyz...
```

### Étape 4 : Créer les Répertoires

```bash
# Certificats Let's Encrypt
mkdir -p letsencrypt
chmod 600 letsencrypt

# Logs Traefik
mkdir -p traefik-logs

# Logs application
mkdir -p logs
```

### Étape 5 : **IMPORTANT** - Test avec Let's Encrypt Staging

**⚠️ TOUJOURS tester avec staging d'abord pour éviter les rate limits !**

```bash
# Éditer docker-compose.prod.yml
nano docker-compose.prod.yml

# Décommenter la ligne staging dans la section traefik:
# - "--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
```

### Étape 6 : Premier Lancement (Staging)

```bash
# Lancer avec staging
docker compose -f docker-compose.prod.yml up -d

# Vérifier les logs
docker compose -f docker-compose.prod.yml logs -f traefik

# Chercher dans les logs :
# - "certificatesResolvers.letsencrypt.acme.caserver=https://acme-staging-v02..."
# - "Certificates obtained for [votredomaine.com]"
```

**Tester l'URL** : `https://votredomaine.com`  
👉 Le navigateur affichera un avertissement (certificat staging), c'est **NORMAL**.

### Étape 7 : Passer en Production

```bash
# Arrêter les conteneurs
docker compose -f docker-compose.prod.yml down

# Supprimer les certificats staging
rm -rf letsencrypt/acme.json

# Éditer docker-compose.prod.yml
nano docker-compose.prod.yml

# RE-commenter la ligne staging (ou la supprimer)
# - "--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"

# Relancer avec production
docker compose -f docker-compose.prod.yml up -d --build

# Vérifier les certificats
docker compose -f docker-compose.prod.yml logs traefik | grep "Certificates obtained"
```

**Tester l'URL** : `https://votredomaine.com`  
🎉 Le navigateur doit afficher un cadenas vert !

### Étape 8 : Sécuriser le Dashboard Traefik (Optionnel)

```bash
# Générer un hash BasicAuth
sudo apt install apache2-utils
echo $(htpasswd -nb admin VotreMotDePasse) | sed -e s/\\$/\\$\\$/g

# Copier le résultat (ex: admin:$$apr1$$xyz...)

# Ajouter dans .env
echo "TRAEFIK_AUTH=admin:$$apr1$$xyz..." >> .env

# Décommenter les lignes dans docker-compose.prod.yml:
# - "traefik.http.routers.dashboard.middlewares=auth"
# - "traefik.http.middlewares.auth.basicauth.users=${TRAEFIK_AUTH}"

# Relancer
docker compose -f docker-compose.prod.yml up -d
```

**Dashboard** : `https://traefik.votredomaine.com:8080`  
Login : `admin` / `VotreMotDePasse`

---

## Troubleshooting

### Erreur : "Cannot obtain certificate"

**Symptômes** : Logs Traefik affichent "Unable to obtain ACME certificate"

**Causes possibles** :
1. **DNS mal configuré** → Tester avec `nslookup votredomaine.com`
2. **Firewall bloque port 80/443** → `sudo ufw status`
3. **Rate limit Let's Encrypt** → Utiliser staging d'abord
4. **Email invalide** → Vérifier `ACME_EMAIL` dans `.env`

**Solution** :
```bash
# Vérifier DNS
dig votredomaine.com +short  # Doit retourner IP_DU_VPS

# Tester port 80 ouvert
curl -I http://votredomaine.com

# Vérifier logs détaillés
docker compose -f docker-compose.prod.yml logs traefik | grep -i error
```

### Erreur : "too many certificates already issued"

**Cause** : Dépassement du rate limit Let's Encrypt (5 certificats/semaine/domaine).

**Solution** :
1. Attendre 7 jours
2. Ou utiliser un sous-domaine différent (`app2.votredomaine.com`)
3. **Toujours tester avec staging d'abord !**

### Application inaccessible (502 Bad Gateway)

**Symptômes** : Traefik répond mais renvoie 502.

**Causes** :
1. **Conteneur API crash** → `docker ps` (vérifier si `yanachat_api` tourne)
2. **Réseau Docker mal configuré** → `docker network ls`

**Solution** :
```bash
# Vérifier logs API
docker compose -f docker-compose.prod.yml logs api

# Redémarrer API
docker compose -f docker-compose.prod.yml restart api
```

### Certificat pas renouvelé automatiquement

**Let's Encrypt** renouvelle automatiquement 30 jours avant expiration.

**Vérifier renouvellement** :
```bash
# Checker expiration certificat
echo | openssl s_client -servername votredomaine.com -connect votredomaine.com:443 2>/dev/null | openssl x509 -noout -dates

# Forcer renouvellement (si < 30 jours)
docker compose -f docker-compose.prod.yml restart traefik
```

---

## Sécurité

### 1. Rate Limiting

**Déjà configuré** dans `docker-compose.prod.yml` :
- 100 requêtes/seconde
- Burst : 50 requêtes

**Modifier** :
```yaml
# Dans labels du service api:
- "traefik.http.middlewares.rate-limit.ratelimit.average=50"  # 50 req/s
- "traefik.http.middlewares.rate-limit.ratelimit.burst=20"
```

### 2. Sécuriser le Dashboard Traefik

**Option 1** : Désactiver complètement
```yaml
# Dans docker-compose.prod.yml, supprimer le port:
# - "8080:8080"
```

**Option 2** : BasicAuth (voir Étape 8)

**Option 3** : IP Whitelist
```yaml
# Autoriser uniquement votre IP
- "traefik.http.middlewares.whitelist.ipwhitelist.sourcerange=VOTRE_IP/32"
- "traefik.http.routers.dashboard.middlewares=whitelist"
```

### 3. HTTPS Only (HSTS)

**Déjà activé** via security-headers :
```yaml
- "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
```

Le navigateur forcera HTTPS pendant 1 an.

### 4. Firewall Applicatif (WAF)

**Optionnel** : Ajouter Cloudflare en amont de Traefik pour :
- Protection DDoS
- WAF (Web Application Firewall)
- Cache CDN

---

## Maintenance

### Renouvellement Automatique

**Let's Encrypt** : Automatique (tous les 60 jours, certificats valides 90 jours).

**Pas d'action requise** si Traefik tourne en continu.

### Backup

```bash
# Sauvegarder certificats
tar -czf letsencrypt-backup-$(date +%Y%m%d).tar.gz letsencrypt/

# Sauvegarder logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### Mise à Jour Docker Images

```bash
# Pull nouvelles images
docker compose -f docker-compose.prod.yml pull

# Rebuild + redémarrage
docker compose -f docker-compose.prod.yml up -d --build

# Nettoyer anciennes images
docker image prune -a
```

---

## Checklist Déploiement

- [ ] VPS avec Docker installé
- [ ] DNS configuré (A record → IP VPS)
- [ ] Firewall ouvert (80, 443)
- [ ] `.env` configuré avec domaine + email
- [ ] Test avec Let's Encrypt **staging**
- [ ] Vérification certificat staging obtenu
- [ ] Passage en production
- [ ] Test HTTPS fonctionnel (cadenas vert)
- [ ] Dashboard Traefik sécurisé (BasicAuth ou désactivé)
- [ ] Monitoring configuré (logs, uptime)

---

## Commandes Utiles

```bash
# Status des conteneurs
docker compose -f docker-compose.prod.yml ps

# Logs temps réel
docker compose -f docker-compose.prod.yml logs -f

# Redémarrer un service
docker compose -f docker-compose.prod.yml restart api

# Reconstruire sans cache
docker compose -f docker-compose.prod.yml build --no-cache

# Vérifier certificats SSL
openssl s_client -connect votredomaine.com:443 -servername votredomaine.com

# Tester redirection HTTP → HTTPS
curl -I http://votredomaine.com
```

---

## Ressources

- [Documentation Traefik](https://doc.traefik.io/traefik/)
- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)
- [Staging Environment](https://letsencrypt.org/docs/staging-environment/)
- [ACME Protocol](https://datatracker.ietf.org/doc/html/rfc8555)

---

**Support** : En cas de problème, vérifier les logs Traefik en premier :
```bash
docker compose -f docker-compose.prod.yml logs traefik | grep -i error
```
