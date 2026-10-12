#!/bin/bash
# setup.sh — creates the .env file and starts the Docker Compose stack

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# ── 1. Create .env if missing ─────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
  echo "==> Creating .env..."
  cat > "$ENV_FILE" <<EOF
POSTGRES_USER=amdemuyn
POSTGRES_DB=piscineds
POSTGRES_PASSWORD=mysecretpassword
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
EOF
fi

# ── 2. Start the stack ────────────────────────────────────────────────────────
echo "==> Starting Docker Compose stack..."
cd "$SCRIPT_DIR"
docker compose --env-file "$ENV_FILE" up -d

echo ""
echo "✅  Stack is up!"
echo "   PostgreSQL : localhost:5432"
echo "   pgAdmin    : http://localhost:8080"
echo ""
echo "   Connect with:"
echo "   psql -U amdemuyn -d piscineds -h localhost -W"
echo "   password: mysecretpassword"
