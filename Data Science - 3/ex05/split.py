import sys
import pandas as pd
from sklearn.model_selection import train_test_split

# ── Usage ─────────────────────────────────────────────────────────────────────
# python3 split.py Train_knight.csv

if len(sys.argv) != 2:
    print("Usage: python3 split.py Train_knight.csv")
    sys.exit(1)

filename = sys.argv[1]

DATA_DIR = "../../subject/"
df = pd.read_csv(DATA_DIR + filename)

# ── Why 80/20? ────────────────────────────────────────────────────────────────
# We keep 80% of the data for training and 20% for validation.
#
# Training set (80%): the data the model learns from.
#   The more data you train on, the better the model can learn the patterns.
#
# Validation set (20%): data the model has NEVER seen during training.
#   We use it to check if the model actually learned something general,
#   or if it just memorized the training data (overfitting).
#   20% of ~400 rows = ~80 rows, which is enough to get a reliable estimate.
#
# random_state=42 makes the split reproducible — running the script twice
# gives the same split, which is important for comparing results.
# stratify=df["knight"] ensures both files have the same Jedi/Sith ratio
# as the original, so neither file ends up with all Jedi and no Sith.

TRAIN_RATIO = 0.8

training, validation = train_test_split(
    df,
    test_size=1 - TRAIN_RATIO,
    random_state=42,
    stratify=df["knight"]   # preserve Jedi/Sith ratio in both splits
)

# ── Save output files ─────────────────────────────────────────────────────────
training.to_csv("Training_knight.csv",   index=False)
validation.to_csv("Validation_knight.csv", index=False)

print(f"Original   : {len(df)} rows")
print(f"Training   : {len(training)} rows  ({len(training)/len(df)*100:.0f}%)  → Training_knight.csv")
print(f"Validation : {len(validation)} rows   ({len(validation)/len(df)*100:.0f}%)  → Validation_knight.csv")

# Verify the Jedi/Sith ratio is preserved in both splits
print(f"\nJedi/Sith ratio in original   : {df['knight'].value_counts().to_dict()}")
print(f"Jedi/Sith ratio in training   : {training['knight'].value_counts().to_dict()}")
print(f"Jedi/Sith ratio in validation : {validation['knight'].value_counts().to_dict()}")
