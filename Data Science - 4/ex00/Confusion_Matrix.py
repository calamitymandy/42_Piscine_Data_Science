import sys
import matplotlib.pyplot as plt
import seaborn as sns


def load_labels(filepath):
    """Read one label per line from a file, stripping whitespace."""
    with open(filepath, "r") as f:
        labels = [line.strip() for line in f if line.strip()]
    return labels


def confusion_matrix(truth, predictions, classes):
    """
    Build a confusion matrix manually.
    Rows = actual class, Columns = predicted class.
    Entry [i][j] = number of samples with actual class i predicted as class j.
    """
    n = len(classes)
    idx = {c: i for i, c in enumerate(classes)}
    matrix = [[0] * n for _ in range(n)]
    for t, p in zip(truth, predictions):
        matrix[idx[t]][idx[p]] += 1
    return matrix


def compute_metrics(matrix, classes):
    """
    Compute precision, recall, f1-score, and total per class.
    All calculations done manually — no sklearn.

    For class i:
        TP = matrix[i][i]
        FP = sum of column i, excluding row i  (predicted as i but actually something else)
        FN = sum of row i, excluding column i  (actually i but predicted as something else)
        precision = TP / (TP + FP)
        recall    = TP / (TP + FN)
        f1        = 2 * precision * recall / (precision + recall)
        total     = sum of row i  (number of actual samples of class i)
    """
    n = len(classes)
    results = {}
    for i in range(n):
        tp = matrix[i][i]
        fp = sum(matrix[j][i] for j in range(n)) - tp   # col sum - TP
        fn = sum(matrix[i][j] for j in range(n)) - tp   # row sum - TP
        total = sum(matrix[i][j] for j in range(n))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)

        results[classes[i]] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "total": total,
        }
    return results


def compute_accuracy(matrix):
    """Accuracy = sum of diagonal / total samples."""
    correct = sum(matrix[i][i] for i in range(len(matrix)))
    total   = sum(matrix[i][j] for i in range(len(matrix))
                                for j in range(len(matrix[i])))
    return correct / total if total > 0 else 0.0, total


def print_report(metrics, accuracy, total, classes):
    """Print the classification report matching the subject's format."""
    print(f"{'':10} {'precision':>9} {'recall':>7} {'f1-score':>9} {'total':>7}")
    print()
    for cls in classes:
        m = metrics[cls]
        print(f"{cls:<10} {m['precision']:>9.2f} {m['recall']:>7.2f} "
              f"{m['f1']:>9.2f} {m['total']:>7}")
    print()
    print(f"{'accuracy':<10} {'':>9} {'':>7} {accuracy:>9.2f} {total:>7}")


def print_matrix(matrix):
    """Print the raw confusion matrix."""
    print()
    for row in matrix:
        print(row)


def plot_heatmap(matrix):
    """Display the confusion matrix as a seaborn heatmap."""
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="viridis",
    )
    plt.tight_layout()
    plt.show()


def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} predictions.txt truth.txt")
        sys.exit(1)

    predictions_file = sys.argv[1]
    truth_file       = sys.argv[2]

    predictions = load_labels(predictions_file)
    truth       = load_labels(truth_file)

    if len(predictions) != len(truth):
        print(f"Error: files have different number of entries "
              f"({len(predictions)} vs {len(truth)})")
        sys.exit(1)

    # Determine classes in consistent order (Jedi=0, Sith=1 matches subject)
    classes = sorted(set(truth) | set(predictions))

    matrix  = confusion_matrix(truth, predictions, classes)
    metrics = compute_metrics(matrix, classes)
    accuracy, total = compute_accuracy(matrix)

    print_report(metrics, accuracy, total, classes)
    print_matrix(matrix)
    plot_heatmap(matrix)


if __name__ == "__main__":
    main()
