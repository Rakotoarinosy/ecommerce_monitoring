from celery import Celery
import os
from dotenv import load_dotenv
from celery.schedules import crontab
import logging

load_dotenv()

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery = Celery(
    "app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,
    include=["app.tasks"]
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC"
)

# Planification de tâches périodiques avec Celery Beat
celery.conf.beat_schedule = {
    # Les logs restent 5 min dans Redis (page « En direct ») avant d'être archivés dans MongoDB.
    "save_logs_every_5_minutes": {
        "task": "app.tasks.save_logs",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "celery"}
    },
    "retrain_model_daily": {
        "task": "app.tasks.retrain_model",
        "schedule": crontab(hour="2", minute="0"),
        "options": {"queue": "celery"}
    }
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✅ Celery worker initialisé avec Beat")
