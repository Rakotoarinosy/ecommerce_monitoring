import pandas as pd
import joblib

# Charger modèle et scaler
model = joblib.load("isolation_forest_model.pkl")
scaler = joblib.load("scaler.pkl")

# Exemple de paiements récents (comme ton tableau)
data = [
    {"ID": "6898add4aba7ab9dff570eb3", "User_id": 123, "Montant": 55.00, "Status": "success", "Date": "2025-08-10 14:33"},
    {"ID": "687bc806fb4b8a9ae2adc1fd", "User_id": 123, "Montant": 55.00, "Status": "success", "Date": "2025-07-19 16:29"},
    {"ID": "67b98197c1d0b80e36ccbd39", "User_id": 123, "Montant": 55.00, "Status": "success", "Date": "2025-02-22 07:49"},
    {"ID": "67b8c60eb8737a3487433dcf", "User_id": 123, "Montant": 55.00, "Status": "success", "Date": "2025-02-21 18:29"},
    {"ID": "67b727deea336f09e844f027", "User_id": 123, "Montant": 55.00, "Status": "success", "Date": "2025-02-20 13:02"},
    {"ID": "68aaa123bbb456ccc789ddd0", "User_id": 123, "Montant": 5000.00, "Status": "success", "Date": "2025-08-10 14:35"},
]

# Convertir en DataFrame
df = pd.DataFrame(data)

# Ajouter un champ "unix_time" basé sur la Date
df["unix_time"] = pd.to_datetime(df["Date"]).astype("int64") // 10**9

# Ajouter la colonne Montant sous le nom attendu
df["amt"] = df["Montant"]

# Features utilisées pour la prédiction (ici amt + unix_time, car les autres infos ne sont pas dispo)
X = df[["amt", "unix_time"]]

# Normalisation
X_scaled = scaler.transform(X)

# Prédictions avec le modèle
df["anomaly"] = model.predict(X_scaled)

# Mapper les résultats en libellés
df["anomaly"] = df["anomaly"].map({1: "normal", -1: "anomalie"})

# Afficher le tableau enrichi
print(df[["ID", "User_id", "Montant", "Status", "Date", "anomaly"]])
