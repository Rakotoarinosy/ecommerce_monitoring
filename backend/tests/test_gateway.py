import hashlib
import hmac
import json

AUTH = {"Authorization": "Bearer test-api-key"}
INTENT = {
    "merchant_reference": "order-1",
    "amount": 1_328_000,
    "currency": "MGA",
    "description": "Commande CMD-TEST1",
    "order_reference": "CMD-TEST1",
    "customer_name": "Rasoa Hanta",
    "customer_email": "hanta@example.com",
    "lines": [
        {"name": "Casque audio", "unit_amount": 700_000, "quantity": 1},
        {"name": "Baskets", "unit_amount": 314_000, "quantity": 2},
    ],
    "success_url": "http://shop.test/my-orders?order=order-1&payment=success",
    "cancel_url": "http://shop.test/my-orders?order=order-1&payment=cancelled",
}


def _create(client):
    response = client.post("/v1/payment-intents", json=INTENT, headers=AUTH)
    assert response.status_code == 201, response.text
    return response.json()


def test_requires_merchant_api_key(client):
    assert client.post("/v1/payment-intents", json=INTENT).status_code == 401
    bad = {"Authorization": "Bearer wrong"}
    assert client.post("/v1/payment-intents", json=INTENT, headers=bad).status_code == 401


def test_rejects_lines_that_do_not_match_amount(client):
    payload = {**INTENT, "amount": 1}
    assert client.post("/v1/payment-intents", json=payload, headers=AUTH).status_code == 422


def test_simulated_payment_succeeds_and_notifies_merchant(client, merchant_inbox):
    intent = _create(client)
    assert intent["status"] == "pending"
    assert intent["currency"] == "MGA"
    assert intent["checkout_url"] == f"http://gateway.test/v1/simulator/checkout/{intent['id']}"

    page = client.get(f"/v1/simulator/checkout/{intent['id']}")
    assert "1 328 000 Ar" in page.text

    paid = client.post(
        f"/v1/simulator/checkout/{intent['id']}", data={"action": "pay"}, follow_redirects=False
    )
    assert paid.status_code == 303
    assert paid.headers["location"] == INTENT["success_url"]

    state = client.get(f"/v1/payment-intents/{intent['id']}", headers=AUTH).json()
    assert state["status"] == "success"
    assert state["paid_at"]

    # Webhook signé reçu une seule fois, vérifiable avec le secret partagé.
    assert len(merchant_inbox) == 1
    headers, body = merchant_inbox[0]
    timestamp, signature = (part.split("=", 1)[1] for part in headers["X-Gateway-Signature"].split(","))
    expected = hmac.new(b"test-webhook-secret", f"{timestamp}.".encode() + body, hashlib.sha256)
    assert hmac.compare_digest(signature, expected.hexdigest())
    event = json.loads(body)
    assert event["type"] == "payment_intent.succeeded"
    assert event["data"]["merchant_reference"] == "order-1"

    # Une intention finalisée ne change plus (pas de second webhook).
    again = client.post(
        f"/v1/simulator/checkout/{intent['id']}", data={"action": "decline"}, follow_redirects=False
    )
    assert again.headers["location"] == INTENT["success_url"]
    assert len(merchant_inbox) == 1


def test_declined_payment_redirects_to_cancel_url(client, merchant_inbox):
    intent = _create(client)
    declined = client.post(
        f"/v1/simulator/checkout/{intent['id']}", data={"action": "decline"}, follow_redirects=False
    )
    assert declined.headers["location"] == INTENT["cancel_url"]
    assert client.get(f"/v1/payment-intents/{intent['id']}", headers=AUTH).json()["status"] == "failed"
    assert json.loads(merchant_inbox[0][1])["type"] == "payment_intent.failed"


def test_new_intent_cancels_previous_pending_one(client):
    first = _create(client)
    second = _create(client)
    assert client.get(f"/v1/payment-intents/{first['id']}", headers=AUTH).json()["status"] == "cancelled"
    assert client.get(f"/v1/payment-intents/{second['id']}", headers=AUTH).json()["status"] == "pending"


def test_dashboard_lists_gateway_payments_in_mga(client):
    _create(client)
    rows = client.get("/payments/recent").json()
    row = next(r for r in rows if r.get("source") == "BazarStore")
    assert row["currency"] == "MGA"
    assert (row["customer_name"], row["order_reference"]) == ("Rasoa Hanta", "CMD-TEST1")
    assert row["provider"] == "simulator"
    assert row["amount"] == 1_328_000
    assert row["prediction"] in {"normal", "anomalie 🚨"}
