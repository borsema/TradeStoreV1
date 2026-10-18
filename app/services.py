from datetime import date, datetime
from app.database import get_connection
from app.schemas import TradeRequest

def parse_date(date_text):
    """Convert DD/MM/YYYY text into a Python date."""
    return datetime.strptime(date_text, "%d/%m/%Y").date()

def save_trade(trade: TradeRequest):
    # trade = TradeRequest
    """Validate and insert or update a trade."""
    today = date.today() #date(2026, 10, 16)  #date.today()
    maturity_date = parse_date(trade.maturity_date)
    created_date =parse_date(trade.created_date)

    #Reject Maturity Date earlier than today
    if maturity_date < today:
        raise ValueError("Maturity Date cannot be earlier than Today.")

    # Create date in future is not valid
    if created_date > today:
        raise ValueError("Created Date cannot be in the future.")

    # A trade that matures today is not yet expired.
    expired = 'Y' if maturity_date < today else 'N'

    connection = get_connection()

    try:
        existing_trade = connection.execute(
            "SELECT version FROM trades WHERE trade_id = ?",
            (trade.trade_id,)
        ).fetchone()

        if existing_trade is not None:
            existing_version = existing_trade["version"]

            if trade.version < existing_version:
                raise ValueError(
                    f"Incoming version {trade.version} is lower than existing version {existing_version}"
                )
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
            """,
            (
                trade.trade_id,
                trade.version,
                trade.counterparty_id,
                trade.portfolio_id,
                trade.maturity_date,
                trade.created_date,
                expired,
            )
        )
        connection.commit()
        saved_trade = connection.execute(
            "SELECT * FROM trades WHERE trade_id = ?",
        (trade.trade_id,)
        ).fetchone()
        print("Saved_trade", dict(saved_trade))
        return dict(saved_trade)
    finally:
        connection.close()

def expire_matured_trade():
    """Mark trade whose maturity date has passed or expired."""
    today = date.today() # date(2026,10,16) # date.today()
    connection = get_connection()

    try:
        rows = connection.execute(
            "SELECT trade_id, maturity_date, expired FROM trades"
        ).fetchall()

        expired_count = 0

        for row in rows:
            print(row)
            maturity_date = parse_date(row["maturity_date"])
            print("MAturity date", maturity_date)
            print("Todays date", today)
            if maturity_date < today and row["expired"] != "Y":
                connection.execute(
                    "UPDATE trades SET expired = 'Y' where trade_id = ?",
                    (row["trade_id"],   )
                )
                expired_count += 1

            connection.commit()

        return expired_count

    finally:
        connection.close()




