# Piscine DataScience - 0 : Creation of a DB

## Project structure

```
Data Science - 0/
├── .env                  ← credentials (not committed)
├── .gitignore
├── setup.sh              ← one-command start (Mac + Linux)
├── ex00/
│   └── docker-compose.yml   ← PostgreSQL + pgAdmin
├── ex01/                 ← pgAdmin GUI (same stack as ex00)
├── ex02/                 ← table.* SQL script
├── ex03/                 ← automatic_table.* script
└── ex04/                 ← items_table.* script
```

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac)
- Docker + docker-compose-v2 (Linux school machines — see below)

---

## Quick start

```bash
./setup.sh
```

That's it. The script handles everything: checks Docker, creates `.env` if missing, and starts the stack.

---

## Manual start

```bash
cd ex00
docker compose --env-file ../.env up -d
```

---

## Connecting to the database

```bash
psql -U amdemuyn -d piscineds -h localhost -W
# password: mysecretpassword
```

> **Mac only:** if `psql` is not found, install the client (no full server needed):
> ```bash
> brew install libpq && brew link --force libpq
> ```
> On school Linux machines `psql` is usually already available system-wide.

Some useful commands to know from this prompt:
  
  \l          -- list all databases
  \du         -- list users/roles
  \dt         -- list tables (useful later for ex02-04)
  \q          -- quit

## pgAdmin (ex01)

Open http://localhost:8080 in your browser.

- Email: `admin@admin.com`
- Password: `admin`

To add the server in pgAdmin:
1. Right-click **Servers** → **Register** → **Server**
2. Name: `piscineds`
3. Connection tab:
   - Host: `postgresql` (the Docker service name, not localhost)
   - Port: `5432`
   - Database: `piscineds`
   - Username: `amdemuyn`
   - Password: `mysecretpassword`

---

## Stop / clean up

```bash
# Stop containers (data persisted in Docker volumes)
docker compose -f ex00/docker-compose.yml down

# Stop AND delete all data (full reset)
docker compose -f ex00/docker-compose.yml down -v
```

---

## School Linux machines (no VM)

The school machines use **goinfre** for extra disk space (your session quota is small).
The `setup.sh` script automatically:
1. Installs Docker if missing (via `apt-get`)
2. Redirects Docker's data directory to `~/goinfre/docker` to avoid quota issues
3. Starts the stack

Just run:
```bash
./setup.sh
```

> ⚠️ After a first-time Docker install on Linux you may need to log out and back in,
> then run `./setup.sh` again so your user is in the `docker` group.

### Transferring the project to school

Option A — git (recommended):
```bash
git clone <your-repo-url>
cd "Data Science - 0"
./setup.sh
```

Option B — USB / scp:
```bash
scp -r "Data Science - 0" amdemuyn@<school-machine>:~/
```

---

## Credentials summary

| Service    | Value              |
|------------|--------------------|
| DB user    | `amdemuyn`         |
| DB name    | `piscineds`        |
| DB password| `mysecretpassword` |
| pgAdmin email | `admin@admin.com` |
| pgAdmin password | `admin`     |
| PostgreSQL port | `5432`        |
| pgAdmin port    | `8080`        |
