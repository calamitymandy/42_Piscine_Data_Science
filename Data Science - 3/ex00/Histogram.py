import sys
import pandas as pd
import matplotlib.pyplot as plt

# ── Usage ─────────────────────────────────────────────────────────────────────
# python3 Histogram.py Train_knight.csv   → overlapping Jedi/Sith histograms
# python3 Histogram.py Test_knight.csv    → single "Knight" histogram per feature

if len(sys.argv) != 2:
    print("Usage: python3 Histogram.py <Train_knight.csv | Test_knight.csv>")
    sys.exit(1)

filename = sys.argv[1]
df = pd.read_csv("../../subject/" + filename)

# Features are all columns except 'knight' (if present)
features = [c for c in df.columns if c != "knight"]

# ── Layout: 6 rows × 5 columns ───────────────────────────────────────────────
fig, axes = plt.subplots(6, 5, figsize=(20, 18))
axes = axes.flatten()

if "knight" in df.columns:
    # Train file — overlapping histograms by class
    jedi = df[df["knight"] == "Jedi"]
    sith = df[df["knight"] == "Sith"]
    for i, feat in enumerate(features):
        ax = axes[i]
        ax.hist(jedi[feat], bins=20, alpha=0.6, color="steelblue", label="Jedi")
        ax.hist(sith[feat], bins=20, alpha=0.6, color="salmon",    label="Sith")
        ax.set_title(feat, fontsize=9)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6)
else:
    # Test file — single histogram, no labels
    for i, feat in enumerate(features):
        ax = axes[i]
        ax.hist(df[feat], bins=20, alpha=0.8, color="mediumseagreen", label="Knight")
        ax.set_title(feat, fontsize=9)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=6)

# Hide any unused subplots
for j in range(len(features), len(axes)):
    axes[j].set_visible(False)

plt.tight_layout()
output = filename.replace(".csv", "_histogram.png")
plt.savefig(output, dpi=150)
plt.show()
print(f"Saved to {output}")
