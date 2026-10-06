import os
import psycopg2

# Database connection parameters
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "piscineds",
    "user":     "amdemuyn",
    "password": "mysecretpassword",
}

# Paths to the CSV data directories
CUSTOMER_DIR = os.path.join(os.path.dirname(__file__), "../../subject/customer")

# All monthly tables and their CSV sources.
# Each entry is (table_name, absolute_path_to_csv).
MONTHLY_TABLES = [
    ("data_2022_oct", os.path.join(CUSTOMER_DIR, "data_2022_oct.csv")),
    ("data_2022_nov", os.path.join(CUSTOMER_DIR, "data_2022_nov.csv")),
    ("data_2022_dec", os.path.join(CUSTOMER_DIR, "data_2022_dec.csv")),
    ("data_2023_jan", os.path.join(CUSTOMER_DIR, "data_2023_jan.csv")),
    ("data_2023_feb", os.path.join(CUSTOMER_DIR, "data_2023_feb.csv")),
]

# SQL to create one monthly table (same structure for all customer CSVs).
# {table_name} is replaced at runtime.
CREATE_MONTHLY_SQL = """
CREATE TABLE {table_name} (
    event_time   TIMESTAMP,
    event_type   VARCHAR(20),
    product_id   INTEGER,
    price        FLOAT,
    user_id      BIGINT,
    user_session UUID
);
"""

# SQL to create the unified customers table (same columns as the monthly tables)
CREATE_CUSTOMERS_SQL = """
CREATE TABLE customers (
    event_time   TIMESTAMP,
    event_type   VARCHAR(20),
    product_id   INTEGER,
    price        FLOAT,
    user_id      BIGINT,
    user_session UUID
);
"""


def recreate_monthly_table(cur, table_name, csv_path):
    """Drop, recreate and load one monthly table from its CSV file."""
    print(f"  [{table_name}] dropping and recreating...")
    cur.execute(f"DROP TABLE IF EXISTS {table_name};")
    cur.execute(CREATE_MONTHLY_SQL.format(table_name=table_name))

    # COPY is the fastest way to bulk-load CSV data into PostgreSQL.
    # We open the file in Python and use copy_expert so the path stays
    # on the client side (works even inside Docker).
    abs_path = os.path.abspath(csv_path)
    print(f"  [{table_name}] loading data from {os.path.basename(abs_path)}...")
    with open(abs_path, "r") as f:
        # HEADER tells PostgreSQL to skip the first line (column names)
        cur.copy_expert(
            f"COPY {table_name} FROM STDIN WITH CSV HEADER",
            f
        )
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cur.fetchone()[0]
    print(f"  [{table_name}] {count:,} rows loaded.")


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True

    with conn.cursor() as cur:

        # ── Step 1: load all monthly tables ──────────────────────────────────
        print("==> Loading monthly tables...")
        for table_name, csv_path in MONTHLY_TABLES:
            recreate_monthly_table(cur, table_name, csv_path)
        print()

        # ── Step 2: create the unified customers table ────────────────────────
        print("==> Creating 'customers' table...")
        cur.execute("DROP TABLE IF EXISTS customers;")
        cur.execute(CREATE_CUSTOMERS_SQL)

        # Insert all rows from every monthly table into customers
        for table_name, _ in MONTHLY_TABLES:
            print(f"  Inserting from {table_name}...")
            cur.execute(f"INSERT INTO customers SELECT * FROM {table_name};")

        cur.execute("SELECT COUNT(*) FROM customers;")
        total = cur.fetchone()[0]
        print(f"\n  'customers' table ready: {total:,} total rows.")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
