from fastapi import FastAPI
from app.routes.payments import router as payment_router
# from app.routes.logs import router as log_router
from app.migrations import setup_database

app = FastAPI(title="E-commerce & Monitoring API")

# Inclure les routes
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
# app.include_router(log_router, prefix="/logs", tags=["Logs"])

setup_database()

@app.get("/")
def home():
    return {"message": "Bienvenue sur l'API E-commerce & Monitoring"}
