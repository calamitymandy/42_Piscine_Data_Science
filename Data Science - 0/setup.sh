#!/bin/bash
# setup.sh — Run this on school Linux machines to start the project
# It installs Docker if needed (via goinfre) and launches the stack.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
GOINFRE="$HOME/goinfre"

# ── 1. Detect OS ────────────────────────────────────────────────────────────
OS="$(uname -s)"
echo "==> Detected OS: $OS"

# ── 2. Check Docker ──────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "==> Docker not found."
  if [ "$OS" = "Linux" ]; then
    echo "==> Attempting to install Docker via goinfre..."
    if [ ! -d "$GOINFRE" ]; then
      echo "ERROR: $GOINFRE does not exist. Are you on a 42 school machine?"
      exit 1
    fi
    # Move Docker's data root to goinfre to avoid filling your session quota
    mkdir -p "$GOINFRE/docker"
    if ! command -v apt-get &>/dev/null; then
      echo "ERROR: apt-get not found. Install Docker manually, then re-run this script."
      exit 1
    fi
    sudo apt-get update -qq
    sudo apt-get install -y docker.io docker-compose-v2
    # Reconfigure Docker daemon to store data in goinfre
    sudo mkdir -p /etc/docker
    echo "{\"data-root\": \"$GOINFRE/docker\"}" | sudo tee /etc/docker/daemon.json > /dev/null
    sudo systemctl restart docker || sudo service docker restart
    sudo usermod -aG docker "$USER"
    echo "==> Docker installed. You may need to log out and back in for group changes."
    echo "    Re-run this script after logging back in."
    exit 0
  else
    echo "ERROR: Docker not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
  fi
fi

# ── 3. Check Docker is running ───────────────────────────────────────────────
if ! docker info &>/dev/null; then
  echo "==> Docker daemon is not running."
  if [ "$OS" = "Linux" ]; then
    echo "==> Starting Docker..."
    sudo systemctl start docker || sudo service docker start
  else
    echo "==> Please start Docker Desktop and try again."
    exit 1
  fi
fi

echo "==> Docker is ready."

# ── 4. Create .env if missing ────────────────────────────────────────────────
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "==> .env not found, creating it..."
  cat > "$ENV_FILE" <<EOF
POSTGRES_USER=amdemuyn
POSTGRES_DB=piscineds
POSTGRES_PASSWORD=mysecretpassword
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
EOF
  echo "==> .env created."
fi

# ── 5. Launch the stack ──────────────────────────────────────────────────────
echo "==> Starting Docker Compose stack..."
cd "$PROJECT_DIR/ex00"
docker compose --env-file "$ENV_FILE" up -d

echo ""
echo "✅  Stack is up!"
echo "   PostgreSQL : localhost:5432  (user: amdemuyn  db: piscineds)"
echo "   pgAdmin    : http://localhost:8080  (email: admin@admin.com  password: admin)"
echo ""
echo "   To connect via psql:"
echo "   psql -U amdemuyn -d piscineds -h localhost -W"
echo ""
echo "   To stop: docker compose -f ex00/docker-compose.yml down"
