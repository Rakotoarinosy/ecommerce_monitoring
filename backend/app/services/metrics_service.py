from app.routes.metrics import (
    payments_total,
    payments_amount_total,
    anomalies_detected_total,
    logs_total,
    payments_pending_gauge,
    stripe_webhooks_total,
)

def record_payment(status: str, amount: float):
    payments_total.labels(status=status).inc()
    payments_amount_total.labels(status=status).inc(amount)

def record_anomaly():
    anomalies_detected_total.inc()

def record_log(level: str, service: str):
    logs_total.labels(level=level.lower(), service=service).inc()

def record_stripe_webhook(event_type: str):
    stripe_webhooks_total.labels(event_type=event_type).inc()
