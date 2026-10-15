import logging
from app.config import db

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    logger.info("🔹 Vérification et création de la base de données MongoDB...")

    # Vérifier si la collection payments existe
    collections = db.list_collection_names()
    if "payments" not in collections:
        logger.info("✅ Création de la collection 'payments' avec un document initial...")
        db.payments.insert_one({
            "user_id": "init_user",
            "amount": 0.0,
            "status": "init",
            "created_at": "2025-02-10T00:00:00Z"
        })

    # Passerelle : identifiant d'intention unique, recherche par commande marchande.
    db.payments.create_index(
        "id", unique=True, name="uniq_payment_intent_id",
        partialFilterExpression={"id": {"$type": "string"}},
    )
    db.payments.create_index([("source", 1), ("source_order_id", 1)], name="merchant_order")
    
    if "logs" not in collections:
        logger.info("✅ Création de la collection 'logs' avec un document initial...")
        db.logs.insert_one({
            "level": "INFO",
            "message": "Base de données initialisée",
            "service": "backend",
            "timestamp": "2025-02-10T00:00:00Z"
        })

    logger.info("✅ Base de données prête à être utilisée !")

if __name__ == "__main__":
    setup_database()
