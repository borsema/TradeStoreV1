import pickle
from pathlib import Path

import numpy as np
import pandas as pd


# Locate the saved model
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = (
    PROJECT_ROOT / "ml" / "artifacts" / "relationship_model.pkl"
)


# Load the model and frequency maps once
with open(MODEL_PATH, "rb") as file:
    artifact = pickle.load(file)

model = artifact["model"]
counterparty_counts = artifact["counterparty_counts"]
portfolio_counts = artifact["portfolio_counts"]
pair_counts = artifact["pair_counts"]


def detect_anomaly(trade: dict) -> dict:
    """
    Check one trade for unusual counterparty-portfolio patterns.
    """

    counterparty_id = trade["counterparty_id"]
    portfolio_id = trade["portfolio_id"]

    # Build the same numerical features used during training.
    features = pd.DataFrame([{
        "counterparty_frequency": counterparty_counts.get(
            counterparty_id, 0
        ),
        "portfolio_frequency": portfolio_counts.get(
            portfolio_id, 0
        ),
        "pair_frequency": pair_counts.get(
            (counterparty_id, portfolio_id), 0
        ),
    }])
    print("features##",features)
    features = np.log1p(features)

    # Ask Isolation Forest to score the trade.
    prediction = model.predict(features)[0]

    # Apply the explicit unseen-relationship rule.
    unseen_counterparty = (
        counterparty_counts.get(counterparty_id, 0) == 0
    )
    unseen_portfolio = (portfolio_counts.get(portfolio_id, 0) == 0)

    unseen_pair = (
        pair_counts.get((counterparty_id, portfolio_id), 0) == 0
    )

    is_unusual = (
        prediction == -1
       or unseen_counterparty or unseen_portfolio
        or unseen_pair
    )
    print('trade',trade)
    print('features2',features)
    print('is_unusual',is_unusual)
    print('prediction',prediction)
    print('unseen_counterparty',unseen_counterparty)
    print('unseen_pair',unseen_pair)


    return {
        "trade_id": trade["trade_id"],
        "version": trade["version"],
        "counterparty_id": counterparty_id,
        "portfolio_id": portfolio_id,
        "anomaly_status": (
            "UNUSUAL" if is_unusual else "NORMAL"
        ),
        "reason": (
            "New counterparty detected"
            if unseen_counterparty
            else "New portfolio detected"
            if unseen_portfolio
            else "Counterparty-portfolio pair not seen in past"
            if unseen_pair
            else "Isolation Forest identified an unusual pattern"
            if prediction == -1
            else "No unusual relationship detected"
        ),
    }