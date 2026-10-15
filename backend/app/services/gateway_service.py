"""Passerelle de paiement : intentions de paiement, fournisseurs et webhooks marchands.

Flux : le backend marchand crée une intention (montant en MGA) → le client paie sur
`checkout_url` (Stripe Checkout ou simulateur) → l'intention passe à `success`/`failed`/
`cancelled` → la passerelle notifie le marchand par un webhook signé HMAC-SHA256.
Le marchand peut aussi relire l'intention (GET) : le webhook n'est qu'une accélération.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone

import httpx
import stripe

from app.config import (
    GATEWAY_MERCHANTS,
    GATEWAY_PROVIDER,
    GATEWAY_PUBLIC_URL,
    db,
    logger,
)
from app.routes.metrics import gateway_intents_total, gateway_webhooks_total

FINAL_STATUSES = {"success", "failed", "cancelled"}
EVENT_TYPES = {
    "success": "payment_intent.succeeded",
    "failed": "payment_intent.failed",
    "cancelled": "payment_intent.cancelled",
}


class ProviderError(Exception):
    pass


def merchant_for_key(api_key: str) -> dict | None:
    """Projet correspondant à une clé API (comparaison à temps constant)."""
    found = None
    for merchant in GATEWAY_MERCHANTS:
        if hmac.compare_digest(api_key.encode(), merchant["api_key"].encode()):
            found = merchant
    return found


def merchant_named(name: str) -> dict | None:
    return next((m for m in GATEWAY_MERCHANTS if m["name"] == name), None)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def public_intent(intent: dict) -> dict:
    """Vue exposée au marchand (aucun champ interne Mongo)."""
    paid_at = intent.get("paid_at")
    created_at = intent.get("created_at")
    return {
        "id": intent["id"],
        "merchant_reference": intent["source_order_id"],
        "amount": intent["amount"],
        "currency": intent["currency"],
        "status": intent["status"],
        "provider": intent["provider"],
        "checkout_url": intent.get("checkout_url"),
        "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
        "paid_at": paid_at.isoformat() if isinstance(paid_at, datetime) else paid_at,
    }


def dashboard_row(intent: dict) -> dict:
    """Ligne du tableau de bord (WebSocket), alignée sur serialize_payment de /payments/recent."""
    created_at = intent.get("created_at")
    return {
        "id": intent["id"],
        "user_id": intent.get("user_id"),
        "amount": intent["amount"],
        "currency": intent["currency"],
        "status": intent["status"],
        "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
        "source": intent["source"],
        "provider": intent["provider"],
        "order_reference": intent.get("order_reference"),
        "customer_name": intent.get("customer_name"),
        "customer_email": intent.get("customer_email"),
    }


# ─── Fournisseurs ────────────────────────────────────────────────────


def _create_stripe_session(intent: dict, lines: list[dict]) -> tuple[str, str]:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            # L'ariary est une devise « zero-decimal » chez Stripe : montant envoyé tel quel.
            line_items=[
                {
                    "price_data": {
                        "currency": "mga",
                        "product_data": {"name": line["name"][:250]},
                        "unit_amount": line["unit_amount"],
                    },
                    "quantity": line["quantity"],
                }
                for line in lines
            ],
            client_reference_id=intent["id"],
            metadata={"payment_intent_id": intent["id"], "merchant_reference": intent["source_order_id"]},
            success_url=intent["success_url"],
            cancel_url=intent["cancel_url"],
            # E-mail pré-rempli sur la page Stripe (reçu de paiement envoyé par Stripe).
            **({"customer_email": intent["customer_email"]} if intent.get("customer_email") else {}),
        )
    except stripe.error.StripeError as exc:
        logger.warning("Stripe checkout creation failed: %s", exc)
        raise ProviderError() from exc
    return session.id, session.url


def _stripe_status(session_id: str) -> str | None:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as exc:
        logger.warning("Stripe session lookup failed: %s", exc)
        raise ProviderError() from exc
    if session.payment_status == "paid":
        return "success"
    if session.status == "expired":
        return "failed"
    return None


# ─── Intentions ──────────────────────────────────────────────────────


def create_intent(
    *,
    merchant: str,
    merchant_reference: str,
    amount: int,
    currency: str,
    description: str,
    lines: list[dict],
    order_reference: str | None = None,
    customer_name: str | None = None,
    customer_email: str | None = None,
    success_url: str,
    cancel_url: str,
) -> dict:
    now = _now()
    intent_id = f"pi_{secrets.token_hex(12)}"
    # Une relance clôt l'intention précédente de la même commande (une seule payable à la fois).
    db.payments.update_many(
        {"source": merchant, "source_order_id": merchant_reference, "status": "pending"},
        {"$set": {"status": "cancelled", "updated_at": now}},
    )
    intent = {
        "id": intent_id,
        "source": merchant,
        "source_order_id": merchant_reference,
        # Colonne historique « Utilisateur » : nom du client, sinon le libellé de la commande.
        "user_id": customer_name or description,
        "description": description,
        "order_reference": order_reference,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "amount": amount,
        "currency": currency,
        "status": "pending",
        "provider": GATEWAY_PROVIDER,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "created_at": now,
        "updated_at": now,
    }
    lines = lines or [{"name": description, "unit_amount": amount, "quantity": 1}]
    if GATEWAY_PROVIDER == "stripe":
        intent["provider_session_id"], intent["checkout_url"] = _create_stripe_session(intent, lines)
    else:
        intent["checkout_url"] = f"{GATEWAY_PUBLIC_URL.rstrip('/')}/v1/simulator/checkout/{intent_id}"
    db.payments.insert_one(intent)
    gateway_intents_total.labels(status="pending", provider=intent["provider"]).inc()
    logger.info("Payment intent %s created for %s (%s %s)", intent_id, merchant_reference, amount, currency)
    return intent


def get_intent(intent_id: str, merchant: str | None = None) -> dict | None:
    """Intention de la passerelle ; avec `merchant`, seulement si elle appartient à ce projet."""
    query = {"id": intent_id, "source_order_id": {"$exists": True}}
    if merchant is not None:
        query["source"] = merchant
    return db.payments.find_one(query, {"_id": 0})


def refresh_intent(intent: dict) -> dict:
    """Relit le fournisseur pour une intention encore en attente (filet si le webhook manque)."""
    if intent["status"] != "pending" or intent["provider"] != "stripe":
        return intent
    status = _stripe_status(intent["provider_session_id"])
    if status:
        return transition(intent, status) or intent
    return intent


def transition(intent: dict, status: str) -> dict | None:
    """pending → état final, une seule fois (écriture conditionnelle : pas de double webhook)."""
    now = _now()
    changes = {"status": status, "updated_at": now}
    if status == "success":
        changes["paid_at"] = now
    updated = db.payments.find_one_and_update(
        {"id": intent["id"], "status": "pending"},
        {"$set": changes},
        projection={"_id": 0},
        return_document=True,
    )
    if updated is None:
        return None
    gateway_intents_total.labels(status=status, provider=updated["provider"]).inc()
    logger.info("Payment intent %s → %s", updated["id"], status)
    return updated


# ─── Webhooks marchands ──────────────────────────────────────────────


def sign(body: bytes, secret: str, timestamp: int | None = None) -> str:
    """En-tête `X-Gateway-Signature: t=<unix>,v1=<hmac_sha256(secret, "<t>.<body>")>`."""
    timestamp = int(time.time()) if timestamp is None else timestamp
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256)
    return f"t={timestamp},v1={digest.hexdigest()}"


def build_event(intent: dict) -> bytes:
    event = {
        "id": f"evt_{secrets.token_hex(12)}",
        "type": EVENT_TYPES[intent["status"]],
        "created": int(time.time()),
        "data": public_intent(intent),
    }
    return json.dumps(event, separators=(",", ":")).encode()


def deliver_webhook(intent: dict, attempts: int = 3) -> bool:
    """Envoi best-effort (tâche de fond) ; le marchand relit de toute façon l'intention."""
    merchant = merchant_named(intent["source"]) or {}
    url, secret = merchant.get("webhook_url"), merchant.get("webhook_secret")
    if not url or not secret:
        return False
    body = build_event(intent)
    for attempt in range(1, attempts + 1):
        try:
            response = httpx.post(
                url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Gateway-Signature": sign(body, secret),
                },
                timeout=5.0,
            )
            response.raise_for_status()
            gateway_webhooks_total.labels(result="delivered").inc()
            return True
        except httpx.HTTPError as exc:
            logger.warning("Webhook for %s failed (attempt %s): %s", intent["id"], attempt, exc)
            time.sleep(attempt)
    gateway_webhooks_total.labels(result="failed").inc()
    return False
