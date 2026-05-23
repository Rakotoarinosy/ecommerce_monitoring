from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.payments import router as payment_router
from app.routes.logs import router as log_router
from app.routes.metrics import router as metrics_router
from app.routes.process_payment import router as process_payment_router
from app.migrations import setup_database
from app.routes.websockets import websocket_logs_endpoint, websocket_payments_endpoint
from app.middleware import PrometheusMiddleware

app = FastAPI(title="E-commerce & Monitoring API")

# ─── Middleware Prometheus (latence HTTP) ─────────────────────────────
app.add_middleware(PrometheusMiddleware)

# ─── Middleware CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(log_router, prefix="/logs", tags=["Logs"])
app.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])
app.include_router(process_payment_router, prefix="/api", tags=["Process payments"])

# ─── WebSockets ───────────────────────────────────────────────────────
app.add_websocket_route("/ws/payments", websocket_payments_endpoint)
app.add_websocket_route("/ws/logs", websocket_logs_endpoint)

setup_database()


@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API E-commerce & Monitoring"}
