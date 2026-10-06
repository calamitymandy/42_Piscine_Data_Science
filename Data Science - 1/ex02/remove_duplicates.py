import psycopg2

# Database connection parameters
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "piscineds",
    "user":     "amdemuyn",
    "password": "mysecretpassword",
}


def get_count(cur, label=""):
    """Return and print the current row count of the customers table."""
    cur.execute("SELECT COUNT(*) FROM customers;")
    count = cur.fetchone()[0]
    if label:
        print(f"  {label}: {count:,} rows")
    return count


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True

    with conn.cursor() as cur:
        get_count(cur, "Before deduplication")

        # ── Step 1: remove exact + near-duplicates in one pass ────────────────
        # Strategy: instead of deleting from a 20M-row table (very slow),
        # we build a clean copy using DISTINCT ON and then swap the tables.
        #
        # DISTINCT ON (event_type, product_id, user_id, user_session,
        #              DATE_TRUNC('second', event_time))
        # keeps exactly one row per unique (user, session, event, product)
        # combination within each 1-second window — this handles both:
        #   - exact duplicates (same timestamp)
        #   - near-duplicates (same event sent twice within 1 second)
        #
        # ORDER BY those columns + event_time ensures we keep the earliest row.

        print("\n==> Building deduplicated copy...")
        cur.execute("""
            CREATE TABLE customers_clean AS
            SELECT DISTINCT ON (
                event_type,
                product_id,
                user_id,
                user_session,
                DATE_TRUNC('second', event_time)
            )
                event_time,
                event_type,
                product_id,
                price,
                user_id,
                user_session
            FROM customers
            ORDER BY
                event_type,
                product_id,
                user_id,
                user_session,
                DATE_TRUNC('second', event_time),
                event_time;
        """)

        # ── Step 2: swap tables ───────────────────────────────────────────────
        print("==> Swapping tables...")
        cur.execute("DROP TABLE customers;")
        cur.execute("ALTER TABLE customers_clean RENAME TO customers;")

        get_count(cur, "After deduplication")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
