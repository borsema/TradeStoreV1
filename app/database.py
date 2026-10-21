import os
import sqlite3
from pathlib import Path

#Store the database at root of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# print(BASE_DIR)
DATABASE_PATH = os.getenv(
    "TRADE_STORE_DB",
    str(BASE_DIR/"trades.db")
)

def get_connection():
    """Create and return a connection to the SQLite3"""
    connection = sqlite3.connect(DATABASE_PATH, timeout = 30 )
    # connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection

def create_tables():
    """Create a trade table if it is not exist"""
    connection =get_connection()
    try:
        connection.execute("""
        CREATE TABLE IF NOT EXISTS trades(
        trade_id TEXT PRIMARY key,
        version INTEGER NOT NULL CHECK(version >= 1),
        counterparty_id TEXT NOT NULL,
        portfolio_id TEXT NOT NULL,
        maturity_date TEXT NOT NULL,
        created_date TEXT NOT NULL,
        expired TEXT NOT NULL DEFAULT 'N' CHECK (expired IN ('Y', 'N'))
        )
        """)

        connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_maturity
                ON trades (maturity_date)
            """)


        connection.execute("""
                    CREATE TABLE IF NOT EXISTS anomaly_reviews (
                        trade_id TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        review_status TEXT NOT NULL
                            CHECK (review_status IN ('SAFE', 'UNSAFE')),
                        reason TEXT NOT NULL,
                        reviewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (trade_id, version, category)
                    )
                """)

        connection.commit()
    finally:
        connection.close()