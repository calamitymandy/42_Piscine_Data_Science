import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sqlalchemy import create_engine
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ── Database connection ───────────────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://amdemuyn:mysecretpassword@localhost:5432/piscineds"
)

# ── Build RFM features per customer ──────────────────────────────────────────
max_date = pd.read_sql(
    "SELECT MAX(event_time) AS max_date FROM customers WHERE event_type = 'purchase';",
    engine
)["max_date"].iloc[0]

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

rfm["recency"] = (max_date - rfm["last_purchase"]).dt.days
features = rfm[["recency", "frequency", "monetary"]].fillna(0)

# ── Scale and cluster with k=4 ────────────────────────────────────────────────
# k=4 chosen from the elbow method: inertia stops dropping sharply after k=4.
scaler = StandardScaler()
X = scaler.fit_transform(features)

km = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["cluster"] = km.fit_predict(X)

# ── Label clusters based on RFM profile ──────────────────────────────────────
# Each cluster is characterised by its median recency, frequency and monetary.
# We assign human-readable names based on those medians:
#   - Low recency + high frequency + high monetary  → Loyal customers
#   - Low recency + low frequency + low monetary    → New customers
#   - High recency + low frequency                  → Inactive customers
#   - Low recency + low frequency + high monetary   → Big spenders
summary = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].median()
print("Cluster medians:")
print(summary.round(1))
print()

# Sort clusters to assign labels consistently
summary_sorted = summary.sort_values(["recency", "frequency", "monetary"],
                                     ascending=[True, False, False])
labels = ["Loyal customers", "New customers", "Big spenders", "Inactive customers"]
label_map = {cluster: label for cluster, label in
             zip(summary_sorted.index, labels)}
rfm["label"] = rfm["cluster"].map(label_map)

# ── Colors per group ──────────────────────────────────────────────────────────
palette = {
    "Loyal customers":    "#f0c896",   # orange/tan
    "New customers":      "#a8bcd4",   # blue/grey
    "Big spenders":       "#c8a0c8",   # purple
    "Inactive customers": "#6dbfaa",   # green
}

# ── Chart 1: horizontal bar chart — customers per cluster ─────────────────────
counts = rfm["label"].value_counts().reset_index()
counts.columns = ["label", "count"]
counts = counts.sort_values("count", ascending=True)

fig1, ax1 = plt.subplots(figsize=(10, 5))
bars = ax1.barh(counts["label"], counts["count"],
                color=[palette[l] for l in counts["label"]])
# Add count labels at the end of each bar
for bar, val in zip(bars, counts["count"]):
    ax1.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
             f"{val:,}", va="center", fontsize=10)
ax1.set_xlabel("number of customers")
ax1.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("Clustering_barchart.png", dpi=150)
plt.show()

# ── Chart 2: bubble chart — recency vs frequency, size = monetary ─────────────
# Recency in months for readability
rfm["recency_months"] = rfm["recency"] / 30

bubble = rfm.groupby("label").agg(
    med_recency=("recency_months", "median"),
    med_frequency=("frequency", "median"),
    avg_monetary=("monetary", "mean")
).reset_index()

fig2, ax2 = plt.subplots(figsize=(8, 6))
for _, row in bubble.iterrows():
    ax2.scatter(
        row["med_recency"], row["med_frequency"],
        s=row["avg_monetary"] * 3,      # bubble size proportional to spend
        color=palette[row["label"]],
        alpha=0.7, edgecolors="white", linewidths=1
    )
    ax2.annotate(
        f'Average "{row["label"]}": {row["avg_monetary"]:.0f}A$',
        (row["med_recency"], row["med_frequency"]),
        textcoords="offset points", xytext=(10, 5), fontsize=9
    )

ax2.set_xlabel("Median Recency (month)")
ax2.set_ylabel("Median Frequency")
ax2.set_xlim(-0.5, bubble["med_recency"].max() + 1)
ax2.set_ylim(0, bubble["med_frequency"].max() * 1.4)
sns.set_theme(style="whitegrid")
plt.tight_layout()
plt.savefig("Clustering_bubble.png", dpi=150)
plt.show()

# ── Chart 3: scatter plot — frequency vs monetary, coloured by cluster ─────────
# Sample 2000 points for readability (plotting all 80k would be too dense)
sample = rfm.sample(2000, random_state=42)

fig3, ax3 = plt.subplots(figsize=(10, 6))
for label, group in sample.groupby("label"):
    ax3.scatter(group["monetary"], group["frequency"],
                color=palette[label], label=label, alpha=0.5, s=15)

# Plot centroids (in original scale)
centers_scaled = km.cluster_centers_
centers_original = scaler.inverse_transform(centers_scaled)
centers_df = pd.DataFrame(centers_original,
                           columns=["recency", "frequency", "monetary"])
ax3.scatter(centers_df["monetary"], centers_df["frequency"],
            color="yellow", s=200, marker="o", edgecolors="black",
            linewidths=1, zorder=5, label="Centroids")

ax3.set_xlabel("Monetary (A$)")
ax3.set_ylabel("Frequency")
ax3.set_title("Clusters")
ax3.legend()
plt.tight_layout()
plt.savefig("Clustering_scatter.png", dpi=150)
plt.show()

print("\nCluster summary:")
print(rfm.groupby("label")[["recency", "frequency", "monetary"]].mean().round(1))
print("\nCharts saved.")
