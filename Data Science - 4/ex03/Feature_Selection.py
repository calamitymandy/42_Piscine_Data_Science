import sys
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def compute_vif(df):
    """
    Compute VIF and Tolerance for each feature in df.

    VIF for a feature = 1 / (1 - R²)
    where R² comes from regressing that feature against all the others.

    Tolerance = 1 / VIF  (= 1 - R²)

    A VIF > 5 means that feature is mostly explained by the others —
    it's redundant and adds noise rather than information.
    """
    vif_data = []
    cols = list(df.columns)
    for col in cols:
        y = df[col].values
        X = df.drop(columns=[col]).values
        r2 = LinearRegression().fit(X, y).score(X, y)
        vif = 1.0 / (1.0 - r2) if r2 < 1.0 else np.inf
        tolerance = 1.0 / vif if vif != np.inf else 0.0
        vif_data.append((col, vif, tolerance))
    return pd.DataFrame(vif_data, columns=["Feature", "VIF", "Tolerance"]).set_index("Feature")


def print_vif(vif_df):
    """Print VIF table sorted by VIF descending."""
    print(f"{'':20} {'VIF':>15} {'Tolerance':>12}")
    for feat, row in vif_df.sort_values("VIF", ascending=False).iterrows():
        print(f"{feat:<20} {row['VIF']:>15.6f} {row['Tolerance']:>12.6f}")


def remove_high_vif(df, threshold=5.0):
    """
    Iteratively remove the feature with the highest VIF until all are below threshold.
    Returns the filtered DataFrame.
    """
    features = df.copy()
    while True:
        vif_df = compute_vif(features)
        max_vif = vif_df["VIF"].max()
        if max_vif < threshold:
            break
        worst = vif_df["VIF"].idxmax()
        features = features.drop(columns=[worst])
    return features, vif_df


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} Train_knight.csv")
        sys.exit(1)

    df = pd.read_csv(sys.argv[1])
    features = df.drop(columns=["knight"])

    # Step 1 — show initial VIF for all features
    print("Initial VIF (all features):")
    print("-" * 50)
    vif_initial = compute_vif(features)
    print_vif(vif_initial)
    print()

    # Step 2 — iteratively drop highest-VIF feature until all < 5
    selected, vif_final = remove_high_vif(features, threshold=5.0)

    print("Selected features after VIF filtering (VIF < 5):")
    print("-" * 50)
    print_vif(vif_final)
    print()
    print(f"Kept {len(selected.columns)} features out of {len(features.columns)}:")
    print(list(selected.columns))


if __name__ == "__main__":
    main()
