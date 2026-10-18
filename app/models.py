from dataclasses import dataclass


@dataclass
class Trade:
    trade_id: str
    version: int
    counterparty_id: str
    portfolio_id: str
    maturity_date: str
    created_date: str
    expired: str = "N"