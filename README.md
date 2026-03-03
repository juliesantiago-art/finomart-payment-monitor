# FinoMart Payment Method Health Monitor

A backend service that monitors **47 payment integrations across 6 Latin American markets** (MX, BR, CO, AR, CL, PE). It ingests transaction data, computes health metrics, surfaces actionable insights, and exposes everything via a REST API.

**Built with:** Python 3.12 + FastAPI (async), PostgreSQL, SQLAlchemy 2 (asyncpg), Docker Compose

---

## What Was Built

This service tracks payment method performance by ingesting raw transaction data and computing cost-benefit metrics, trend analysis, and automated insight detection. Champions like Visa MX and PIX BR are identified as high-ROI keepers, while zombies like Webpay CL (5 transactions/month against a $200/mo fixed fee) are flagged for removal. Hidden gems — high-approval methods under-promoted in checkout — are surfaced automatically. With more time, I'd add real-time FX rate fetching, a webhook system for alerting on declining trends, and a front-end dashboard with time-series charts.

---

## Setup & Run

### Prerequisites
- Docker + Docker Compose
- Python 3.11+ (for local scripts)

### Start with Docker Compose

```bash
git clone https://github.com/YOUR_USERNAME/finomart-payment-monitor
cd finomart-payment-monitor

# Set your API key (optional — defaults to dev key)
cp .env.example .env
# Edit .env if needed

docker-compose up --build
```

API will be available at `http://localhost:8000`.

### Explore the API (Swagger UI)

Open **http://localhost:8000/docs** — this is the primary way to explore and test all endpoints interactively. Click "Authorize" and enter your API key.

---

## Seed the Database

After `docker-compose up`, seed 400+ realistic transactions:

```bash
# From the project root
./scripts/seed_db.sh

# Or with custom URL and API key
./scripts/seed_db.sh http://localhost:8000 my-api-key
```

Or generate the data manually and POST directly:

```bash
python3 scripts/generate_test_data.py /tmp/data.json

# Seed reference data
curl -X POST http://localhost:8000/api/v1/admin/seed \
  -H "X-API-Key: dev-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d @/tmp/data.json

# Seed transactions (extract from data.json and POST)
```

---

## Currency Handling

All cost and revenue comparisons use **USD**. At ingest time:

1. `usd_amount = amount × FX_RATES[currency]` — static rates in `app/config.py`
2. `net_revenue_usd = usd_amount × margin_rate` — only for `approved` transactions

Static FX rates (in `app/config.py`):
| Currency | Rate (to USD) |
|----------|-------------|
| MXN | 0.058 |
| BRL | 0.200 |
| COP | 0.00024 |
| ARS | 0.00110 |
| CLP | 0.00107 |
| PEN | 0.267 |

The local `amount` field is retained for display purposes.

## Revenue vs TPV

Raw TPV (Total Payment Volume) overstates actual earnings. This service uses:

```
net_revenue_usd = usd_amount × margin_rate
```

Where `margin_rate` is configurable per payment method (default 2%, cards 2.5%, cash/voucher up to 3.5%). All ROI, insights, and cost-efficiency calculations use `net_revenue_usd`, not TPV.

---

## All Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | No | Health check |
| GET | `/docs` | No | Swagger UI (primary exploration) |
| POST | `/api/v1/transactions/ingest` | Yes | Bulk ingest JSON array |
| GET | `/api/v1/transactions` | Yes | Paginated list (`limit`/`offset`) |
| GET | `/api/v1/metrics` | Yes | Health metrics (filterable) |
| GET | `/api/v1/metrics/{id}` | Yes | Single method detail |
| GET | `/api/v1/insights` | Yes | Automated insights |
| GET | `/api/v1/trends` | Yes | Week-over-week trend analysis |
| GET | `/api/v1/roi` | Yes | Cost-benefit ROI per method |
| GET | `/api/v1/market-gaps` | Yes | Missing high-popularity methods |
| GET | `/api/v1/reports/html` | Yes | Full HTML report |
| GET | `/api/v1/reports/summary` | Yes | JSON portfolio summary |
| POST | `/api/v1/admin/seed` | Yes | Bulk seed reference data |

### Authentication

All protected endpoints require `X-API-Key` header:

```bash
curl -H "X-API-Key: dev-api-key-change-in-production" http://localhost:8000/api/v1/metrics
```

### Example Requests

```bash
# Metrics for Mexico
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/metrics?country=MX"

# All insights
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/insights"

# Zombie insights only
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/insights?insight_type=zombie"

# ROI sorted by worst performers first
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/roi?sort_by=recommendation"

# Trends for Brazil
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/trends?country=BR"

# Market gaps in Colombia
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/market-gaps?country=CO"

# Full HTML report (save to file)
curl -H "X-API-Key: dev-api-key-change-in-production" \
  "http://localhost:8000/api/v1/reports/html" > report.html
```

---

## Architecture & Key Design Decisions

- **Async throughout** — FastAPI + SQLAlchemy 2 async engine (asyncpg driver). All routes use `AsyncSession`.
- **USD normalization** — Static FX rates applied at ingest; `usd_amount` stored on every transaction for consistent cost comparisons.
- **Net revenue** — Margin-based `net_revenue_usd` stored at ingest (not re-computed on read).
- **API key auth** — `X-API-Key` header validated via FastAPI dependency; key set via `API_KEY` env var.
- **Global error handler** — All unhandled exceptions return `{"error": ..., "detail": ...}` JSON.
- **Testcontainers** — All tests use a real PostgreSQL container; no SQLite mocking.
- **Insight detection** — Runs on pre-computed metrics (no extra DB queries): zombie, hidden gem, performance alert, cost trap.
- **Trend analysis** — Core feature: weekly/monthly bucketing with DECLINING, GROWING, CHARGEBACK_SPIKE flags.

## Test Data Design

`scripts/generate_test_data.py` seeds 400+ transactions with deliberate profiles:

| Profile | Methods | Characteristics |
|---------|---------|----------------|
| Champion | Visa MX, Mastercard BR, MercadoPago AR | High volume (80-130 tx), ~80% approval |
| Hidden Gem | SPEI MX, PIX BR, PSE CO | Low volume (20-35 tx), ~85% approval, >5% revenue |
| Problem Child | OXXO MX, Boleto BR, Efecty CO | Medium volume (50-80 tx), ~45% approval |
| Zombie | Webpay CL, PagoEfectivo PE, Cupon AR | Very low volume (2-8 tx), has monthly fee |
| Average | 6 others | Medium volume (30-60 tx), ~65% approval |

---

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (requires Docker for testcontainers)
pytest --cov=app --cov-report=term-missing

# Run specific test files
pytest tests/test_metrics_engine.py -v
pytest tests/test_insight_detector.py -v
pytest tests/test_data_generator.py -v
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://finomart:finomart@localhost:5432/finomart` | Async PostgreSQL URL |
| `API_KEY` | `dev-api-key-change-in-production` | API authentication key |
