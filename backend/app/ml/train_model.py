import mlflow, mlflow.sklearn
import pandas as pd, joblib, os, logging
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_PATH   = os.path.join(BASE_DIR, "data/fraudTrain.csv")
MODEL_DIR   = os.path.join(BASE_DIR, "models")
MODEL_PATH  = os.path.join(MODEL_DIR, "isolation_forest_model.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
EXPERIMENT_NAME     = "ecommerce-anomaly-detection"
CONTAMINATION       = float(os.getenv("ML_CONTAMINATION", "0.01"))
N_ESTIMATORS        = int(os.getenv("ML_N_ESTIMATORS", "100"))
FEATURES            = ["amt", "unix_time"]

def train_and_log():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info(f"🚀 Démarrage pipeline — {datetime.now().isoformat()}")

    df = pd.read_csv(DATA_PATH)
    X  = df[FEATURES]
    logger.info(f"✅ {len(df)} lignes — features: {FEATURES}")

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    with mlflow.start_run(run_name=f"isolation-forest-{datetime.now().strftime('%Y%m%d-%H%M')}") as run:
        model = IsolationForest(contamination=CONTAMINATION, n_estimators=N_ESTIMATORS, random_state=42, n_jobs=-1)
        model.fit(X_scaled)
        logger.info("✅ Modèle entraîné")

        df["anomaly"] = model.predict(X_scaled)
        df["anomaly"] = df["anomaly"].map({1: 0, -1: 1})

        precision = precision_score(df["is_fraud"], df["anomaly"], zero_division=0)
        recall    = recall_score(df["is_fraud"],    df["anomaly"], zero_division=0)
        f1        = f1_score(df["is_fraud"],        df["anomaly"], zero_division=0)

        logger.info(f"\n{classification_report(df['is_fraud'], df['anomaly'])}")
        logger.info(f"🚨 Anomalies: {int(df['anomaly'].sum())} / {len(df)}")

        mlflow.log_params({"contamination": CONTAMINATION, "n_estimators": N_ESTIMATORS, "features": str(FEATURES), "dataset_size": len(df)})
        mlflow.log_metrics({"precision": round(float(precision),4), "recall": round(float(recall),4), "f1_score": round(float(f1),4), "anomaly_count": int(df["anomaly"].sum())})
        mlflow.sklearn.log_model(model, "isolation-forest-model", registered_model_name="IsolationForest-EcommerceAnomalyDetection")

        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        mlflow.log_artifact(MODEL_PATH, "models")
        mlflow.log_artifact(SCALER_PATH, "models")

        return {"run_id": run.info.run_id, "metrics": {"f1_score": round(float(f1),4), "anomaly_count": int(df["anomaly"].sum()), "dataset_size": len(df)}}

if __name__ == "__main__":
    r = train_and_log()
    print(f"✅ Run ID: {r['run_id']} | F1: {r['metrics']['f1_score']}")
