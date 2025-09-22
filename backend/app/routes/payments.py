from datetime import datetime
import json
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import stripe
from app.models import Payment
from app.config import db, redis_client, logger
from app.routes.websockets import notify_payment_clients
from app.tasks import log_to_redis  # Importer la fonction log_to_redis
from app.routes.ml_model import predict_payment


router = APIRouter()
# 🔹 Configuration Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
success_url_redirection = os.getenv("SUCCESS_URL_REDIRECTION")
cancel_url_redirection = os.getenv("CANCEL_URL_REDIRECTION")


# ✅ Route pour récupérer tous les paiements
@router.get("/")
def get_payments():
    payments = list(db.payments.find({}, {"_id": 0}))  # Exclure `_id`
    return {"payments": payments}


# def serialize_payment(payment):
#     # Assurez-vous que 'created_at' est un objet datetime, sinon il pourrait s'agir d'une chaîne ou null
#     created_at = payment.get("created_at")
    
#     if isinstance(created_at, datetime):
#         created_at_iso = created_at.isoformat()
#     elif isinstance(created_at, str):
#         try:
#             created_at_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")  # Adaptez le format si nécessaire
#             created_at_iso = created_at_obj.isoformat()
#         except ValueError:
#             created_at_iso = None  # Si la chaîne n'est pas dans le bon format, mettez la valeur à None
#     elif created_at is None:
#         created_at_iso = None  # Si 'created_at' est null, vous pouvez le définir sur None ou une valeur par défaut
#     else:
#         created_at_iso = None  # Pour tout autre type inattendu, définissez à None

#     # Vérifiez si l'ID existe et est valide
#     payment_id = payment.get("id")
#     if payment_id is None:
#         payment_id = str(payment.get("_id"))  # Essayez de récupérer l'_id si l'id n'est pas présent

#     return {
#         "id": str(payment_id),  # Assurez-vous que l'id est une chaîne valide
#         "user_id": payment.get("user_id"),
#         "amount": payment.get("amount"),
#         "status": payment.get("status"),
#         "created_at": created_at_iso,  # Vous pouvez définir une valeur par défaut ici si nécessaire
#     }

def serialize_payment(payment):
    created_at = payment.get("created_at")

    if isinstance(created_at, datetime):
        created_at_iso = created_at.isoformat()
    elif isinstance(created_at, str):
        try:
            created_at_obj = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            created_at_iso = created_at_obj.isoformat()
        except ValueError:
            created_at_iso = None
    else:
        created_at_iso = None

    payment_id = payment.get("id") or str(payment.get("_id"))

    payment_dict = {
        "id": str(payment_id),
        "user_id": payment.get("user_id"),
        "amount": payment.get("amount"),
        "status": payment.get("status"),
        "created_at": created_at_iso,
    }

    # 🔎 Ajouter la prédiction d’anomalie
    payment_with_prediction = predict_payment(payment_dict)

    print(f"Payment with prediction: {payment_with_prediction}")  # Debugging line
    return payment_with_prediction


@router.get("/recent")
async def get_recent_payments():
    payments = db.payments.find().sort("created_at", -1)
    serialized_payments = [serialize_payment(p) for p in payments]
    redis_client.setex("recent_payments", 600, json.dumps(serialized_payments))
    log_to_redis("Récupération des paiements récents réussie", level="info")  # Ajouter log à Redis
    return serialized_payments

# ✅ Route pour créer une session Stripe Checkout
@router.post("/checkout")
async def create_checkout_session(user_id: str, amount: float):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Paiement E-commerce",
                        },
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            metadata={"user_id": user_id},
            mode="payment",
            success_url=f"{BASE_URL}/payments/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{cancel_url_redirection}",
        )

        # Sauvegarde en base avec `pending`
        payment = Payment(user_id=user_id, amount=amount, status="pending")
        payment.save()

        logger.info(f"✅ Session Stripe créée pour user_id={user_id}, montant={amount}")
        log_to_redis(f"✅ Session Stripe créée pour user_id={user_id}, montant={amount}", level="info")  # Ajouter log à Redis

        # Notifier les clients via WebSocket
        await notify_payment_clients({
            "user_id": user_id,
            "amount": amount,
            "status": "pending",
        })

        return {"checkout_url": checkout_session.url}
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de la session Stripe : {e}")
        log_to_redis(f"❌ Erreur lors de la création de la session Stripe : {e}", level="error")  # Ajouter log à Redis
        raise HTTPException(status_code=500, detail=f"Erreur Stripe: {str(e)}")


# ✅ Route pour gérer la redirection après un paiement réussi
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

            logger.info(f"Recherche du document avec user_id={user_id} et status=pending")
            log_to_redis(f"Recherche du document avec user_id={user_id} et status=pending", level="info")  # Ajouter log à Redis
            document = db.payments.find_one(
                {"user_id": str(user_id), "status": "pending"},
                sort=[("created_at", -1)]  # Trier par la date la plus récente
            )
            logger.info(f"Document trouvé : {document}")
            log_to_redis(f"Document trouvé : {document}", level="info")  # Ajouter log à Redis

            if document:
                logger.info(f"Avant mise à jour - user_id: {user_id}, status: pending")
                result = db.payments.update_one(
                    {"_id": document["_id"]},  # Mettre à jour le paiement spécifique trouvé
                    {"$set": {"status": "success"}}
                )
                logger.info(f"Après mise à jour - modified_count: {result.modified_count}")
                log_to_redis(f"Après mise à jour - modified_count: {result.modified_count}", level="info")  # Ajouter log à Redis
                updated_document = db.payments.find_one({"_id": document["_id"]})
                logger.info(f"Document mis à jour : {updated_document}")
                log_to_redis(f"Document mis à jour : {updated_document}", level="info")  # Ajouter log à Redis

                if result.modified_count > 0:
                    logger.info(f"✅ Paiement mis à jour en succès pour user_id={user_id}")
                    log_to_redis(f"✅ Paiement mis à jour en succès pour user_id={user_id}", level="info")  # Ajouter log à Redis
                    
                    # 🔹 Notifier les clients WebSocket que le paiement est "success"
                    await notify_payment_clients({
                        "user_id": user_id,
                        "amount": document["amount"],
                        "status": "success",
                    })
                else:
                    logger.warning(f"⚠️ Aucun paiement en pending trouvé pour user_id={user_id}")
                    log_to_redis(f"⚠️ Aucun paiement en pending trouvé pour user_id={user_id}", level="warning")  # Ajouter log à Redis
            else:
                logger.warning(f"⚠️ Aucun document trouvé pour user_id={user_id} avec status=pending")
                log_to_redis(f"⚠️ Aucun document trouvé pour user_id={user_id} avec status=pending", level="warning")  # Ajouter log à Redis

            return RedirectResponse(url=success_url_redirection)

        return {"message": "Paiement non complété", "session_id": session_id}
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération de la session Stripe : {e}")
        log_to_redis(f"❌ Erreur lors de la récupération de la session Stripe : {e}", level="error")  # Ajouter log à Redis
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ✅ Route pour gérer les webhooks Stripe
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        logger.info(f"Webhook reçu de Stripe, type d'événement: {event['type']}")
        log_to_redis(f"Webhook reçu de Stripe, type d'événement: {event['type']}", level="info")  # Ajouter log à Redis
    except ValueError:
        logger.error("Payload Stripe invalide")
        log_to_redis("Payload Stripe invalide", level="error")  # Ajouter log à Redis
        raise HTTPException(status_code=400, detail="⚠️ Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Signature Stripe invalide")
        log_to_redis("Signature Stripe invalide", level="error")  # Ajouter log à Redis
        raise HTTPException(status_code=400, detail="⚠️ Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")

        if user_id:
            db.payments.update_one(
                {"user_id": str(user_id), "status": "pending"},
                {"$set": {"status": "success"}}
            )
            logger.info(f"✅ Paiement réussi pour user_id={user_id}")
            log_to_redis(f"✅ Paiement réussi pour user_id={user_id}", level="info")  # Ajouter log à Redis

            # Notifier les clients via WebSocket
            await notify_payment_clients({
                "user_id": user_id,
                "amount": session["amount_total"] / 100,
                "status": "success",
            })
        else:
            logger.warning("⚠️ Aucun user_id trouvé dans la session.")
            log_to_redis("⚠️ Aucun user_id trouvé dans la session.", level="warning")  # Ajouter log à Redis

    return {"status": "success"}