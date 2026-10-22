# Trade Store API (TSV1)

A RESTful API for managing financial trades, built with **FastAPI** and **SQLite**.

## Features

- Create or update trades (upsert by `trade_id`)
- Reject trades with a maturity date in the past
- Reject incoming versions lower than the stored version
- Mark matured trades as expired via a dedicated endpoint
- ML-based anomaly detection for unusual counterparty-portfolio relationships
- Anomaly review system to mark trades as SAFE or UNSAFE
- CI/CD pipeline with automated tests and Trivy security scan

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Database | SQLite3 |
| Validation | Pydantic v2 |
| ML | scikit-learn (Isolation Forest) |
| Data Processing | Pandas, NumPy |
| Server | Uvicorn / Gunicorn |
| Testing | Pytest + HTTPX |
| CI/CD | GitHub Actions |
| Deployment | Azure App Service |

## Project Structure

```
TradeStoreV1/
├── app/
│   ├── main.py        # FastAPI routes
│   ├── services.py    # Business logic
│   ├── schemas.py     # Pydantic request/response models
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

## Live Deployment

The API is deployed on **Azure App Service** (Malaysia West).

| | URL |
|---|---|
| Base URL | https://tsv1-bxcxcthgbadyc3ht.malaysiawest-01.azurewebsites.net |
| Interactive Docs | https://tsv1-bxcxcthgbadyc3ht.malaysiawest-01.azurewebsites.net/docs |

## API Endpoints

### Trade Management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/trades` | Create or update a trade |
| `GET` | `/trades` | List all trades |
| `GET` | `/trades/{trade_id}` | Get a trade by ID |
| `POST` | `/trades/expire` | Mark matured trades as expired |

### Anomaly Detection

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/anomalies` | Scan all trades for unusual patterns |
| `POST` | `/anomalies/{trade_id}/review` | Review and classify an anomaly |
| `GET` | `/anomalies/reviews` | Get all anomaly reviews |

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
