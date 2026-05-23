"""
Service centralisé pour incrémenter les métriques Prometheus.
Importé dans payments.py, tasks.py, etc.
"""
from app.routes.metrics import (
    payments_total,
    payments_amount_total,
    anomalies_detected_total,
    logs_total,
    payments_pending_gauge,
    stripe_webhooks_total,
)


def record_payment(status: str, amount: float):
    """Enregistre un paiement dans Prometheus."""
    payments_total.labels(status=status).inc()
    payments_amount_total.labels(status=status).inc(amount)
    if status == "pending":
        payments_pending_gauge.inc()
    elif status in ("success", "failed"):
        payments_pending_gauge.dec()


def record_anomaly():
    """Enregistre une anomalie détectée par le modèle ML."""
    anomalies_detected_total.inc()


def record_log(level: str, service: str):
    """Enregistre un log dans Prometheus."""
    logs_total.labels(level=level.lower(), service=service).inc()


def record_stripe_webhook(event_type: str):
    """Enregistre un webhook Stripe reçu."""
    stripe_webhooks_total.labels(event_type=event_type).inc()
