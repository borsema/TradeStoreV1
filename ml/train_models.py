import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


# File paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAIN_PATH = PROJECT_ROOT / "ml" / "synthetic_trades_train.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "relationship_model.pkl"


# 1. Read training data
df = pd.read_csv(TRAIN_PATH)


# 2. Learn how often each relationship occurs
counterparty_counts = df["counterparty_id"].value_counts().to_dict()
portfolio_counts = df["portfolio_id"].value_counts().to_dict()
pair_counts = df.groupby(["counterparty_id", "portfolio_id"]).size().to_dict()


# 3. Convert each trade into numerical features
features = pd.DataFrame({
    "counterparty_frequency": df["counterparty_id"].map(counterparty_counts),
    "portfolio_frequency": df["portfolio_id"].map(portfolio_counts),
    "pair_frequency": [
        pair_counts.get((cp, pf), 0)
        for cp, pf in zip(df["counterparty_id"], df["portfolio_id"])
    ],
})

# Reduce the effect of large frequency values
features = np.log1p(features)


# 4. Train the anomaly detection model
model = IsolationForest(
    n_estimators=200,
    contamination=0.03,
    random_state=42,
)

model.fit(features)


# 5. Save the model and frequency maps for future predictions
artifact = {
    "model": model,
    "counterparty_counts": counterparty_counts,
    "portfolio_counts": portfolio_counts,
    "pair_counts": pair_counts,
}

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(MODEL_PATH, "wb") as file:
    pickle.dump(artifact, file)

print(f"Training completed using {len(df)} trades.")
print(f"Model saved to: {MODEL_PATH}")