
from datetime import date, datetime

from app.database import get_connection
from app.schemas import TradeRequest


def parse_date(date_text: str) -> date:
    """Convert DD/MM/YYYY text into a Python date."""
    return datetime.strptime(date_text, "%d/%m/%Y").date()


def validate_trade(trade: TradeRequest, existing_version: None,) -> None:
    """Validate trade fields, dates, and version rules."""
    today = date.today()

    maturity_date = parse_date(trade.maturity_date)
    if maturity_date < today:
        raise ValueError(
            "VAL-001: Maturity Date cannot be earlier than Today."
        )

    created_date = parse_date(trade.created_date)
    if created_date > today:
        raise ValueError(
            "VAL-002: Created Date cannot be in the future."
        )

    if existing_version is not None and trade.version < existing_version:
        raise ValueError(
            f"VAL-003: Incoming version {trade.version} is lower "
            f"than existing version {existing_version}."
        )


def save_trade(trade: TradeRequest):
    """Validate and insert or update a trade."""

    connection = get_connection()

    try:
        # First, check whether this trade already exists.
        existing_trade = connection.execute(
            "SELECT version FROM trades WHERE trade_id = ?",
            (trade.trade_id,),
        ).fetchone()

        # Get the existing version, if available.
        existing_version = (existing_trade["version"] if existing_trade is not None else None )

        # Perform all business validations in one function.
        validate_trade(trade, existing_version)

        # A trade maturing today is not yet expired.
        maturity_date = parse_date(trade.maturity_date)
        expired = "Y" if maturity_date < date.today() else "N"

        # Insert a new trade or update an existing trade.
        connection.execute(
            """
            INSERT INTO trades (
                trade_id,
                version,
                counterparty_id,
                portfolio_id,
                maturity_date,
                created_date,
                expired
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trade_id) DO UPDATE SET
                version = excluded.version,
                counterparty_id = excluded.counterparty_id,
                portfolio_id = excluded.portfolio_id,
                maturity_date = excluded.maturity_date,
                created_date = excluded.created_date,
                expired = excluded.expired
            WHERE excluded.version >= trades.version
            """,
            (
                trade.trade_id,
                trade.version,
                trade.counterparty_id,
                trade.portfolio_id,
                trade.maturity_date,
                trade.created_date,
                expired,
            ),
        )

        connection.commit()

        saved_trade = connection.execute(
            "SELECT * FROM trades WHERE trade_id = ?",
            (trade.trade_id,),
        ).fetchone()

        return dict(saved_trade)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def expire_matured_trade():
    """Mark trades as expired when their maturity date has passed."""

    today = date.today()  #date(2026,10, 28)#
    connection = get_connection()

    try:
        rows = connection.execute(
            "SELECT trade_id, maturity_date FROM trades WHERE expired = 'N'"
        ).fetchall()

        expired_trade_ids = [
            row["trade_id"]
            for row in rows
            if parse_date(row["maturity_date"]) < today
        ]

        if expired_trade_ids:
            placeholders = ",".join("?" for _ in expired_trade_ids)

            connection.execute(
                f"""
                UPDATE trades
                SET expired = 'Y'
                WHERE expired = 'N'
                  AND trade_id IN ({placeholders})
                """,
                expired_trade_ids,
            )

        connection.commit()
        return len(expired_trade_ids)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def delete_trade(trade_id: str) -> bool:
    """Delete a trade by its ID."""

    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM trades WHERE trade_id = ?",
            (trade_id,),
        )
        connection.commit()
        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def store_trades_bulk(trades: list[TradeRequest]) -> dict:
    """Validate and save multiple trades, collecting individual errors."""

    stored = []
    errors = []

    for trade in trades:
        try:
            # save_trade performs validation and saving.
            save_trade(trade)
            stored.append(trade.trade_id)

        except (ValueError, Exception) as exc:
            errors.append({
                "trade_id": trade.trade_id,
                "error": str(exc),
            })

    return {
        "success_count": len(stored),
        "errors": errors,
    }
