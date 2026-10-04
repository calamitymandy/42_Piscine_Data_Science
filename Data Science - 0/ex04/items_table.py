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
DROP TABLE IF EXISTS items;
"""

# SQL statement to create the items table.
# Column names match the item.csv header exactly:
#   product_id, category_id, category_code, brand
#
# Data types chosen:
#   INTEGER   — product_id fits in a 32-bit integer
#   BIGINT    — category_id values exceed int range (e.g. 1487580005268456192)
#   TEXT      — category_code is a variable-length dot-separated string
#               (e.g. "electronics.smartphone"), can also be empty/null
#   VARCHAR   — brand is a short name with a reasonable length cap
#
# That gives us 4 distinct data types, satisfying the 3-type minimum.
CREATE_TABLE = """
CREATE TABLE items (
    product_id    INTEGER,
    category_id   BIGINT,
    category_code TEXT,
    brand         VARCHAR(100)
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
        print("Table 'items' created successfully.")

    conn.close()

if __name__ == "__main__":
    main()
