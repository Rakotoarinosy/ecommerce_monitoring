from app.config import db, redis_client
from app.celery_worker import celery
import json
import logging
from datetime import datetime, timezone
import sys
sys.path.insert(0, "/app/app/ml")
from app.ml.train_model import train_and_log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_to_redis(message, level="info"):
    """Capture les logs et les stocke dans Redis."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message
    }
    
    # En tête de liste : la page « En direct » lit les plus récents en premier.
    redis_client.lpush("recent_logs", json.dumps(log_entry))

@celery.task(name="app.tasks.save_logs")
def save_logs():
    """Sauvegarde les logs de Redis vers MongoDB."""
    try:
        logger.info("🚀 Début de la tâche save_logs")
        
        # log_to_redis("Début du processus d'enregistrement des logs", level="info")
        
        # Lecture + vidage atomiques : un log écrit pendant l'archivage n'est jamais perdu.
        pipe = redis_client.pipeline(transaction=True)
        pipe.lrange("recent_logs", 0, -1)
        pipe.delete("recent_logs")
        logs, _ = pipe.execute()
        if not logs:
            logger.info("⚠️ Aucun log à enregistrer.")
            return {"status": "no logs"}

        log_entries = [json.loads(log) for log in logs]
        logger.info(f"📌 {len(log_entries)} logs récupérés de Redis.")

        try:
            db.logs.insert_many(log_entries)
        except Exception:
            # MongoDB indisponible : on remet les logs dans Redis pour le prochain passage.
            redis_client.rpush("recent_logs", *logs)
            raise
        logger.info(f"✅ {len(log_entries)} logs archivés dans MongoDB.")

        return {"status": "success", "logs_saved": len(log_entries)}
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'enregistrement des logs : {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@celery.task(name="app.tasks.test_celery")
def test_celery():
    """Tâche de test pour vérifier si Celery fonctionne."""
    logger.info("✅ Tâche Celery test exécutée avec succès.")
    return {"status": "success"}

@celery.task(name="app.tasks.retrain_model")
def retrain_model():
    """Réentraîne le modèle Isolation Forest avec MLflow tracking."""
    try:
        logger.info("🤖 Début du réentraînement MLOps")
        log_to_redis("🤖 Réentraînement du modèle ML démarré", level="info")


        result = train_and_log()
        run_id  = result["run_id"]
        metrics = result["metrics"]

        logger.info(f"✅ Réentraînement terminé — Run ID: {run_id}")

        from app.routes.ml_model import reload_model
        reload_model()

        log_to_redis(
            f"✅ Modèle réentraîné — F1={metrics['f1_score']} — "
            f"Anomalies={metrics['anomaly_count']}/{metrics['dataset_size']}",
            level="info"
        )
        return {"status": "success", "run_id": run_id, "metrics": metrics}

    except Exception as e:
        logger.error(f"❌ Erreur réentraînement: {e}", exc_info=True)
        log_to_redis(f"❌ Erreur réentraînement modèle: {e}", level="error")
        return {"status": "error", "message": str(e)}
