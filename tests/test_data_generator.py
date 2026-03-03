import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_test_data import generate_transactions, generate_payment_methods, PAYMENT_METHODS, VOLUME


def test_transaction_count_over_400():
    txns = generate_transactions()
    assert len(txns) >= 400, f"Expected >= 400 transactions, got {len(txns)}"


def test_all_6_countries_covered():
    txns = generate_transactions()
    countries = {t["country"] for t in txns}
    assert countries == {"MX", "BR", "CO", "AR", "CL", "PE"}


def test_zombie_profiles_have_under_10_tx():
    txns = generate_transactions()
    zombie_ids = {pm["id"] for pm in PAYMENT_METHODS if pm["profile"] == "zombie"}
    for zid in zombie_ids:
        count = sum(1 for t in txns if t["payment_method_id"] == zid)
        assert count < 10, f"Zombie {zid} has {count} transactions, expected < 10"


def test_champion_profiles_have_over_50_tx():
    txns = generate_transactions()
    champion_ids = {pm["id"] for pm in PAYMENT_METHODS if pm["profile"] == "champion"}
    for cid in champion_ids:
        count = sum(1 for t in txns if t["payment_method_id"] == cid)
        assert count > 50, f"Champion {cid} has {count} transactions, expected > 50"


def test_all_required_fields_present():
    txns = generate_transactions()
    required = {"payment_method_id", "country", "amount", "currency", "status", "created_at"}
    for tx in txns[:10]:  # Check first 10
        for field in required:
            assert field in tx, f"Missing field: {field}"


def test_status_distribution_reasonable():
    txns = generate_transactions()
    statuses = [t["status"] for t in txns]
    approved_pct = statuses.count("approved") / len(statuses)
    declined_pct = statuses.count("declined") / len(statuses)
    # Overall: expect 50-75% approved
    assert 0.45 <= approved_pct <= 0.80, f"Unexpected approval rate: {approved_pct:.1%}"
    assert declined_pct > 0.10, f"Too few declined: {declined_pct:.1%}"


def test_18_payment_methods():
    pms = generate_payment_methods()
    assert len(pms) == 18
