import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import plot_tree
from sklearn.metrics import f1_score


# Paths to the train/validation split from DS3 ex05
DS3_EX05 = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "Data Science - 3", "ex05"
)
TRAINING_FILE   = os.path.join(DS3_EX05, "Training_knight.csv")
VALIDATION_FILE = os.path.join(DS3_EX05, "Validation_knight.csv")


def load_csv(filepath):
    df = pd.read_csv(filepath)
    X = df.drop(columns=["knight"])
    y = df["knight"]
    return X, y


def load_test(filepath):
    """Test file has no knight column."""
    df = pd.read_csv(filepath)
    return df


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} Train_knight.csv Test_knight.csv")
        sys.exit(1)

    train_file = sys.argv[1]
    test_file  = sys.argv[2]

    # --- Load training and validation data from DS3 ex05 ---
    X_train, y_train = load_csv(TRAINING_FILE)
    X_val,   y_val   = load_csv(VALIDATION_FILE)

    # --- Train Random Forest ---
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # --- Validate and report f1-score ---
    y_pred_val = model.predict(X_val)
    f1 = f1_score(y_val, y_pred_val, average="weighted")
    print(f"Validation f1-score: {f1:.4f}")
    if f1 < 0.90:
        print("WARNING: f1-score below 90% threshold!")
    else:
        print("f1-score >= 90% OK")

    # --- Predict on Test_knight.csv ---
    X_test = load_test(test_file)
    predictions = model.predict(X_test)

    # Write Tree.txt — one prediction per line
    output_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Tree.txt")
    with open(output_path, "w") as f:
        for pred in predictions:
            f.write(pred + "\n")
    print(f"Predictions written to {output_path}")

    # --- Display one tree from the forest ---
    fig, ax = plt.subplots(figsize=(24, 10))
    plot_tree(
        model.estimators_[0],
        feature_names=X_train.columns.tolist(),
        class_names=model.classes_.tolist(),
        filled=True,
        rounded=True,
        ax=ax,
        fontsize=6,
    )
    ax.set_title("Decision tree trained on all Knights features", fontsize=14)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
