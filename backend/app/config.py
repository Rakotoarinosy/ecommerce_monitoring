# backend/app/config.py
from pymongo import MongoClient
import redis
import json
import os
from dotenv import load_dotenv
import logging
from celery import Celery

load_dotenv()  # Charger les variables d'environnement

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ecommerce_db")
db = mongo_client[MONGO_DB_NAME]  # Base de données principale

# Configuration Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,  db=0, decode_responses=True)

# Configuration de Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Exemple d'utilisation dans une fonction
logger = logging.getLogger(__name__)

# ─── Passerelle de paiement : projets marchands ──────────────────────
# Plusieurs projets : GATEWAY_MERCHANTS (JSON), une entrée par projet :
#   [{"name": "BazarStore", "api_key": "...", "webhook_url": "https://…", "webhook_secret": "..."}]
# Un seul projet : les variables GATEWAY_* ci-dessous suffisent (rétrocompatible).
# Clés envoyées par le backend du projet (jamais par un frontend).
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "")
GATEWAY_MERCHANT_WEBHOOK_URL = os.getenv("GATEWAY_MERCHANT_WEBHOOK_URL", "")
GATEWAY_WEBHOOK_SECRET = os.getenv("GATEWAY_WEBHOOK_SECRET", "")
GATEWAY_MERCHANT_NAME = os.getenv("GATEWAY_MERCHANT_NAME", "BazarStore")


def _load_merchants() -> list[dict]:
    raw = os.getenv("GATEWAY_MERCHANTS", "").strip()
    if raw:
        merchants = json.loads(raw)
    elif GATEWAY_API_KEY:
        merchants = [{
            "name": GATEWAY_MERCHANT_NAME,
            "api_key": GATEWAY_API_KEY,
            "webhook_url": GATEWAY_MERCHANT_WEBHOOK_URL,
            "webhook_secret": GATEWAY_WEBHOOK_SECRET,
        }]
    else:
        merchants = []
    for merchant in merchants:
        if not merchant.get("name") or not merchant.get("api_key"):
            raise ValueError("GATEWAY_MERCHANTS : chaque projet doit avoir name et api_key")
    names = [m["name"] for m in merchants]
    if len(names) != len(set(names)) or "Monitoring" in names:
        raise ValueError("GATEWAY_MERCHANTS : noms en double ou réservé (Monitoring)")
    return merchants


GATEWAY_MERCHANTS = _load_merchants()
# stripe | simulator ; par défaut Stripe si une clé est configurée, sinon simulateur (local, CI).
GATEWAY_PROVIDER = os.getenv("GATEWAY_PROVIDER") or (
    "stripe" if os.getenv("STRIPE_SECRET_KEY") else "simulator"
)
# URL publique de cette API (page du simulateur vue par le navigateur du client).
GATEWAY_PUBLIC_URL = os.getenv("GATEWAY_PUBLIC_URL") or os.getenv("BASE_URL", "http://localhost:8011")
# Le modèle d'anomalies a été entraîné en USD : les montants MGA sont convertis avant prédiction.
MGA_PER_USD = float(os.getenv("MGA_PER_USD", "4500"))
