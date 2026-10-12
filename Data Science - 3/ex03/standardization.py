import sys
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# ── Usage ─────────────────────────────────────────────────────────────────────
# python3 standardization.py Train_knight.csv
# python3 standardization.py Test_knight.csv

DATA_DIR = "../../subject/"

if len(sys.argv) != 2:
    print("Usage: python3 standardization.py <Train_knight.csv | Test_knight.csv>")
    sys.exit(1)

filename = sys.argv[1]
df = pd.read_csv(DATA_DIR + filename)

# Separate the features (skills) from the target column 'knight' (Jedi/Sith)
# We only standardize the feature columns, not the label
features = [c for c in df.columns if c != "knight"]
X = df[features]

# ── Print original data ───────────────────────────────────────────────────────
# Shows the raw values before any transformation
print(X.to_string(index=False))
print()

# ── What is standardization? ──────────────────────────────────────────────────
# The problem: features have very different scales.
#   - Stims goes from 50 to 250
#   - Deflection goes from 0.01 to 0.08
#
# If you feed this raw data to a machine learning algorithm that measures
# distances (like K-means or KNN), Stims will dominate just because its
# numbers are bigger — even if Deflection is more informative.
#
# Standardization fixes this by rescaling every feature so that:
#   - Its mean becomes 0  (the average value is now 0)
#   - Its std becomes 1   (values are measured in "how many std from average")
#
# Formula for each value:  z = (x - mean) / std
#
# After standardization, a Stims value of 100 becomes ~0, and 200 becomes ~1.
# All features are now on the same scale and can be fairly compared.
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=features)

# ── Print standardized data ───────────────────────────────────────────────────
# Values are now centered around 0, most between -3 and +3
print(X_scaled.to_string(index=False))

# ── Scatter plot with standardized data ──────────────────────────────────────
# We replot the separating scatter from ex02 (Empowered vs Stims)
# using the standardized values.
# The clusters should still be clearly separated — just re-centered around 0.
# This shows that standardization changes the scale but NOT the structure.
fig, ax = plt.subplots(figsize=(7, 6))

if "knight" in df.columns:
    # Train file: colour by Jedi / Sith
    jedi = X_scaled[df["knight"] == "Jedi"]
    sith = X_scaled[df["knight"] == "Sith"]
    ax.scatter(sith["Empowered"], sith["Stims"],
               label="Sith", color="salmon", alpha=0.5, s=30)
    ax.scatter(jedi["Empowered"], jedi["Stims"],
               label="Jedi", color="steelblue", alpha=0.5, s=30)
else:
    # Test file: no labels, single green color
    ax.scatter(X_scaled["Empowered"], X_scaled["Stims"],
               label="Knight", color="mediumseagreen", alpha=0.6, s=30)

ax.set_xlabel("Empowered (standardized)")
ax.set_ylabel("Stims (standardized)")
ax.legend()
plt.tight_layout()
output = filename.replace(".csv", "_standardized.png")
plt.savefig(output, dpi=150)
plt.show()
print(f"\nSaved to {output}")
