from fastapi import APIRouter
from prometheus_client import Counter, generate_latest

router = APIRouter()

# Compteurs pour les paiements réussis et échoués
payments_success = Counter("payments_success", "Nombre de paiements réussis")
payments_failed = Counter("payments_failed", "Nombre de paiements échoués")

@router.get("/metrics")
def metrics():
    return generate_latest()