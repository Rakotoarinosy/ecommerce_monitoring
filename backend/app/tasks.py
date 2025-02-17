from app.config import db, redis_client
from app.celery_worker import celery
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_to_redis(message, level="info"):
    """Capture les logs et les stocke dans Redis."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message
    }
    
    # Convertir le log en JSON et l'ajouter à la liste Redis
    redis_client.rpush("recent_logs", json.dumps(log_entry))

@celery.task(name="app.tasks.save_logs")
def save_logs():
    """Sauvegarde les logs de Redis vers MongoDB."""
    try:
        logger.info("🚀 Début de la tâche save_logs")
        
        log_to_redis("Début du processus d'enregistrement des logs", level="info")
        
        logs = redis_client.lrange("recent_logs", 0, -1)
        if not logs:
            logger.info("⚠️ Aucun log à enregistrer.")
            return {"status": "no logs"}

        log_entries = [json.loads(log) for log in logs]
        logger.info(f"📌 {len(log_entries)} logs récupérés de Redis.")

        # Insérer les logs dans MongoDB
        db.logs.insert_many(log_entries)
        logger.info(f"✅ {len(log_entries)} logs enregistrés dans MongoDB.")

        # Nettoyer Redis après insertion
        redis_client.delete("recent_logs")
        logger.info("🧹 Redis nettoyé après insertion des logs.")

        return {"status": "success", "logs_saved": len(log_entries)}
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'enregistrement des logs : {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@celery.task(name="app.tasks.test_celery")
def test_celery():
    """Tâche de test pour vérifier si Celery fonctionne."""
    logger.info("✅ Tâche Celery test exécutée avec succès.")
    return {"status": "success"}