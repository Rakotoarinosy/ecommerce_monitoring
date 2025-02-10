from fastapi import APIRouter, HTTPException
from app.models import Payment
from app.config import db

router = APIRouter()

# ✅ Route pour récupérer tous les paiements
@router.get("/")
def get_payments():
    payments = list(db.payments.find({}, {"_id": 0}))  # Exclure `_id`
    return {"payments": payments}

# ✅ Route pour créer un paiement (sans Stripe pour l'instant)
@router.post("/")
def create_payment(user_id: str, amount: float, status: str = "pending"):
    payment = Payment(user_id=user_id, amount=amount, status=status)
    payment.save()
    return {"message": "Paiement créé avec succès", "payment": payment.to_dict()}

# ✅ Route pour récupérer un paiement spécifique
@router.get("/{payment_id}")
def get_payment(payment_id: str):
    payment = db.payments.find_one({"_id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Paiement non trouvé")
    return payment
