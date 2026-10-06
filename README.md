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


## Create table from CSV (ex02)

1. Run the script

   - python3 ex02/table.py
  We see: Table 'data_2022_oct' created successfully.
  
2. Connect to the DB and describe the table
   - psql -U amdemuyn -d piscineds -h localhost -W
   - Then inside psql: \d data_2022_oct
  
  We see the table structure with all 6 types.
  
  We can also show it in pgAdmin (ex01 tool) — navigate to piscineds > Schemas > public > Tables >
  data_2022_oct and right-click → Properties. More visual.



----------------------------------------------------------


# Piscine DataScience - 1 : Data Warehouse
## ex02

To show that there is no duplicates with psql:
Connect to psql and run a few queries:
  
  psql -U amdemuyn -d piscineds -h localhost -W
  
  Then inside:
  
  -- row count
  SELECT COUNT(*) FROM customers;
  
  -- check there are no exact duplicates left
  SELECT COUNT(*) FROM customers
  EXCEPT
  SELECT COUNT(*) FROM (SELECT DISTINCT * FROM customers) AS d;
  
  -- peek at the data
  SELECT * FROM customers LIMIT 5;
  
  -- see all tables
  \dt


## ex03

We build a new fused table then swap it in, which is much faster than adding columns and running an UPDATE on 19M rows. The duplicates have different category_id or brand — some rows have nulls, others have values. The right strategy is to keep the most informative row per product_id (prefer non-null values).

The fusion.py script will:
  1. Load item.csv into the items table
  2. Add the 3 new columns (category_id, category_code, brand) to customers
  3. Populate them via a LEFT JOIN with items on product_id

customers now has 9 columns — the original 6 plus category_id, category_code, and brand from
items. Row count unchanged at 19,583,741.

Shell PGPASSWORD=mysecretpassword psql -U amdemuyn -d piscineds -h localhost -c "
  SELECT
      COUNT(*)                          AS total_rows,
      COUNT(category_id)                AS rows_with_category_id,
      COUNT(brand)                      AS rows_with_brand,
      COUNT(*) - COUNT(category_id)     AS rows_without_match
  FROM customers;
  "
     total_rows | rows_with_category_id | rows_with_brand | rows_without_match 
    ------------+-----------------------+-----------------+--------------------
       19583741 |              19582393 |        11404851 |               1348
    (1 row)

• - 19,583,741 total rows — unchanged ✅
  - 19,582,393 rows matched a product in items and got category_id
  - 1,348 rows had a product_id not present in items at all — they got NULL for the item columns,
  which is correct for a LEFT JOIN
  - 11,404,851 rows have a brand (the rest have null brand in items itself — that's the source
  data being incomplete)
  
  No customer rows were lost. The 1,348 nulls are expected — those product IDs simply don't exist
  in the items catalogue.


-> to show the columns: \d customers 