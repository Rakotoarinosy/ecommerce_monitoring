import json
import os
from fastapi import APIRouter, HTTPException, Request
import stripe
from app.models import Payment
from app.config import db
from app.services.payment_service import create_stripe_payment

router = APIRouter()
# 🔹 Configuration Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ✅ Route pour récupérer tous les paiements
@router.get("/")
def get_payments():
    payments = list(db.payments.find({}, {"_id": 0}))  # Exclure `_id`
    return {"payments": payments}

# ✅ Route pour initier un paiement avec Stripe
@router.post("/stripe")
def create_payment(user_id: str, amount: float):
    client_secret = create_stripe_payment(amount)
    if not client_secret:
        raise HTTPException(status_code=500, detail="Échec de création du paiement Stripe")

    # Sauvegarde en base avec `pending`
    payment = Payment(user_id=user_id, amount=amount, status="pending")
    payment.save()

    return {"message": "Paiement Stripe initié", "client_secret": client_secret, "payment": payment.to_dict()}

# ✅ Route pour récupérer un paiement spécifique
@router.get("/{payment_id}")
def get_payment(payment_id: str):
    payment = db.payments.find_one({"_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    return payment

# ✅ Route pour créer une session Stripe Checkout
@router.post("/checkout")
def create_checkout_session(user_id: str, amount: float):
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
            success_url=f"{BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/cancel",
        )

        # Sauvegarde en base avec `pending`
        payment = Payment(user_id=user_id, amount=amount, status="pending")
        payment.save()

        return {"checkout_url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Stripe: {str(e)}")
    
@router.get("/success")
async def payment_success(session_id: str):
    try:
        # Récupérer les détails de la session de paiement
        session = stripe.checkout.Session.retrieve(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session introuvable")

        # Vérifier si le paiement a été complété
        if session.payment_status == "paid":
            user_id = session.metadata.get("user_id")

            # Mettre à jour le statut du paiement en base de données
            payment = db.payments.find_one({"user_id": user_id, "status": "pending"})
            if payment:
                db.payments.update_one(
                    {"_id": payment["_id"]}, {"$set": {"status": "success"}}
                )

            return {"message": "Paiement réussi", "session_id": session_id}

        return {"message": "Paiement non complété", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="❌ STRIPE_WEBHOOK_SECRET non configuré")

    try:
        # ✅ Vérification de la signature Stripe
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="⚠️ Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="⚠️ Invalid signature")

    # 🎯 Gérer les événements Stripe
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")

        if user_id:
            # ✅ Mettre à jour la base de données avec `success`
            db.payments.update_one({"user_id": user_id}, {"$set": {"status": "success"}})
            print(f"✅ Paiement réussi pour user_id: {user_id}")
        else:
            print("⚠️ Aucun user_id trouvé dans la session.")

    return {"status": "success"}