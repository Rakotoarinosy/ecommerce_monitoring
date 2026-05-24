import os
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib

# 1. Charger le dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data/fraudTrain.csv")
df = pd.read_csv(DATA_PATH)

# 2. Sélectionner les colonnes numériques utiles
features = ["amt", "lat", "long", "city_pop", "unix_time", "merch_lat", "merch_long"]
X = df[features]

# 3. Normaliser les données (important pour Isolation Forest)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Créer et entraîner le modèle
model = IsolationForest(contamination=0.01, random_state=42)  # 1% d’anomalies attendues
model.fit(X_scaled)

# 5. Faire les prédictions (-1 = anomalie, 1 = normal)
df["anomaly"] = model.predict(X_scaled)

# Conversion : 1 = normal → 0, -1 = anomalie → 1
df["anomaly"] = df["anomaly"].map({1: 0, -1: 1})

# 6. Comparer avec la colonne réelle "is_fraud"
print(df[["amt", "merchant", "is_fraud", "anomaly"]].head(20))

# 7. Évaluer la performance du modèle
print("\n=== Rapport de classification ===")
print(classification_report(df["is_fraud"], df["anomaly"]))

# 8. Sauvegarder le modèle et le scaler
joblib.dump(model, "isolation_forest_model.pkl")
joblib.dump(scaler, "scaler.pkl")
print("\n✅ Modèle et scaler sauvegardés !")

# 9. Recharger le modèle plus tard
loaded_model = joblib.load("isolation_forest_model.pkl")
loaded_scaler = joblib.load("scaler.pkl")

# Exemple de prédiction avec le modèle rechargé
sample = X.iloc[:5]  # quelques transactions
sample_scaled = loaded_scaler.transform(sample)
pred = loaded_model.predict(sample_scaled)

# Conversion -1 / 1 en 0 / 1
pred = pd.Series(pred).map({1: 0, -1: 1})
print("\n🔎 Prédictions sur un échantillon :")
print(pred.tolist())

print(df[df["anomaly"] == 1].head(20))
print("Nombre d'anomalies détectées :", df["anomaly"].sum())
