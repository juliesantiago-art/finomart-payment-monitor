from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://finomart:finomart@localhost:5432/finomart"
    API_KEY: str = "dev-api-key-change-in-production"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Static FX rates (local currency → USD)
FX_RATES: dict[str, float] = {
    "MXN": 0.058,   # Mexican Peso
    "BRL": 0.200,   # Brazilian Real
    "COP": 0.00024, # Colombian Peso
    "ARS": 0.00110, # Argentine Peso
    "CLP": 0.00107, # Chilean Peso
    "PEN": 0.267,   # Peruvian Sol
    "USD": 1.0,
}

# Net revenue margin rates per payment method type (default 2%)
DEFAULT_MARGIN_RATE: float = 0.02

MARGIN_RATES: dict[str, float] = {
    # Cards
    "visa_mx": 0.025,
    "mastercard_mx": 0.025,
    "amex_mx": 0.030,
    "visa_br": 0.025,
    "mastercard_br": 0.025,
    "visa_co": 0.025,
    "mastercard_co": 0.025,
    # Wallets / digital
    "mercadopago_ar": 0.018,
    "mercadopago_mx": 0.018,
    "mercadopago_br": 0.018,
    # Bank transfers
    "spei_mx": 0.015,
    "pix_br": 0.015,
    "pse_co": 0.015,
    # Cash / voucher
    "oxxo_mx": 0.035,
    "boleto_br": 0.030,
    "efecty_co": 0.030,
    # Niche / local
    "webpay_cl": 0.022,
    "pagoefectivo_pe": 0.028,
    "cupon_ar": 0.020,
}

# Yuno catalog: payment methods available per country with popularity scores (1–10)
YUNO_CATALOG: dict[str, list[dict]] = {
    "MX": [
        {"id": "visa_mx", "name": "Visa", "type": "card", "popularity_score": 10},
        {"id": "mastercard_mx", "name": "Mastercard", "type": "card", "popularity_score": 10},
        {"id": "amex_mx", "name": "American Express", "type": "card", "popularity_score": 7},
        {"id": "spei_mx", "name": "SPEI", "type": "bank_transfer", "popularity_score": 9},
        {"id": "oxxo_mx", "name": "OXXO", "type": "cash", "popularity_score": 8},
        {"id": "mercadopago_mx", "name": "MercadoPago", "type": "wallet", "popularity_score": 8},
        {"id": "klarna_mx", "name": "Klarna", "type": "bnpl", "popularity_score": 7},
        {"id": "paypal_mx", "name": "PayPal", "type": "wallet", "popularity_score": 8},
    ],
    "BR": [
        {"id": "visa_br", "name": "Visa", "type": "card", "popularity_score": 10},
        {"id": "mastercard_br", "name": "Mastercard", "type": "card", "popularity_score": 10},
        {"id": "pix_br", "name": "PIX", "type": "bank_transfer", "popularity_score": 10},
        {"id": "boleto_br", "name": "Boleto", "type": "cash", "popularity_score": 8},
        {"id": "mercadopago_br", "name": "MercadoPago", "type": "wallet", "popularity_score": 7},
        {"id": "nubank_br", "name": "Nubank", "type": "wallet", "popularity_score": 9},
        {"id": "picpay_br", "name": "PicPay", "type": "wallet", "popularity_score": 7},
    ],
    "CO": [
        {"id": "visa_co", "name": "Visa", "type": "card", "popularity_score": 10},
        {"id": "mastercard_co", "name": "Mastercard", "type": "card", "popularity_score": 10},
        {"id": "pse_co", "name": "PSE", "type": "bank_transfer", "popularity_score": 9},
        {"id": "efecty_co", "name": "Efecty", "type": "cash", "popularity_score": 7},
        {"id": "nequi_co", "name": "Nequi", "type": "wallet", "popularity_score": 8},
        {"id": "daviplata_co", "name": "Daviplata", "type": "wallet", "popularity_score": 7},
    ],
    "AR": [
        {"id": "mercadopago_ar", "name": "MercadoPago", "type": "wallet", "popularity_score": 10},
        {"id": "visa_ar", "name": "Visa", "type": "card", "popularity_score": 9},
        {"id": "mastercard_ar", "name": "Mastercard", "type": "card", "popularity_score": 9},
        {"id": "cupon_ar", "name": "Cupon", "type": "cash", "popularity_score": 4},
        {"id": "naranja_ar", "name": "Naranja X", "type": "wallet", "popularity_score": 7},
        {"id": "modo_ar", "name": "MODO", "type": "wallet", "popularity_score": 7},
    ],
    "CL": [
        {"id": "webpay_cl", "name": "Webpay", "type": "card", "popularity_score": 10},
        {"id": "flow_cl", "name": "Flow", "type": "wallet", "popularity_score": 7},
        {"id": "mach_cl", "name": "MACH", "type": "wallet", "popularity_score": 8},
        {"id": "fpay_cl", "name": "Fpay", "type": "wallet", "popularity_score": 7},
    ],
    "PE": [
        {"id": "pagoefectivo_pe", "name": "PagoEfectivo", "type": "cash", "popularity_score": 6},
        {"id": "yape_pe", "name": "Yape", "type": "wallet", "popularity_score": 9},
        {"id": "plin_pe", "name": "Plin", "type": "wallet", "popularity_score": 8},
        {"id": "visa_pe", "name": "Visa", "type": "card", "popularity_score": 10},
        {"id": "mastercard_pe", "name": "Mastercard", "type": "card", "popularity_score": 10},
    ],
}
