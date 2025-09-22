# app/ml_model.py
import joblib
import pandas as pd
import os
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "isolation_forest_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "scaler.pkl")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# model = joblib.load("isolation_forest_model.pkl")
# scaler = joblib.load("scaler.pkl")

def predict_payment(payment: dict) -> dict:
    """
    Prend un seul paiement (dict) et ajoute 'prediction'
    ('normal' ou 'anomalie 🚨').
    """
    df = pd.DataFrame([payment])

    # Vérifier si 'amount' existe
    if "amount" not in df.columns:
        payment["prediction"] = "inconnu"
        return payment

    # Extraire unix_time depuis created_at ou Date
    if "created_at" in df.columns:
        try:
            df["unix_time"] = pd.to_datetime(df["created_at"]).astype("int64") // 10**9
        except Exception:
            df["unix_time"] = 0
    elif "Date" in df.columns:
        try:
            df["unix_time"] = pd.to_datetime(df["Date"]).astype("int64") // 10**9
        except Exception:
            df["unix_time"] = 0
    else:
        df["unix_time"] = 0

    # Features (amount + unix_time)
    df["amt"] = df["amount"] if "amount" in df else df["Montant"]
    X = df[["amt", "unix_time"]]

    # Normalisation et prédiction
    X_scaled = scaler.transform(X)
    prediction = model.predict(X_scaled)[0]

    payment["prediction"] = "normal" if prediction == 1 else "anomalie 🚨"
    return payment
