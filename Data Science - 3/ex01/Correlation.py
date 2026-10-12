import pandas as pd

# ── Load training data ────────────────────────────────────────────────────────
# Train_knight.csv contains 30 knight skills (features) and a 'knight' column
# (target) that tells us whether the knight is a Jedi or a Sith.

df = pd.read_csv("../../subject/" + "Train_knight.csv")

# ── Encode the target column ──────────────────────────────────────────────────
# Pearson correlation only works with numeric values, so we convert the
# text labels into numbers:
#   Jedi → 1
#   Sith → 0
df["knight"] = df["knight"].map({"Jedi": 1, "Sith": 0})

# ── Compute Pearson correlation ───────────────────────────────────────────────
# df.corr() computes the correlation between every pair of columns.
# We only care about the correlation with the 'knight' column.
#
# Pearson correlation ranges from -1 to 1:
#   1  → perfect positive relationship (high feature value = Jedi)
#  -1  → perfect negative relationship (high feature value = Sith)
#   0  → no linear relationship
#
# We take the absolute value because we care about strength of the
# relationship, not direction. Then we sort from strongest to weakest.
corr = df.corr()["knight"].abs().sort_values(ascending=False)

# ── Print results ─────────────────────────────────────────────────────────────
# This shows which features are most useful for predicting Jedi vs Sith.
# Features at the top are the most discriminating — good candidates for
# a machine learning model.
print(corr.to_string())
