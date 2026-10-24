import pickle
from pathlib import Path

import numpy as np
import pandas as pd


# File paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEST_PATH = PROJECT_ROOT / "ml" / "synthetic_trades_test.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "relationship_model.pkl"


# 1. Load the saved model
with open(MODEL_PATH, "rb") as file:
    artifact = pickle.load(file)

model = artifact["model"]

counterparty_counts = artifact["counterparty_counts"]
portfolio_counts = artifact["portfolio_counts"]
pair_counts = artifact["pair_counts"]


# 2. Read test trades
df = pd.read_csv(TEST_PATH)


# 3. Build the same features used during training
features = pd.DataFrame({
    "counterparty_frequency": (
        df["counterparty_id"].map(counterparty_counts).fillna(0)
    ),
    "portfolio_frequency": (
        df["portfolio_id"].map(portfolio_counts).fillna(0)
    ),
    "pair_frequency": [
        pair_counts.get((cp, pf), 0)
        for cp, pf in zip(df["counterparty_id"], df["portfolio_id"])
    ],
})

features = np.log1p(features)

print("\nCheck unusual test trades:")

print(
    df[
        (df["counterparty_id"] == "CP020")
        & (df["portfolio_id"] == "PF010")
    ][["trade_id", "counterparty_id", "portfolio_id"]].head()
)

print(
    "Training frequency of CP020:",
    counterparty_counts.get("CP020", 0),
)

print(
    "Training frequency of PF010:",
    portfolio_counts.get("PF010", 0),
)

print(
    "Training frequency of CP020 + PF010:",
    pair_counts.get(("CP020", "PF010"), 0),
)

# 4. Predict whether each trade looks normal or unusual

predictions = model.predict(features)

# Flag trades with an unseen counterparty or unseen pair.
df["anomaly_status"] = [
    "UNUSUAL"
    if (
        prediction == -1
        or counterparty_counts.get(cp, 0) == 0
        or pair_counts.get((cp, pf), 0) == 0
    )
    else "NORMAL"
    for prediction, cp, pf in zip(
        predictions,
        df["counterparty_id"],
        df["portfolio_id"],
    )
]

# 5. Display results
print("\nAnomaly detection summary:")
print(df["anomaly_status"].value_counts())

print("\nSample unusual trades:")
print(
    df[df["anomaly_status"] == "UNUSUAL"][
        [
            "trade_id",
            "counterparty_id",
            "portfolio_id",
            "maturity_date",
            "anomaly_status",
        ]
    ].head(20)
)

######Evaluation


# 6. Evaluate model performance without actual labels

# Measure 1: Anomaly score distribution
# Lower decision_function scores indicate more unusual records.
df["anomaly_score"] = model.decision_function(features)

print("\n========== ANOMALY SCORE DISTRIBUTION ==========")

print(df["anomaly_score"].describe())

print("\nMost unusual trades according to the model:")

print(
    df.sort_values("anomaly_score")[
        [
            "trade_id",
            "counterparty_id",
            "portfolio_id",
            "anomaly_score",
        ]
    ].head(10)
)


# Measure 2: Detection rate / anomaly rate
# Isolation Forest returns -1 for unusual and 1 for normal.
anomaly_count = int((predictions == -1).sum())
normal_count = int((predictions == 1).sum())
total_count = len(predictions)

anomaly_rate = (
    anomaly_count / total_count * 100
    if total_count > 0
    else 0
)

print("\n========== DETECTION RATE ==========")
print("Total trades tested:", total_count)
print("Normal trades detected:", normal_count)
print("Unusual trades detected:", anomaly_count)
print(f"Anomaly rate: {anomaly_rate:.2f}%")
