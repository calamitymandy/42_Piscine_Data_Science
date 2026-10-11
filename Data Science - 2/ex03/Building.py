import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# ── Database connection ───────────────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://amdemuyn:mysecretpassword@localhost:5432/piscineds"
)

# ── Query: purchase frequency per customer ────────────────────────────────────
freq_df = pd.read_sql("""
    SELECT user_id, COUNT(*) AS frequency
    FROM customers
    WHERE event_type = 'purchase'
    GROUP BY user_id;
""", engine)

# ── Query: total spend (monetary value) per customer ─────────────────────────
spend_df = pd.read_sql("""
    SELECT user_id, SUM(price) AS monetary
    FROM customers
    WHERE event_type = 'purchase'
    GROUP BY user_id;
""", engine)

# ── Bin the data to match the subject's histogram-style bar charts ─────────────
# Left chart: frequency bins of width 5 (0-5, 5-10, 10-15 ...), cap at ~40
freq_bins  = range(0, 45, 5)
freq_df["freq_bin"] = pd.cut(freq_df["frequency"], bins=freq_bins, right=False)
freq_counts = freq_df.groupby("freq_bin", observed=True).size().reset_index(name="customers")
freq_counts["bin_label"] = freq_counts["freq_bin"].apply(lambda x: int(x.left))

# Right chart: monetary bins of width 50 (0-50, 50-100 ...), cap at ~250
spend_bins = range(-50, 300, 50)
spend_df["spend_bin"] = pd.cut(spend_df["monetary"], bins=spend_bins, right=False)
spend_counts = spend_df.groupby("spend_bin", observed=True).size().reset_index(name="customers")
spend_counts["bin_label"] = spend_counts["spend_bin"].apply(lambda x: int(x.left))

# ── Plot ──────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: frequency
sns.barplot(data=freq_counts, x="bin_label", y="customers", ax=ax1, color="steelblue")
ax1.set_xlabel("frequency")
ax1.set_ylabel("customers")
ax1.tick_params(axis="x", rotation=0)

# Right: monetary value
sns.barplot(data=spend_counts, x="bin_label", y="customers", ax=ax2, color="steelblue")
ax2.set_xlabel("monetary value in A$")
ax2.set_ylabel("customers")
ax2.tick_params(axis="x", rotation=0)

plt.tight_layout()
plt.savefig("Building.png", dpi=150)
plt.show()
print("Chart saved to Building.png")
