import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# ── Database connection ───────────────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://amdemuyn:mysecretpassword@localhost:5432/piscineds"
)

# ── Query ─────────────────────────────────────────────────────────────────────
# Count how many events of each type exist in the customers table.
query = """
    SELECT event_type, COUNT(*) AS count
    FROM customers
    GROUP BY event_type
    ORDER BY count DESC;
"""
df = pd.read_sql(query, engine)

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 8))

# autopct shows the percentage inside each slice
# startangle=90 puts the first slice at the top
wedges, texts, autotexts = ax.pie(
    df["count"],
    labels=df["event_type"],
    autopct="%1.1f%%",
    startangle=90,
    counterclock=False,
)

# Make percentage labels bold and readable
for autotext in autotexts:
    autotext.set_fontsize(11)
    autotext.set_fontweight("bold")

ax.set_title("Customer Events on the Site", fontsize=16, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("pie.png", dpi=150)
plt.show()
print("Chart saved to pie.png")
