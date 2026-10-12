import sys
import pandas as pd
import matplotlib.pyplot as plt

# ── Usage ─────────────────────────────────────────────────────────────────────
# python3 points.py Train_knight.csv   → 2 scatter plots with Jedi/Sith colors
# python3 points.py Test_knight.csv    → 2 scatter plots with single green color

DATA_DIR = "../../subject/"

if len(sys.argv) != 2:
    print("Usage: python3 points.py <Train_knight.csv | Test_knight.csv>")
    sys.exit(1)

filename = sys.argv[1]
df = pd.read_csv(DATA_DIR + filename)

# ── Feature pairs ─────────────────────────────────────────────────────────────
# Separating pair: features with HIGH correlation to knight.
# Empowered and Stims are among the top correlators — Jedi and Sith clusters
# are clearly apart on these axes.
SEPARATING = ("Empowered", "Stims")

# Mixing pair: features with LOW correlation to knight.
# Pull and Deflection have near-zero correlation — Jedi and Sith overlap
# completely, making them useless for classification.
MIXING = ("Pull", "Deflection")

def plot_scatter(df, x_feat, y_feat, title, filename):
    """Plot a scatter coloured by knight class (or green if no labels)."""
    fig, ax = plt.subplots(figsize=(7, 6))

    if "knight" in df.columns:
        # Train file: colour by class
        for label, color in [("Sith", "salmon"), ("Jedi", "steelblue")]:
            subset = df[df["knight"] == label]
            ax.scatter(subset[x_feat], subset[y_feat],
                       label=label, color=color, alpha=0.5, s=30)
    else:
        # Test file: no labels, single green color
        ax.scatter(df[x_feat], df[y_feat],
                   label="Knight", color="mediumseagreen", alpha=0.6, s=30)

    ax.set_xlabel(x_feat)
    ax.set_ylabel(y_feat)
    ax.legend()
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.show()
    print(f"Saved to {filename}")

# ── Plot 1: separating features ───────────────────────────────────────────────
plot_scatter(df, *SEPARATING,
             title="Separating features",
             filename=f"points_separating_{filename.replace('.csv', '')}.png")

# ── Plot 2: mixing features ───────────────────────────────────────────────────
plot_scatter(df, *MIXING,
             title="Mixing features",
             filename=f"points_mixing_{filename.replace('.csv', '')}.png")
