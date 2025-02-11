import stripe
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_stripe_payment(amount: float, currency="usd"):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe attend des centimes
            currency=currency
        )
        return payment_intent.client_secret
    except Exception as e:
        print(f"❌ Erreur Stripe: {e}")
        return None
