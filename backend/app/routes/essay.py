from datetime import datetime
import json
import os
from fastapi import APIRouter, HTTPException, Request
import stripe
from app.models import Payment
from app.config import db, redis_client, logger
from app.routes.websockets import notify_payment_clients

router = APIRouter()
# 🔹 Configuration Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8011")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.get("/success")
async def payment_success(session_id: str):
    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session introuvable")

        if session.payment_status == "paid":
            user_id = session.metadata.get("user_id")

            if not user_id:
                raise HTTPException(status_code=400, detail="user_id manquant dans les métadonnées")

            logger.info(f"Avant mise à jour - user_id: {user_id}, status: pending")
            result = db.payments.update_one(
                {"user_id": str(user_id), "status": "pending"},
                {"$set": {"status": "success"}}
            )
            logger.info(f"Après mise à jour - modified_count: {result.modified_count}")

            if result.modified_count > 0:
                logger.info(f"✅ Paiement mis à jour en succès pour user_id={user_id}")
            else:
                logger.warning(f"⚠️ Aucun paiement en pending trouvé pour user_id={user_id}")

            return {"message": "Paiement réussi", "session_id": session_id}

        return {"message": "Paiement non complété", "session_id": session_id}
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de la session Stripe : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")