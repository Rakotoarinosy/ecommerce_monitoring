"""API publique de la passerelle de paiement (/v1), utilisée par le backend BazarStore."""

import hmac
from html import escape
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, HttpUrl

from app.config import GATEWAY_API_KEY, GATEWAY_MERCHANT_NAME, logger
from app.routes.ml_model import predict_by_currency
from app.routes.websockets import notify_payment_clients
from app.services import gateway_service as gateway
from app.tasks import log_to_redis

router = APIRouter()


def require_merchant(authorization: str | None = Header(default=None)) -> None:
    if not GATEWAY_API_KEY:
        raise HTTPException(status_code=503, detail="Passerelle non configurée")
    if not authorization or not hmac.compare_digest(authorization, f"Bearer {GATEWAY_API_KEY}"):
        raise HTTPException(status_code=401, detail="Unauthorized")


class IntentLine(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    unit_amount: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1000)


class IntentIn(BaseModel):
    merchant_reference: str = Field(min_length=1, max_length=80)
    amount: int = Field(gt=0, le=1_000_000_000)
    currency: Literal["MGA"] = "MGA"
    description: str = Field(min_length=1, max_length=120)
    order_reference: str | None = Field(default=None, max_length=40)
    customer_name: str | None = Field(default=None, max_length=120)
    customer_email: str | None = Field(default=None, max_length=254)
    lines: list[IntentLine] = Field(default_factory=list, max_length=100)
    success_url: HttpUrl
    cancel_url: HttpUrl


async def _publish(intent: dict, background: BackgroundTasks) -> None:
    """Tableau de bord temps réel + journal + webhook marchand (en arrière-plan)."""
    # Même forme que /payments/recent : le tableau de bord met la ligne à jour par son id.
    await notify_payment_clients(predict_by_currency(gateway.dashboard_row(intent)))
    log_to_redis(f"Paiement {intent['id']} ({intent['source_order_id']}) : {intent['status']}", level="info")
    if intent["status"] in gateway.FINAL_STATUSES:
        background.add_task(gateway.deliver_webhook, intent)


@router.post("/payment-intents", status_code=201, dependencies=[Depends(require_merchant)])
async def create_payment_intent(payload: IntentIn, background: BackgroundTasks) -> dict:
    lines = [line.model_dump() for line in payload.lines]
    if lines and sum(line["unit_amount"] * line["quantity"] for line in lines) != payload.amount:
        raise HTTPException(status_code=422, detail="La somme des lignes ne correspond pas au montant")
    try:
        intent = gateway.create_intent(
            merchant_reference=payload.merchant_reference,
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            order_reference=payload.order_reference,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            lines=lines,
            success_url=str(payload.success_url),
            cancel_url=str(payload.cancel_url),
        )
    except gateway.ProviderError:
        raise HTTPException(status_code=502, detail="Fournisseur de paiement indisponible")
    await _publish(intent, background)
    return gateway.public_intent(intent)


@router.get("/payment-intents/{intent_id}", dependencies=[Depends(require_merchant)])
async def read_payment_intent(intent_id: str, background: BackgroundTasks) -> dict:
    intent = gateway.get_intent(intent_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Intention introuvable")
    try:
        refreshed = gateway.refresh_intent(intent)
    except gateway.ProviderError:
        raise HTTPException(status_code=502, detail="Fournisseur de paiement indisponible")
    if refreshed["status"] != intent["status"]:
        await _publish(refreshed, background)
    return gateway.public_intent(refreshed)


async def complete_from_stripe(intent_id: str, background: BackgroundTasks) -> None:
    """Appelé par le webhook Stripe existant (/payments/webhook) pour une session de la passerelle."""
    intent = gateway.get_intent(intent_id)
    if intent is None:
        logger.warning("Stripe webhook for unknown payment intent %s", intent_id)
        return
    updated = gateway.transition(intent, "success")
    if updated:
        await _publish(updated, background)


# ─── Simulateur (local, CI, démo) ────────────────────────────────────

SIMULATOR_PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paiement simulé · {merchant}</title>
<style>
 body{{font-family:system-ui,sans-serif;background:#f4f6fb;margin:0;display:grid;place-items:center;min-height:100vh;color:#1e293b}}
 main{{background:#fff;border-radius:16px;box-shadow:0 10px 30px #0f172a1a;padding:32px;max-width:420px;width:calc(100% - 32px)}}
 .badge{{display:inline-block;background:#fef3c7;color:#92400e;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:600}}
 .amount{{font-size:34px;font-weight:700;margin:16px 0 4px}}
 p{{color:#64748b;margin:0 0 20px}} form{{display:grid;gap:10px}}
 button{{border:0;border-radius:10px;padding:13px;font-size:15px;font-weight:600;cursor:pointer}}
 .pay{{background:#4f46e5;color:#fff}} .decline{{background:#fee2e2;color:#991b1b}} .cancel{{background:#e2e8f0;color:#334155}}
</style></head><body><main>
 <span class="badge">Mode simulateur — aucun débit réel</span>
 <div class="amount">{amount} Ar</div>
 <p>{merchant} · {description}</p>
 <form method="post">
  <button class="pay" name="action" value="pay">Payer {amount} Ar</button>
  <button class="decline" name="action" value="decline">Simuler un refus de carte</button>
  <button class="cancel" name="action" value="cancel">Annuler et revenir à la boutique</button>
 </form>
</main></body></html>"""


def _simulated_intent(intent_id: str) -> dict:
    intent = gateway.get_intent(intent_id)
    if intent is None or intent["provider"] != "simulator":
        raise HTTPException(status_code=404, detail="Intention introuvable")
    return intent


@router.get("/simulator/checkout/{intent_id}", response_class=HTMLResponse, include_in_schema=False)
def simulator_page(intent_id: str):
    intent = _simulated_intent(intent_id)
    if intent["status"] != "pending":
        return RedirectResponse(intent["success_url" if intent["status"] == "success" else "cancel_url"], 303)
    return SIMULATOR_PAGE.format(
        merchant=escape(GATEWAY_MERCHANT_NAME),
        description=escape(intent.get("description") or intent["user_id"]),
        amount=f"{intent['amount']:,}".replace(",", " "),
    )


@router.post("/simulator/checkout/{intent_id}", include_in_schema=False)
async def simulator_submit(intent_id: str, request: Request, background: BackgroundTasks):
    intent = _simulated_intent(intent_id)
    action = (await request.form()).get("action")
    status = {"pay": "success", "decline": "failed", "cancel": "cancelled"}.get(action)
    if status is None:
        raise HTTPException(status_code=422, detail="Action inconnue")
    updated = gateway.transition(intent, status)
    if updated:
        await _publish(updated, background)
    final = updated or gateway.get_intent(intent_id)
    return RedirectResponse(final["success_url" if final["status"] == "success" else "cancel_url"], 303)
