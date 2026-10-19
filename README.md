# Trade Store API (TSV1)

A RESTful API for managing financial trades, built with **FastAPI** and **SQLite**.

## Features

- Create or update trades (upsert by `trade_id`)
- Reject trades with a maturity date in the past
- Reject incoming versions lower than the stored version
- Mark matured trades as expired via a dedicated endpoint
- CI pipeline with automated tests and Trivy security scan

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Database | SQLite3 |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Testing | Pytest + HTTPX |
| CI | GitHub Actions |

## Project Structure

```
TradeStoreV1/
├── app/
│   ├── main.py        # FastAPI routes
│   ├── services.py    # Business logic
│   ├── schemas.py     # Pydantic request/response models
│   ├── models.py      # Trade dataclass
│   └── database.py    # SQLite connection & table setup
├── tests/
│   ├── test_trades.py # Unit tests (service layer)
│   ├── test_API.py    # Integration tests (API layer)
│   └── conftest.py
├── .github/workflows/ci.yml
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.12+

### Installation

```bash
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn app.main:app --reload
```

API will be available at `http://127.0.0.1:8000`.  
Interactive docs: `http://127.0.0.1:8000/docs`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/trades` | Create or update a trade |
| `GET` | `/trades` | List all trades |
| `GET` | `/trades/{trade_id}` | Get a trade by ID |
| `POST` | `/trades/expire` | Mark matured trades as expired |

### Trade Payload

```json
{
  "trade_id": "TRD001",
  "version": 1,
  "counterparty_id": "CP001",
  "portfolio_id": "PF001",
  "maturity_date": "31/12/2026",
  "created_date": "01/01/2025",
  "expired": "N"
}
```
## Business Rules

- **Maturity date** cannot be earlier than today.
- **Created date** cannot be in the future.
- **Version** of an incoming trade cannot be lower than the stored version for the same `trade_id`.
- The `/trades/expire` endpoint scans all trades and sets `expired = Y` for any trade whose maturity date has passed.

## Running Tests

```bash
pytest -v
```

Set a separate test database to avoid polluting the production database:

```bash
TRADE_STORE_DB=tests/test_trades.db pytest -v
```

## CI/CD

GitHub Actions runs on every push/PR to `main`:

1. **Automated Regression Tests** — installs dependencies and runs `pytest`.
2. **Dependency Vulnerability Scan** — runs Trivy to detect CRITICAL CVEs in the filesystem.
