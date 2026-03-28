#!/bin/bash
# Beyond AI — Hostinger VPS Setup
# Ubuntu 22.04 LTS
# Einmalig als root ausführen: bash server-setup.sh

set -e

echo "=== 1. System aktualisieren ==="
apt-get update && apt-get upgrade -y

echo "=== 2. Firewall (UFW) ==="
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "=== 3. Docker installieren ==="
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "=== 4. ElasticSearch — Kernel-Parameter ==="
# ES benötigt erhöhten vm.max_map_count
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p

echo "=== 5. Deployment-User anlegen ==="
useradd -m -s /bin/bash deploy || true
usermod -aG docker deploy

echo "=== 6. Projektverzeichnis ==="
mkdir -p /opt/beyond-ai
chown deploy:deploy /opt/beyond-ai

echo ""
echo "✅ Server-Setup abgeschlossen!"
echo ""
echo "Nächste Schritte:"
echo "  1. Als deploy-User einloggen: su - deploy"
echo "  2. Repo klonen: git clone https://github.com/endvater/beyond-ai /opt/beyond-ai"
echo "  3. cd /opt/beyond-ai"
echo "  4. cp .env.prod.example .env && nano .env"
echo "  5. docker compose -f docker-compose.prod.yml up -d"
