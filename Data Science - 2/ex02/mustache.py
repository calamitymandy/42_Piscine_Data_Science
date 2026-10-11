import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# ── Database connection ───────────────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://amdemuyn:mysecretpassword@localhost:5432/piscineds"
)

# ── Query: all purchase prices ────────────────────────────────────────────────
prices = pd.read_sql("""
    SELECT price
    FROM customers
    WHERE event_type = 'purchase';
""", engine)["price"]

# ── Query: average spend per customer per day ─────────────────────────────────
avg_spend = pd.read_sql("""
    SELECT SUM(price) / COUNT(DISTINCT user_id) AS avg_spend
    FROM customers
    WHERE event_type = 'purchase'
    GROUP BY DATE_TRUNC('day', event_time);
""", engine)["avg_spend"]

# ── Print stats ───────────────────────────────────────────────────────────────
print(prices.describe().round(6).to_string())
print()

# ── Seaborn style ─────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid")

# ── Plot 1: full price range (all purchases, shows outliers) ──────────────────
fig1, ax1 = plt.subplots(figsize=(8, 4))
sns.boxplot(x=prices, ax=ax1, color="dimgray", flierprops={"marker": "D", "markersize": 3})
ax1.set_xlabel("price")
ax1.set_ylabel("")
plt.tight_layout()
plt.savefig("mustache_all_prices.png", dpi=150)
plt.show()

# ── Plot 2: item prices zoomed in (IQR view, no extreme outliers) ─────────────
# Clip to the range visible in the subject: 0 to ~13 (1.5*IQR filter)
q1, q3 = prices.quantile(0.25), prices.quantile(0.75)
iqr = q3 - q1
prices_filtered = prices[(prices >= q1 - 1.5 * iqr) & (prices <= q3 + 1.5 * iqr)]

fig2, ax2 = plt.subplots(figsize=(8, 4))
sns.boxplot(x=prices_filtered, ax=ax2, color="mediumseagreen",
            flierprops={"marker": "D", "markersize": 3})
ax2.set_xlabel("price")
ax2.set_ylabel("")
plt.tight_layout()
plt.savefig("mustache_item_prices.png", dpi=150)
plt.show()

# ── Plot 3: average basket per customer per day ───────────────────────────────
fig3, ax3 = plt.subplots(figsize=(8, 4))
sns.boxplot(x=avg_spend, ax=ax3, color="steelblue",
            flierprops={"marker": "D", "markersize": 3})
ax3.set_xlabel("price")
ax3.set_ylabel("")
plt.tight_layout()
plt.savefig("mustache_avg_basket.png", dpi=150)
plt.show()

print("Plots saved.")
