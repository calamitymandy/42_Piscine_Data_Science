import sys
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

# ── Usage ─────────────────────────────────────────────────────────────────────
# python3 Normalization.py Train_knight.csv
# python3 Normalization.py Test_knight.csv

DATA_DIR = "../../subject/"

if len(sys.argv) != 2:
    print("Usage: python3 Normalization.py <Train_knight.csv | Test_knight.csv>")
    sys.exit(1)

filename = sys.argv[1]
df = pd.read_csv(DATA_DIR + filename)

# Separate the features (skills) from the target column 'knight' (Jedi/Sith)
features = [c for c in df.columns if c != "knight"]
X = df[features]

# ── Print original data ───────────────────────────────────────────────────────
print(X.to_string(index=False))
print()

# ── What is normalization? ────────────────────────────────────────────────────
# Like standardization, normalization rescales features so they are all
# on the same scale — but instead of centering around 0, it squashes every
# feature into the range [0, 1].
#
# Formula for each value:  z = (x - min) / (max - min)
#
# After normalization:
#   - The smallest value in a feature becomes 0
#   - The largest value in a feature becomes 1
#   - Everything else is in between
#
# When to use normalization vs standardization:
#   - Normalization is better when you know the data has hard boundaries
#     (e.g. pixel values 0-255, percentages 0-100)
#   - Standardization is better when the data may have outliers, because
#     one extreme value won't stretch the whole scale to 0 or 1
#
# For this dataset both work — we use normalization here as required by ex04.
scaler = MinMaxScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=features)

# ── Print normalized data ─────────────────────────────────────────────────────
# All values are now between 0 and 1
print(X_scaled.to_string(index=False))

# ── Scatter plot with normalized data ────────────────────────────────────────
# We use the MIXING pair (Pull vs Deflection) — the "other" graph from ex02.
# This pair shows Jedi and Sith overlapping even after normalization,
# confirming these features have no predictive power regardless of scaling.
fig, ax = plt.subplots(figsize=(7, 6))

if "knight" in df.columns:
    # Train file: colour by Jedi / Sith
    jedi = X_scaled[df["knight"] == "Jedi"]
    sith = X_scaled[df["knight"] == "Sith"]
    ax.scatter(sith["Pull"], sith["Deflection"],
               label="Sith", color="salmon", alpha=0.5, s=30)
    ax.scatter(jedi["Pull"], jedi["Deflection"],
               label="Jedi", color="steelblue", alpha=0.5, s=30)
else:
    # Test file: no labels, single green color
    ax.scatter(X_scaled["Pull"], X_scaled["Deflection"],
               label="Knight", color="mediumseagreen", alpha=0.6, s=30)

ax.set_xlabel("Pull (normalized)")
ax.set_ylabel("Deflection (normalized)")
ax.legend()
plt.tight_layout()
output = filename.replace(".csv", "_normalized.png")
plt.savefig(output, dpi=150)
plt.show()
print(f"\nSaved to {output}")
