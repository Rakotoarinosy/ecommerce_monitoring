import joblib, pandas as pd, os, logging
logger = logging.getLogger(__name__)

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR      = os.path.join(BASE_DIR, "ml", "models")
MODEL_PATH  = os.path.join(ML_DIR, "isolation_forest_model.pkl")
SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")

model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
logger.info("✅ Modèle chargé depuis fichier local")

def reload_model():
    global model, scaler
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    logger.info("🔄 Modèle rechargé")

def predict_payment(payment: dict) -> dict:
    if "amount" not in payment:
        payment["prediction"] = "inconnu"
        return payment
    try:
        unix_time = int(pd.to_datetime(payment.get("created_at")).timestamp()) if payment.get("created_at") else 0
    except Exception:
        unix_time = 0

    X = pd.DataFrame([{"amt": payment.get("amount", 0), "unix_time": unix_time}])
    X_scaled = scaler.transform(X)
    prediction = model.predict(X_scaled)[0]
    payment["prediction"] = "normal" if prediction == 1 else "anomalie 🚨"
    return payment
