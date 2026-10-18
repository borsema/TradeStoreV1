
import pytest
from datetime import date, timedelta

from app.database import create_tables, get_connection
from app.schemas import TradeRequest
from app.services import save_trade, expire_matured_trade


from app.database import DATABASE_PATH
print("PYTEST DATABASE:", DATABASE_PATH)

@pytest.fixture(autouse=True)
def clean_database():
    """Prepare an empty trades table for each test."""
    create_tables()
    connection = get_connection()
    connection.execute("DELETE FROM trades")
    connection.commit()
    connection.close()


def make_trade(
    trade_id="TRD001",
    version=1,
    maturity_date=None,
    portfolio_id="PF001",
):
    if maturity_date is None:
        maturity_date = (date.today() + timedelta(days=30)).strftime(
            "%d/%m/%Y"
        )

    return TradeRequest(
        trade_id=trade_id,
        version=version,
        counterparty_id="CP001",
        portfolio_id=portfolio_id,
        maturity_date=maturity_date,
        created_date=date.today().strftime("%d/%m/%Y"),
    )


def test_create_new_trade():
    result = save_trade(make_trade())

    assert result["trade_id"] == "TRD001"
    assert result["version"] == 1
    assert result["expired"] == "N"


def test_reject_lower_version():
    save_trade(make_trade(version=2))

    with pytest.raises(ValueError, match="lower than"):
        save_trade(make_trade(version=1))


def test_same_version_updates_existing_trade():
    save_trade(make_trade(version=1, portfolio_id="PF001"))

    result = save_trade(make_trade(version=1, portfolio_id="PF002"))

    assert result["portfolio_id"] == "PF002"
    assert result["version"] == 1


def test_higher_version_updates_existing_trade():
    save_trade(make_trade(version=1))

    result = save_trade(make_trade(version=2, portfolio_id="PF003"))

    assert result["version"] == 2
    assert result["portfolio_id"] == "PF003"


def test_reject_past_maturity_date():
    past_date = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    with pytest.raises(ValueError, match="Maturity Date"):
        save_trade(make_trade(maturity_date=past_date))


def test_expire_matured_trades():
    # Insert a trade that matured yesterday.
    past_date = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    connection = get_connection()
    connection.execute(
        """
        INSERT INTO trades (
            trade_id, version, counterparty_id, portfolio_id,
            maturity_date, created_date, expired
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "TRD_EXPIRED",
            1,
            "CP001",
            "PF001",
            past_date,
            date.today().strftime("%d/%m/%Y"),
            "N",
        ),
    )
    connection.commit()
    connection.close()

    # Run the expiry process.
    count = expire_matured_trade()

    # Verify that the trade was marked as expired.
    connection = get_connection()
    trade = connection.execute(
        "SELECT expired FROM trades WHERE trade_id = ?",
        ("TRD_EXPIRED",),
    ).fetchone()
    connection.close()

    assert count == 1
    assert trade["expired"] == "Y"
