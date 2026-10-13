import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def load_features(filepath):
    """Load CSV and return only the numeric feature columns (drop knight)."""
    df = pd.read_csv(filepath)
    features = df.drop(columns=["knight"])
    return features


def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} Train_knight.csv")
        sys.exit(1)

    # Load and standardize — PCA needs standardized data so that features
    # with big numbers (like Power=1000) don't dominate over small ones (like Agility=0.1)
    features = load_features(sys.argv[1])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)

    # Run PCA with all 30 components
    pca = PCA(n_components=features.shape[1])
    pca.fit(X_scaled)

    # Each component's contribution as a percentage of total variance
    variances_pct = pca.explained_variance_ratio_ * 100
    cumulative_pct = np.cumsum(variances_pct)

    # How many components to reach 90%
    n_for_90 = int(np.argmax(cumulative_pct >= 90)) + 1

    # Print results
    print("Variances (Percentage):")
    print(variances_pct)
    print()
    print("Cumulative Variances (Percentage):")
    print(cumulative_pct)
    print()
    print(f"Number of components needed to reach 90%: {n_for_90}")

    # Plot cumulative variance curve
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(cumulative_pct) + 1), cumulative_pct, color="steelblue")
    plt.xlabel("Number of components")
    plt.ylabel("Explained variance (%)")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
