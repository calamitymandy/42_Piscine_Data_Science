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

# Path to item.csv
ITEM_CSV = os.path.join(os.path.dirname(__file__), "../../subject/item/item.csv")


def load_items(cur):
    """Reload the items table from item.csv."""
    print("==> Loading items table...")
    cur.execute("TRUNCATE TABLE items;")
    with open(os.path.abspath(ITEM_CSV), "r") as f:
        cur.copy_expert("COPY items FROM STDIN WITH CSV HEADER", f)
    cur.execute("SELECT COUNT(*) FROM items;")
    print(f"  {cur.fetchone()[0]:,} rows loaded into items.")


def fuse(cur):
    """
    Merge items data into customers using a LEFT JOIN on product_id.

    We use LEFT JOIN so that every row in customers is preserved, even if
    the product_id has no match in items (those rows get NULL for the
    item columns). This satisfies the subject's requirement of not losing
    any information.

    items itself contains duplicate product_ids with varying non-null values.
    We first deduplicate it using DISTINCT ON, keeping the most informative
    row per product_id (prefer non-null category_id, then non-null brand).

    Strategy: build a new fused table then swap it in, which is much faster
    than adding columns and running an UPDATE on 19M rows.
    """
    print("\n==> Fusing customers with items...")
    cur.execute("""
        CREATE TABLE customers_fused AS
        SELECT
            c.event_time,
            c.event_type,
            c.product_id,
            c.price,
            c.user_id,
            c.user_session,
            i.category_id,
            i.category_code,
            i.brand
        FROM customers c
        LEFT JOIN (
            -- Deduplicate items: one row per product_id,
            -- preferring rows with non-null category_id and brand.
            SELECT DISTINCT ON (product_id)
                product_id,
                category_id,
                category_code,
                brand
            FROM items
            ORDER BY
                product_id,
                category_id NULLS LAST,
                brand        NULLS LAST
        ) i ON c.product_id = i.product_id;
    """)

    cur.execute("DROP TABLE customers;")
    cur.execute("ALTER TABLE customers_fused RENAME TO customers;")

    cur.execute("SELECT COUNT(*) FROM customers;")
    print(f"  customers now has {cur.fetchone()[0]:,} rows.")


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True

    with conn.cursor() as cur:
        load_items(cur)
        fuse(cur)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
