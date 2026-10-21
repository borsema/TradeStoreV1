from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection
from app.anomaly_detector import detect_anomaly

router = APIRouter(prefix="/anomalies", tags=["Anomaly Detection"])


class AnomalyReviewRequest(BaseModel):
    version: int
    category: str = "UNSEEN_COUNTERPARTY"
    review_status: Literal["SAFE", "UNSAFE"]
    reason: str


@router.get("")
def get_trade_anomalies():
    connection = get_connection()
    try:
        trades = connection.execute(
            "SELECT * FROM trades ORDER BY trade_id"
        ).fetchall()

        anomalies = []

        for trade_row in trades:
            trade = dict(trade_row)
            result = detect_anomaly(trade)

            if result["anomaly_status"] != "UNUSUAL":
                continue

            review_row = connection.execute(
                """
                SELECT review_status, reason, reviewed_at
                FROM anomaly_reviews
                WHERE trade_id = ?
                  AND version = ?
                  AND category = ?
                """,
                (
                    trade["trade_id"],
                    trade["version"],
                    "UNSEEN_COUNTERPARTY"
                    if result["reason"] == "Counterparty not seen in training data"
                    else "UNSEEN_COUNTERPARTY"
                    if result["reason"] == "Counterparty-portfolio pair not seen in training data"
                    else "ISOLATION_FOREST"
                )
            ).fetchone()

            result["review_status"] = review_row["review_status"] if review_row else None
            result["review_reason"] = review_row["reason"] if review_row else None
            result["reviewed_at"] = review_row["reviewed_at"] if review_row else None

            anomalies.append(result)

        return {
            "total_trades_scanned": len(trades),
            "unusual_trades_count": len(anomalies),
            "anomalies": anomalies
        }

    finally:
        connection.close()


@router.post("/{trade_id}/review")
def review_anomaly(trade_id: str, review: AnomalyReviewRequest):
    connection = get_connection()
    try:
        trade = connection.execute(
            "SELECT version FROM trades WHERE trade_id = ?",
            (trade_id,)
        ).fetchone()

        if trade is None:
            raise HTTPException(status_code=404, detail="Trade not found")

        connection.execute(
            """
            INSERT INTO anomaly_reviews (
                trade_id, version, category, review_status, reason
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (trade_id, version, category)
            DO UPDATE SET
                review_status = excluded.review_status,
                reason = excluded.reason,
                reviewed_at = CURRENT_TIMESTAMP
            """,
            (trade_id, review.version, review.category, review.review_status, review.reason)
        )
        connection.commit()

        return {
            "trade_id": trade_id,
            "version": review.version,
            "category": review.category,
            "review_status": review.review_status,
            "reason": review.reason,
            "message": "Review saved successfully"
        }

    finally:
        connection.close()


@router.get("/reviews")
def get_anomaly_reviews():
    connection = get_connection()
    try:
        reviews = connection.execute(
            """
            SELECT trade_id, version, category, review_status, reason, reviewed_at
            FROM anomaly_reviews
            ORDER BY reviewed_at DESC
            """
        ).fetchall()

        return {
            "total_reviews": len(reviews),
            "reviews": [dict(review) for review in reviews]
        }

    finally:
        connection.close()
