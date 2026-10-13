import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score

# Training/Validation files from DS3 ex05
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
    return pd.read_csv(filepath)


def draw_voting_diagram():
    """Display a diagram showing how the voting classifier works."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor("white")

    def box(x, y, w, h, text, color="#d0e8ff", fontsize=10):
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                              boxstyle="round,pad=0.1", linewidth=1.5,
                              edgecolor="black", facecolor=color)
        ax.add_patch(rect)
        ax.text(x, y, text, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color="black", lw=1.5))

    # Models
    box(2.5, 3.5, 2.0, 1.2, "Decision\nTree")
    box(5.0, 3.5, 2.2, 1.2, "Logistic\nRegression")
    box(7.5, 3.5, 2.0, 1.2, "KNN")

    # Voting classifier
    box(5.0, 6.5, 3.5, 1.2, "Voting Classifier", color="#fffacc")

    # Output
    box(5.0, 8.8, 1.0, 0.8, "1", color="white", fontsize=12)

    # New data point
    ax.plot(5.0, 1.5, "o", color="gray", markersize=12)
    ax.text(5.0, 1.0, "New data point", ha="center", va="center", fontsize=10)

    # Arrows: data point → models
    arrow(5.0, 1.5, 2.5, 2.9)
    arrow(5.0, 1.5, 5.0, 2.9)
    arrow(5.0, 1.5, 7.5, 2.9)

    # Vote labels
    for x, label in [(2.5, "1"), (5.0, "0"), (7.5, "1")]:
        ax.text(x, 5.1, label, ha="center", va="center",
                fontsize=12, fontweight="bold")
        arrow(x, 4.1, x, 5.9)
        arrow(x, 5.4, 5.0, 5.9)

    # Arrow: voting → output
    arrow(5.0, 7.1, 5.0, 8.4)

    # Predictions label
    ax.text(0.5, 6.5, "Predictions", ha="center", va="center",
            fontsize=11, fontweight="bold", color="darkred")
    ax.annotate("", xy=(2.0, 6.5), xytext=(1.2, 6.5),
                arrowprops=dict(arrowstyle="->", color="red", lw=2))

    ax.set_title("Voting Classifier", fontsize=13, fontweight="bold", pad=10)
    plt.tight_layout()
    plt.show()


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} Train_knight.csv Test_knight.csv")
        sys.exit(1)

    test_file = sys.argv[2]

    # --- Load data ---
    X_train, y_train = load_csv(TRAINING_FILE)
    X_val,   y_val   = load_csv(VALIDATION_FILE)

    # Standardize — needed for Logistic Regression and KNN
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_val_sc   = scaler.transform(X_val)

    # --- Build the three models ---
    dt  = DecisionTreeClassifier(random_state=42)
    lr  = LogisticRegression(max_iter=1000, random_state=42)
    knn = KNeighborsClassifier(n_neighbors=11)

    # --- Voting classifier (majority vote) ---
    voting = VotingClassifier(
        estimators=[("dt", dt), ("lr", lr), ("knn", knn)],
        voting="hard",
    )
    voting.fit(X_train_sc, y_train)

    # --- Validate ---
    y_pred_val = voting.predict(X_val_sc)
    f1 = f1_score(y_val, y_pred_val, average="weighted")
    print(f"Validation f1-score: {f1:.4f}")
    if f1 < 0.94:
        print("WARNING: f1-score below 94% threshold!")
    else:
        print("f1-score >= 94% OK")

    # --- Predict on test set ---
    X_test = load_test(test_file)
    X_test_sc = scaler.transform(X_test)
    predictions = voting.predict(X_test_sc)

    # Write Voting.txt
    output_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "Voting.txt")
    with open(output_path, "w") as f:
        for pred in predictions:
            f.write(pred + "\n")
    print(f"Predictions written to {output_path}")

    # --- Display voting diagram ---
    draw_voting_diagram()


if __name__ == "__main__":
    main()
