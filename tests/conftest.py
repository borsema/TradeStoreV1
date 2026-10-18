import os
from pathlib import Path

# Set the test database path before application modules are imported.
TEST_DB_PATH = Path(__file__).resolve().parent / "test_trades.db"
os.environ["TRADE_STORE_DB"] = str(TEST_DB_PATH)
