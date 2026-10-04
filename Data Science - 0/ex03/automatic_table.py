import os
import psycopg2

# Database connection parameters
# These match the credentials defined in the docker-compose stack (ex00)
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "piscineds",
    "user":     "amdemuyn",
    "password": "mysecretpassword",
}

# Path to the folder containing the customer CSV files.
# Adjust this path if running from a different working directory.
CUSTOMER_DIR = os.path.join(os.path.dirname(__file__), "../subject/customer")

# SQL template to create a customer table.
# All customer CSVs share the same columns and types:
#   event_time   TIMESTAMP  — date + time of the event
#   event_type   VARCHAR    — type of action (view, cart, purchase…)
#   product_id   INTEGER    — product identifier
#   price        FLOAT      — item price
#   user_id      BIGINT     — customer identifier (exceeds int range)
#   user_session UUID       — session identifier in UUID format
#
# {table_name} is replaced at runtime with the CSV filename (without extension).
CREATE_TABLE_SQL = """
CREATE TABLE {table_name} (
    event_time   TIMESTAMP,
    event_type   VARCHAR(20),
    product_id   INTEGER,
    price        FLOAT,
    user_id      BIGINT,
    user_session UUID
);
"""

def create_table(cursor, table_name):
    """Drop the table if it exists, then recreate it."""
    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    cursor.execute(CREATE_TABLE_SQL.format(table_name=table_name))
    print(f"  Table '{table_name}' created.")

def main():
    # Collect all CSV files in the customer directory
    csv_files = sorted([
        f for f in os.listdir(CUSTOMER_DIR)
        if f.endswith(".csv")
    ])

    if not csv_files:
        print(f"No CSV files found in {CUSTOMER_DIR}")
        return

    print(f"Found {len(csv_files)} CSV file(s) in {CUSTOMER_DIR}:")
    for f in csv_files:
        print(f"  - {f}")
    print()

    # Connect to the database
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True

    with conn.cursor() as cur:
        for filename in csv_files:
            # Table name = filename without the .csv extension
            table_name = os.path.splitext(filename)[0]
            create_table(cur, table_name)

    conn.close()
    print("\nAll tables created successfully.")

if __name__ == "__main__":
    main()
