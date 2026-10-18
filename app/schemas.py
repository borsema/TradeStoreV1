from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class TradeRequest(BaseModel):
    trade_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    counterparty_id: str = Field(min_length=1)
    portfolio_id: str = Field(min_length=1)
    maturity_date: str
    created_date: str
    expired: Literal["Y", "N"] = "N"

    @field_validator("maturity_date", "created_date")
    @classmethod
    def validate_date_format(cls, value: str) -> str:
        try:
            parsed_date = datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            raise ValueError("Date must be in DD/MM/YYYY format")

        return parsed_date.strftime("%d/%m/%Y")


class TradeResponse(TradeRequest):
    pass