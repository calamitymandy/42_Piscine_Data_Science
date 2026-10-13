import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def load_data(filepath):
    """Load the CSV and encode the knight column as 0/1."""
    df = pd.read_csv(filepath)
    # Encode Jedi=0, Sith=1 so the knight column can be part of the correlation
    df["knight"] = df["knight"].map({"Jedi": 0, "Sith": 1})
    return df


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} Train_knight.csv")
        sys.exit(1)

    df = load_data(sys.argv[1])

    # Compute the Pearson correlation matrix across all columns
    corr = df.corr()

    # Plot
    fig, ax = plt.subplots(figsize=(14, 11))
    sns.heatmap(
        corr,
        ax=ax,
        cmap="Reds",
        vmin=-0.6,
        vmax=1.0,
        linewidths=0.3,
        linecolor="white",
    )
    ax.set_title("Correlation Coefficient Heatmap", fontsize=14, pad=12)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
