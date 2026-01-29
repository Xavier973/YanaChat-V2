**Déploiement 24/7 sur VPS Infomaniak (Docker Compose)**

**Prérequis**
- VPS Infomaniak (Accès SSH / terminal, Docker & Docker Compose installés).  
- Clé/API Mistral si vous voulez activer le LLM (config via `MISTRAL_API_URL` / `MISTRAL_API_KEY`).

**1) Préparer le serveur**
- Se connecter au VPS : `ssh user@votre-vps`.
- Installer Docker & Docker Compose (si absent). Exemple Ubuntu :

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER # Ajouter votre utilisateur au groupe docker (optionnel, pour éviter sudo)
newgrp docker
docker --version
docker compose version
groups
docker ps
```

**2) Déployer le projet**
- Copier / cloner le repo sur le VPS :

```bash
git clone https://github.com/Xavier973/YanaChat-V2 yanachat && cd yanachat
```

# Créer un fichier `.env` au même niveau que `docker-compose.yml` pour les secrets :

```env
MISTRAL_API_KEY="sk_..."
# MISTRAL_API_URL n'est pas utilisé pour le moment (endpoints fixés dans src/llm_pipeline.py)
```

- (Optionnel) Éditer `docker-compose.yml` pour ajouter `restart: unless-stopped` sous le service `yana-backend` si vous préférez le déclarer ici.

**3) Démarrer le service**

```bash
docker compose pull
docker compose up -d --remove-orphans
```

Vérifier le statut :

```bash
docker compose ps
docker compose logs -f
```

**4) Assurer disponibilité 24/7 : systemd wrapper**
Créer une unité systemd pour démarrer et redémarrer automatiquement `docker compose` au boot et en cas d'échec.

Fichier exemple `/etc/systemd/system/yanachat.service` :

```ini
[Unit]
Description=YanaChat Docker Compose
After=network.target docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/<user>/yanachat
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Activer et lancer :

```bash
sudo systemctl daemon-reload
sudo systemctl enable yanachat.service
sudo systemctl start yanachat.service
sudo systemctl status yanachat.service
```

Cette unité relance `docker compose up -d` au démarrage. En cas de crash de conteneurs Docker, Docker lui‑même gère le `restart` si défini (`unless-stopped`).

**5) Logs & monitoring basique**
- Consulter logs : `docker compose logs -f yana-backend` ou via `journalctl -u yanachat.service -f`.
- Pour limiter la taille des logs, ajouter dans `docker-compose.yml` (service) :

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**6) Mise à jour / rollback**
- Pull + stop + up :

```bash
git pull
docker compose pull
docker compose up -d --remove-orphans
```
- Si nouveau conteneur pose problème : `docker compose rollback` n'existe pas — utiliser `docker compose down` et remettre l'image précédente si nécessaire (tagging d'image recommandé pour prod).

**7) Sécurité & firewall**
- Ouvrir uniquement les ports nécessaires (ex. 80/443 si reverse proxy, 8000 local pour debug). Utiliser `ufw` ou le firewall Infomaniak.
- Utiliser un reverse-proxy (Nginx) pour TLS (Let's Encrypt) devant le service, ou configurer Infomaniak pour TLS.

**8) Notes opérationnelles**
- Stocker secrets (MISTRAL_API_KEY) uniquement dans `.env` et ne pas les committer.  
- Tests de santé : votre service expose `/health` — configurez un checker externe (uptimerobot, etc.) pointant sur `https://votre-domaine/health`.
- Pour autorun auto‑update d'images : ajouter Watchtower (optionnel) dans le `docker-compose.yml`.

**Checklist PoC → Prod**
- `.env` en place et accessible par le process.  
- `restart: unless-stopped` ou gestion via systemd active.  
- Reverse proxy TLS configuré.  
- Backups réguliers (si stockage persistant ajouté).  

---
Fichier généré automatiquement par l'agent : instructions de déploiement 24/7 pour un VPS Infomaniak (Docker Compose + systemd). 
