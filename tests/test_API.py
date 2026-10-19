
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import create_tables, get_connection


@pytest.fixture
def client():
    """Prepare a clean test database and start the API."""
    create_tables()

    connection = get_connection()
    try:
        connection.execute("DELETE FROM trades")
        connection.commit()
    finally:
        connection.close()

    with TestClient(app) as test_client:
        yield test_client


def make_trade(
    trade_id="API001",
    version=1,
    maturity_date=None,
):
    """Build a valid trade request."""
    if maturity_date is None:
        maturity_date = (
            date.today() + timedelta(days=30)
        ).strftime("%d/%m/%Y")

    return {
        "trade_id": trade_id,
        "version": version,
        "counterparty_id": "CP001",
        "portfolio_id": "PF001",
        "maturity_date": maturity_date,
        "created_date": date.today().strftime("%d/%m/%Y"),
        "expired": "N",
    }


def test_create_and_get_trade(client):
    response = client.post(
        "/trades",
        json=make_trade(),
    )

    assert response.status_code == 200
    assert response.json()["trade_id"] == "API001"

    response = client.get("/trades/API001")

    assert response.status_code == 200
    assert response.json()["version"] == 1


def test_get_all_trades(client):
    client.post("/trades", json=make_trade("API001"))
    client.post("/trades", json=make_trade("API002"))

    response = client.get("/trades")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_missing_trade_returns_404(client):
    response = client.get("/trades/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["detail"] == "Trade not found"


def test_lower_version_returns_400(client):
    client.post(
        "/trades",
        json=make_trade(trade_id="API003", version=2),
    )

    response = client.post(
        "/trades",
        json=make_trade(trade_id="API003", version=1),
    )

    assert response.status_code == 400
    assert "lower than" in response.json()["detail"]


def test_invalid_date_format_returns_422(client):
    response = client.post(
        "/trades",
        json=make_trade(
            trade_id="API004",
            maturity_date="2026-12-31",
        ),
    )

    assert response.status_code == 422


def test_expiry_endpoint(client):
    past_date = (
        date.today() - timedelta(days=1)
    ).strftime("%d/%m/%Y")

    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO trades (
                trade_id, version, counterparty_id, portfolio_id,
                maturity_date, created_date, expired
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "API_EXPIRED",
                1,
                "CP001",
                "PF001",
                past_date,
                date.today().strftime("%d/%m/%Y"),
                "N",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    response = client.post("/trades/expire")

    assert response.status_code == 200
    assert response.json()["trades_marked_expired"] == 1

    connection = get_connection()
    try:
        trade = connection.execute(
            "SELECT expired FROM trades WHERE trade_id = ?",
            ("API_EXPIRED",),
        ).fetchone()
    finally:
        connection.close()

    assert trade["expired"] == "Y"
