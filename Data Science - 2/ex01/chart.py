import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# ── Database connection ───────────────────────────────────────────────────────
engine = create_engine(
    "postgresql+psycopg2://amdemuyn:mysecretpassword@localhost:5432/piscineds"
)

# ── Query: daily purchase data ────────────────────────────────────────────────
daily_query = """
    SELECT
        DATE_TRUNC('day', event_time)          AS day,
        COUNT(DISTINCT user_id)                AS num_customers,
        SUM(price)                             AS total_revenue,
        SUM(price) / COUNT(DISTINCT user_id)   AS avg_spend_per_customer
    FROM customers
    WHERE event_type = 'purchase'
    GROUP BY day
    ORDER BY day;
"""
daily = pd.read_sql(daily_query, engine)
daily["day"] = pd.to_datetime(daily["day"])

# ── Query: monthly purchase data ──────────────────────────────────────────────
monthly_query = """
    SELECT
        TO_CHAR(DATE_TRUNC('month', event_time), 'Mon') AS month,
        DATE_TRUNC('month', event_time)                 AS month_order,
        SUM(price) / 1e6                                AS total_sales_millions
    FROM customers
    WHERE event_type = 'purchase'
    GROUP BY month_order, month
    ORDER BY month_order;
"""
monthly = pd.read_sql(monthly_query, engine)

# ── Seaborn style (matches the subject's look) ────────────────────────────────
sns.set_theme(style="darkgrid")

# ── Chart 1: Number of customers per day (line chart) ────────────────────────
fig1, ax1 = plt.subplots(figsize=(10, 8))
sns.lineplot(data=daily, x="day", y="num_customers", ax=ax1)
ax1.set_title("")
ax1.set_xlabel("")
ax1.set_ylabel("Number of customers")
ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b"))
ax1.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator())
plt.tight_layout()
plt.savefig("chart_customers_per_day.png", dpi=150)
plt.show()

# ── Chart 2: Total sales per month (bar chart) ────────────────────────────────
fig2, ax2 = plt.subplots(figsize=(8, 6))
sns.barplot(data=monthly, x="month", y="total_sales_millions", ax=ax2, color="steelblue")
ax2.set_title("")
ax2.set_xlabel("month")
ax2.set_ylabel("total sales in million of A$")
plt.tight_layout()
plt.savefig("chart_sales_per_month.png", dpi=150)
plt.show()

# ── Chart 3: Average spend per customer per day (area chart) ─────────────────
fig3, ax3 = plt.subplots(figsize=(10, 8))
ax3.fill_between(daily["day"], daily["avg_spend_per_customer"], alpha=0.4, color="steelblue")
ax3.plot(daily["day"], daily["avg_spend_per_customer"], color="steelblue", linewidth=0.8)
ax3.set_xlabel("")
ax3.set_ylabel("average spend/customers in A$")
ax3.set_ylim(bottom=0)
ax3.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%b"))
ax3.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator())
# Apply the same darkgrid background manually for the area chart
ax3.set_facecolor("#eaeaf2")
ax3.grid(color="white", linewidth=1)
plt.tight_layout()
plt.savefig("chart_avg_spend_per_day.png", dpi=150)
plt.show()

print("Charts saved.")
