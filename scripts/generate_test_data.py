"""
Generate realistic test data for FinoMart Payment Monitor.
Produces 400+ transactions across 6 countries and 18 payment methods.
Outputs JSON to stdout or a file for use with POST /api/v1/transactions/ingest.
"""

import json
import random
import sys
from datetime import datetime, timedelta, timezone

# Seed for reproducibility
random.seed(42)

PAYMENT_METHODS = [
    # Champions: high volume, high approval
    {"id": "visa_mx", "name": "Visa", "type": "card", "country": "MX", "currency": "MXN",
     "profile": "champion", "monthly_fee": 150.0, "per_tx_fee": 0.10},
    {"id": "mastercard_br", "name": "Mastercard", "type": "card", "country": "BR", "currency": "BRL",
     "profile": "champion", "monthly_fee": 150.0, "per_tx_fee": 0.10},
    {"id": "mercadopago_ar", "name": "MercadoPago", "type": "wallet", "country": "AR", "currency": "ARS",
     "profile": "champion", "monthly_fee": 100.0, "per_tx_fee": 0.08},

    # Hidden Gems: high approval, decent revenue contribution, low tx volume
    {"id": "spei_mx", "name": "SPEI", "type": "bank_transfer", "country": "MX", "currency": "MXN",
     "profile": "hidden_gem", "monthly_fee": 50.0, "per_tx_fee": 0.05},
    {"id": "pix_br", "name": "PIX", "type": "bank_transfer", "country": "BR", "currency": "BRL",
     "profile": "hidden_gem", "monthly_fee": 50.0, "per_tx_fee": 0.05},
    {"id": "pse_co", "name": "PSE", "type": "bank_transfer", "country": "CO", "currency": "COP",
     "profile": "hidden_gem", "monthly_fee": 40.0, "per_tx_fee": 0.05},

    # Problem Children: decent volume, low approval
    {"id": "oxxo_mx", "name": "OXXO", "type": "cash", "country": "MX", "currency": "MXN",
     "profile": "problem_child", "monthly_fee": 80.0, "per_tx_fee": 0.12},
    {"id": "boleto_br", "name": "Boleto", "type": "cash", "country": "BR", "currency": "BRL",
     "profile": "problem_child", "monthly_fee": 80.0, "per_tx_fee": 0.12},
    {"id": "efecty_co", "name": "Efecty", "type": "cash", "country": "CO", "currency": "COP",
     "profile": "problem_child", "monthly_fee": 60.0, "per_tx_fee": 0.10},

    # Zombies: almost no activity, has monthly fee
    {"id": "webpay_cl", "name": "Webpay", "type": "card", "country": "CL", "currency": "CLP",
     "profile": "zombie", "monthly_fee": 200.0, "per_tx_fee": 0.15},
    {"id": "pagoefectivo_pe", "name": "PagoEfectivo", "type": "cash", "country": "PE", "currency": "PEN",
     "profile": "zombie", "monthly_fee": 120.0, "per_tx_fee": 0.10},
    {"id": "cupon_ar", "name": "Cupon", "type": "cash", "country": "AR", "currency": "ARS",
     "profile": "zombie", "monthly_fee": 80.0, "per_tx_fee": 0.08},

    # Average performers
    {"id": "mastercard_mx", "name": "Mastercard MX", "type": "card", "country": "MX", "currency": "MXN",
     "profile": "average", "monthly_fee": 120.0, "per_tx_fee": 0.10},
    {"id": "visa_br", "name": "Visa BR", "type": "card", "country": "BR", "currency": "BRL",
     "profile": "average", "monthly_fee": 120.0, "per_tx_fee": 0.10},
    {"id": "visa_co", "name": "Visa CO", "type": "card", "country": "CO", "currency": "COP",
     "profile": "average", "monthly_fee": 100.0, "per_tx_fee": 0.10},
    {"id": "mastercard_co", "name": "Mastercard CO", "type": "card", "country": "CO", "currency": "COP",
     "profile": "average", "monthly_fee": 100.0, "per_tx_fee": 0.10},
    {"id": "mercadopago_br", "name": "MercadoPago BR", "type": "wallet", "country": "BR", "currency": "BRL",
     "profile": "average", "monthly_fee": 90.0, "per_tx_fee": 0.08},
    {"id": "mercadopago_mx", "name": "MercadoPago MX", "type": "wallet", "country": "MX", "currency": "MXN",
     "profile": "average", "monthly_fee": 90.0, "per_tx_fee": 0.08},
]

# Amount ranges per currency (min, max)
AMOUNT_RANGES = {
    "MXN": (150, 5000),
    "BRL": (30, 800),
    "COP": (50000, 500000),
    "ARS": (500, 20000),
    "CLP": (5000, 100000),
    "PEN": (20, 400),
}

# Status distributions per profile
STATUS_DIST = {
    "champion":     {"approved": 0.80, "declined": 0.12, "pending": 0.05, "refunded": 0.03},
    "hidden_gem":   {"approved": 0.85, "declined": 0.08, "pending": 0.05, "refunded": 0.02},
    "problem_child": {"approved": 0.45, "declined": 0.40, "pending": 0.10, "refunded": 0.05},
    "zombie":       {"approved": 0.60, "declined": 0.25, "pending": 0.10, "refunded": 0.05},
    "average":      {"approved": 0.65, "declined": 0.20, "pending": 0.10, "refunded": 0.05},
}

# Volume per profile over 90 days
VOLUME = {
    "champion": (80, 130),
    "hidden_gem": (20, 35),
    "problem_child": (50, 80),
    "zombie": (2, 8),
    "average": (30, 60),
}

FX_RATES = {
    "MXN": 0.058, "BRL": 0.200, "COP": 0.00024,
    "ARS": 0.00110, "CLP": 0.00107, "PEN": 0.267, "USD": 1.0,
}

MARGIN_RATES = {
    "visa_mx": 0.025, "mastercard_mx": 0.025, "spei_mx": 0.015,
    "oxxo_mx": 0.035, "mercadopago_mx": 0.018,
    "mastercard_br": 0.025, "visa_br": 0.025, "pix_br": 0.015,
    "boleto_br": 0.030, "mercadopago_br": 0.018,
    "visa_co": 0.025, "mastercard_co": 0.025, "pse_co": 0.015, "efecty_co": 0.030,
    "mercadopago_ar": 0.018, "cupon_ar": 0.020,
    "webpay_cl": 0.022, "pagoefectivo_pe": 0.028,
}
DEFAULT_MARGIN = 0.02


def pick_status(profile: str) -> str:
    dist = STATUS_DIST[profile]
    r = random.random()
    cumulative = 0.0
    for status, prob in dist.items():
        cumulative += prob
        if r < cumulative:
            return status
    return "approved"


def random_datetime(days_ago_max: int = 90) -> datetime:
    # Weight towards weekdays and end of month (payday peaks)
    day_offset = random.randint(0, days_ago_max)
    base = datetime.now(timezone.utc) - timedelta(days=day_offset)
    hour = random.choices(range(24), weights=[
        1, 1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 6,
        6, 6, 6, 5, 5, 5, 5, 4, 4, 3, 2, 1
    ])[0]
    minute = random.randint(0, 59)
    return base.replace(hour=hour, minute=minute, second=random.randint(0, 59))


def generate_transactions() -> list[dict]:
    transactions = []

    for pm in PAYMENT_METHODS:
        profile = pm["profile"]
        vol_min, vol_max = VOLUME[profile]
        count = random.randint(vol_min, vol_max)

        amount_min, amount_max = AMOUNT_RANGES[pm["currency"]]

        for _ in range(count):
            status = pick_status(profile)
            amount = round(random.uniform(amount_min, amount_max), 2)
            created_at = random_datetime()

            # Chargeback only on approved
            chargeback = False
            if status == "approved" and random.random() < 0.02:
                chargeback = True

            # Settlement speed for bank transfers and cards
            settlement = None
            if status == "approved":
                if pm["type"] in ("card", "bank_transfer"):
                    settlement = random.randint(1, 5)
                elif pm["type"] == "wallet":
                    settlement = random.randint(1, 2)

            # FX spread for cross-currency
            fx_spread = None
            if pm["type"] == "card" and random.random() < 0.3:
                fx_spread = round(random.uniform(0.5, 3.5), 2)

            # Installments for cards
            installments = 1
            if pm["type"] == "card" and random.random() < 0.35:
                installments = random.randint(2, 12)

            transactions.append({
                "payment_method_id": pm["id"],
                "country": pm["country"],
                "amount": amount,
                "currency": pm["currency"],
                "status": status,
                "chargeback_flag": chargeback,
                "settlement_speed_days": settlement,
                "fx_spread_pct": fx_spread,
                "installment_count": installments,
                "created_at": created_at.isoformat(),
            })

    random.shuffle(transactions)
    return transactions


def generate_payment_methods() -> list[dict]:
    return [
        {
            "id": pm["id"],
            "name": pm["name"],
            "type": pm["type"],
            "country": pm["country"],
            "is_active": True,
        }
        for pm in PAYMENT_METHODS
    ]


def generate_integration_costs() -> list[dict]:
    from datetime import date
    costs = []
    for pm in PAYMENT_METHODS:
        costs.append({
            "payment_method_id": pm["id"],
            "monthly_fee_usd": pm["monthly_fee"],
            "per_transaction_fee_usd": pm["per_tx_fee"],
            "effective_from": date(2024, 1, 1).isoformat(),
        })
    return costs


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else None

    transactions = generate_transactions()
    payment_methods = generate_payment_methods()
    costs = generate_integration_costs()

    output = {
        "payment_methods": payment_methods,
        "integration_costs": costs,
        "transactions": transactions,
        "summary": {
            "total_transactions": len(transactions),
            "payment_methods": len(payment_methods),
            "countries": list({pm["country"] for pm in PAYMENT_METHODS}),
        },
    }

    if output_file:
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2, default=str)
        print(f"Generated {len(transactions)} transactions → {output_file}")
    else:
        print(json.dumps(output, indent=2, default=str))
