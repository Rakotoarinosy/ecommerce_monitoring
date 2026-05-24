# ════════════════════════════════════════════════════════════════════
# AJOUTER DANS celery_worker.py — beat_schedule
# (dans celery.conf.beat_schedule = { ... })
# ════════════════════════════════════════════════════════════════════

    # Réentraînement automatique toutes les 24h
    "retrain_model_daily": {
        "task": "app.tasks.retrain_model",
        "schedule": crontab(hour="2", minute="0"),  # 2h du matin
        "options": {"queue": "celery"}
    },

    # Réentraînement hebdomadaire complet (dimanche à 3h)
    "retrain_model_weekly": {
        "task": "app.tasks.retrain_model",
        "schedule": crontab(day_of_week="0", hour="3", minute="0"),
        "options": {"queue": "celery"}
    },
