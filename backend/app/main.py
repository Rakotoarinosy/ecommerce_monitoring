from fastapi import FastAPI
from app.routes.payments import router as payment_router
from app.routes.logs import router as log_router
from app.routes.metrics import router as metrics_router
from app.migrations import setup_database
from app.routes.websockets import websocket_logs_endpoint, websocket_payments_endpoint

app = FastAPI(title="E-commerce & Monitoring API")

# Inclure les routes
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(log_router, prefix="/logs", tags=["Logs"])
app.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])

# Ajouter les WebSockets
app.add_websocket_route("/ws/payments", websocket_payments_endpoint)
app.add_websocket_route("/ws/logs", websocket_logs_endpoint)

setup_database()

@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API E-commerce & Monitoring"}
