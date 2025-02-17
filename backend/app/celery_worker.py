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
    "save_logs_every_minute": {
        "task": "app.tasks.save_logs",
        "schedule": crontab(minute="*/1"),
        "options": {"queue": "celery"}
    }
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("✅ Celery worker initialisé avec Beat")
