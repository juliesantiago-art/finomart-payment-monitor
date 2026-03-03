#!/usr/bin/env bash
# Seed the database with test data.
# Usage: ./scripts/seed_db.sh [API_URL] [API_KEY]

set -e

API_URL="${1:-http://localhost:8000}"
API_KEY="${2:-${API_KEY:-dev-api-key-change-in-production}}"

echo "Generating test data..."
TMPFILE=$(mktemp /tmp/finomart_data_XXXXXX.json)
python3 scripts/generate_test_data.py "$TMPFILE"

echo "Seeding reference data (payment methods + costs)..."
python3 - <<PYEOF
import json, urllib.request, sys

with open("$TMPFILE") as f:
    data = json.load(f)

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "$API_KEY",
}

def post(path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request("$API_URL" + path, data=body, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.request.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode(), file=sys.stderr)
        sys.exit(1)

# Seed payment methods and costs
seed_payload = {
    "payment_methods": data["payment_methods"],
    "integration_costs": data["integration_costs"],
}
result = post("/api/v1/admin/seed", seed_payload)
print(f"  Payment methods seeded: {result['payment_methods_seeded']}")
print(f"  Integration costs seeded: {result['costs_seeded']}")

# Seed transactions in batches
txns = data["transactions"]
batch_size = 100
total_inserted = 0
for i in range(0, len(txns), batch_size):
    batch = txns[i:i+batch_size]
    result = post("/api/v1/transactions/ingest", batch)
    total_inserted += result["inserted"]
    print(f"  Batch {i//batch_size + 1}: inserted {result['inserted']} transactions ({total_inserted} total)")

print(f"\nDone! Seeded {total_inserted} transactions.")
PYEOF

rm -f "$TMPFILE"
echo "Database seeded successfully!"
