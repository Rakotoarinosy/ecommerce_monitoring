
from fastapi import APIRouter, Response

from prometheus_client import (

    Counter, Histogram, Gauge,

    generate_latest, CONTENT_TYPE_LATEST

)

router = APIRouter()

payments_total = Counter(

    "ecommerce_payments_total",

    "Nombre total de paiements",

    ["status"]

)

payments_amount_total = Counter(

    "ecommerce_payments_amount_total",

    "Montant total des paiements en USD",

    ["status"]

)

anomalies_detected_total = Counter(

    "ecommerce_anomalies_detected_total",

    "Nombre total d anomalies detectees"

)

logs_total = Counter(

    "ecommerce_logs_total",

    "Nombre total de logs",

    ["level", "service"]

)

http_request_duration_seconds = Histogram(

    "ecommerce_http_request_duration_seconds",

    "Duree des requetes HTTP",

    ["method", "endpoint", "status_code"],

    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]

)

payments_pending_gauge = Gauge(

    "ecommerce_payments_pending",

    "Paiements en statut pending"

)

stripe_webhooks_total = Counter(

    "ecommerce_stripe_webhooks_total",

    "Webhooks Stripe recus",

    ["event_type"]

)

@router.get("/metrics")

def metrics():

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

