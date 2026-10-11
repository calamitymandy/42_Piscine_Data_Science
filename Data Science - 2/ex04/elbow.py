import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ── Database connection ───────────────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://amdemuyn:mysecretpassword@localhost:5432/piscineds"
)

# ── Build RFM features per customer ──────────────────────────────────────────
# RFM summarises each customer with 3 numbers:
#   Recency   — days since their last purchase (0 = bought very recently)
#   Frequency — total number of purchases
#   Monetary  — total amount spent in A$

# Get the most recent purchase date in the whole dataset
max_date = pd.read_sql(
    "SELECT MAX(event_time) AS max_date FROM customers WHERE event_type = 'purchase';",
    engine
)["max_date"].iloc[0]

# Aggregate per customer
rfm = pd.read_sql("""
    SELECT
        user_id,
        COUNT(*)        AS frequency,
        SUM(price)      AS monetary,
        MAX(event_time) AS last_purchase
    FROM customers
    WHERE event_type = 'purchase'
    GROUP BY user_id;
""", engine)

# Recency = days between customer's last purchase and the dataset's last date
rfm["recency"] = (max_date - rfm["last_purchase"]).dt.days
features = rfm[["recency", "frequency", "monetary"]].fillna(0)

# ── Scale features ────────────────────────────────────────────────────────────
# K-means is distance-based, so all features must be on the same scale.
# StandardScaler transforms each feature to have mean=0 and std=1.
scaler = StandardScaler()
X = scaler.fit_transform(features)

# ── Elbow method: compute inertia for k = 1 to 10 ────────────────────────────
# Inertia = sum of squared distances from each customer to their group centre.
# The "elbow" is where the curve stops dropping sharply — that's the best k.
inertias = []
k_range = range(1, 11)

print("Computing inertia for k = 1 to 10...")
for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X)
    inertias.append(km.inertia_)
    print(f"  k={k}: inertia={km.inertia_:,.0f}")

# ── Plot ──────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid")
fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(k_range, inertias, color="steelblue", linewidth=1.5)
ax.set_title("The Elbow Method")
ax.set_xlabel("Number of clusters")
ax.set_ylabel("Inertia")

plt.tight_layout()
plt.savefig("elbow.png", dpi=150)
plt.show()
print("Chart saved to elbow.png")
