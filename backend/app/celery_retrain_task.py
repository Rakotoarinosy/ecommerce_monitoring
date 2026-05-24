"""
Tâche Celery — Réentraînement automatique du modèle MLOps
À ajouter dans backend/app/tasks.py
"""

# ════════════════════════════════════════════════════════════════════
# AJOUTER CES IMPORTS EN HAUT DE tasks.py
# ════════════════════════════════════════════════════════════════════
# import sys
# import os
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ml"))

# ════════════════════════════════════════════════════════════════════
# AJOUTER CETTE TÂCHE DANS tasks.py
# ════════════════════════════════════════════════════════════════════

@celery.task(name="app.tasks.retrain_model")
def retrain_model():
    """
    Réentraîne le modèle Isolation Forest avec les données récentes.
    Logge dans MLflow et recharge le modèle en production.
    """
    try:
        logger.info("🤖 Début du réentraînement MLOps")
        log_to_redis("🤖 Réentraînement du modèle ML démarré", level="info")

        # Lancer le pipeline d'entraînement
        import sys
        sys.path.insert(0, "/app/app/ml")
        from train_model import train_and_log

        result = train_and_log()

        run_id  = result["run_id"]
        metrics = result["metrics"]

        logger.info(f"✅ Réentraînement terminé — Run ID: {run_id}")
        logger.info(f"📈 F1-Score: {metrics['f1_score']}")

        # Recharger le modèle dans l'API
        from app.routes.ml_model import reload_model
        reload_model()

        log_to_redis(
            f"✅ Modèle réentraîné — F1={metrics['f1_score']} — "
            f"Anomalies={metrics['anomaly_count']}/{metrics['dataset_size']}",
            level="info"
        )

        # Exposer dans Prometheus
        try:
            from prometheus_client import Gauge
            Gauge("ml_last_retrain_f1",        "F1 du dernier réentraînement").set(metrics["f1_score"])
            Gauge("ml_last_retrain_anomalies", "Anomalies du dernier run").set(metrics["anomaly_count"])
        except Exception:
            pass

        return {
            "status":  "success",
            "run_id":  run_id,
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"❌ Erreur réentraînement: {e}", exc_info=True)
        log_to_redis(f"❌ Erreur réentraînement modèle: {e}", level="error")
        return {"status": "error", "message": str(e)}
