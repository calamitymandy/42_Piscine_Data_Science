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

# Drop the table if it already exists, then recreate it from scratch.
# This avoids errors when running the script multiple times (e.g. during eval).
DROP_TABLE = """
DROP TABLE IF EXISTS data_2022_oct;
"""

# SQL statement to create the table
# Column order and names match the CSV header exactly:
#   event_time, event_type, product_id, price, user_id, user_session
#
# Data types chosen:
#   TIMESTAMP  — date + time without timezone (e.g. "2022-10-01 00:00:00 UTC")
#   VARCHAR    — short variable-length string (event types are small words)
#   INTEGER    — 32-bit whole number (product IDs fit in int range)
#   FLOAT      — floating-point number (prices have decimals)
#   BIGINT     — 64-bit whole number (user IDs exceed int range)
#   UUID       — universally unique identifier (user_session format)
#
# That gives us 6 distinct data types as required by the subject.
# TIMESTAMP is the first column, also as required.
CREATE_TABLE = """
CREATE TABLE data_2022_oct (
    event_time   TIMESTAMP,
    event_type   VARCHAR(20),
    product_id   INTEGER,
    price        FLOAT,
    user_id      BIGINT,
    user_session UUID
);
"""

def main():
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**DB_CONFIG)

    # autocommit=True so we don't need an explicit COMMIT after DDL statements
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(DROP_TABLE)
        cur.execute(CREATE_TABLE)
        print("Table 'data_2022_oct' created successfully.")

    conn.close()

if __name__ == "__main__":
    main()
