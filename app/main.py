from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from app.database import get_connection, create_tables
from app.schemas import TradeRequest, TradeResponse
from app.services import save_trade, expire_matured_trade

app = FastAPI(title='Trade Store API', version ="1.0.0")

# @app.on_event("startup")
@asynccontextmanager
def startup():
    create_tables()



@app.post("/trades",response_model = TradeResponse)
def create_or_update_trade(trade: TradeRequest):
    try:
        saved_trade = save_trade(trade)
        return saved_trade
    except ValueError as exc:
        raise HTTPException(status_code = 400, detail = str(exc))

@app.get("/trades/{trade_id}")
def get_trade(trade_id: str):
    connection = get_connection()
    try:
        trade = connection.execute(
            "SELECT * FROM trades WHERE trade_id = ?",
            (trade_id,)
        ).fetchone()
        if trade is None:
            raise HTTPException(
                status_code=404,
                detail="Trade not found"
            )
        return dict(trade)
    finally:
        connection.close()

@app.get("/trades")
def get_all_trades():
    connection = get_connection()
    try:
        trades = connection.execute(
            "SELECT * FROM trades ORDER BY trade_id"
        ).fetchall()
        return [dict(trade) for trade in trades]
    finally:
        connection.close()

@app.post("/trades/expire")
def expire_trade():
    count = expire_matured_trade()
    return {
        "message": "Expiry check completed",
        "trades_marked_expired": count
    }