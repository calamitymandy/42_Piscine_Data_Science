import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
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


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} Train_knight.csv Test_knight.csv")
        sys.exit(1)

    test_file = sys.argv[2]

    # --- Load and standardize ---
    # KNN measures distances between knights, so features need to be on the same
    # scale — otherwise Power (up to 1260) would drown out Agility (up to 0.14)
    X_train, y_train = load_csv(TRAINING_FILE)
    X_val,   y_val   = load_csv(VALIDATION_FILE)

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_val_sc   = scaler.transform(X_val)

    # --- Try k from 1 to 30, record f1-score on validation set ---
    k_values = list(range(1, 31))
    f1_scores = []

    for k in k_values:
        knn = KNeighborsClassifier(n_neighbors=k)
        knn.fit(X_train_sc, y_train)
        y_pred = knn.predict(X_val_sc)
        f1 = f1_score(y_val, y_pred, average="weighted")
        f1_scores.append(f1)

    # --- Pick the best k ---
    best_k = k_values[f1_scores.index(max(f1_scores))]
    best_f1 = max(f1_scores)
    print(f"Best k: {best_k}  |  Validation f1-score: {best_f1:.4f}")
    if best_f1 < 0.92:
        print("WARNING: f1-score below 92% threshold!")
    else:
        print("f1-score >= 92% OK")

    # --- Train final model with best k on full training data ---
    X_test = load_test(test_file)
    X_test_sc = scaler.transform(X_test)

    knn_final = KNeighborsClassifier(n_neighbors=best_k)
    knn_final.fit(X_train_sc, y_train)
    predictions = knn_final.predict(X_test_sc)

    # Write KNN.txt
    output_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "KNN.txt")
    with open(output_path, "w") as f:
        for pred in predictions:
            f.write(pred + "\n")
    print(f"Predictions written to {output_path}")

    # --- Plot f1-score vs k ---
    plt.figure(figsize=(8, 5))
    plt.plot(k_values, f1_scores, color="steelblue")
    plt.xlabel("k values")
    plt.ylabel("accuracy")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
