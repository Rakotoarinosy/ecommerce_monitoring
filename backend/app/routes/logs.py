from datetime import datetime, timezone
import json
import logging
from typing import List
from pydantic import BaseModel
import re
from fastapi import APIRouter, Query
from app.config import db, redis_client
from app.routes.websockets import notify_log_clients

router = APIRouter()

class LogEntry(BaseModel):
    level: str
    message: str

# Modèle pour recevoir plusieurs logs
class LogBatch(BaseModel):
    logs: List[LogEntry]

@router.post("/")
async def create_log(log: LogEntry):
    log_entry = {
        "level": log.level,
        "message": log.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Stocker le log dans Redis sous la clé "recent_logs"
    redis_client.lpush("recent_logs", json.dumps(log_entry))
    redis_client.ltrim("recent_logs", 0, 1999)  # Borne de sécurité entre deux archivages (5 min)

    # Stocker les logs critiques dans Redis (pour la clé "critical_logs")
    if log.level in ["error", "critical"]:
        redis_client.lpush("critical_logs", json.dumps(log_entry))
        redis_client.ltrim("critical_logs", 0, 9)  # Garde les 10 derniers logs critiques
    
    # Notifier les clients via WebSocket
    await notify_log_clients(log_entry)

    return {"message": "Log enregistré dans Redis"}

# @router.post("/many_logs")
# async def create_logs(log_batch: LogBatch):
#     log_entries = []
    
#     for log in log_batch.logs:
#         log_entry = {
#             "level": log.level,
#             "message": log.message,
#             "timestamp": datetime.now(timezone.utc).isoformat()  # Conversion datetime en string
#         }
#         log_entries.append(log_entry)
        
#         # Stocker le log dans Redis sous la clé "recent_logs" (pour les logs récents)
#         redis_client.lpush("recent_logs", json.dumps(log_entry))
#         redis_client.ltrim("recent_logs", 0, 1999)  # Borne de sécurité entre deux archivages (5 min)
        
#         # Stocker les logs critiques dans Redis (pour la clé "critical_logs")
#         if log.level in ["error", "critical"]:
#             redis_client.lpush("critical_logs", json.dumps(log_entry))
#             redis_client.ltrim("critical_logs", 0, 9)  # Garde les 10 derniers logs critiques
        
#         # Notifier les clients WebSocket
#         await notify_log_clients(log_entry)  # Ajout de await

#     # Insérer tous les logs en une seule fois dans MongoDB (optimisation)
#     if log_entries:
#         db.logs.insert_many(log_entries)

#     return {"message": f"{len(log_entries)} logs enregistrés"}

@router.get("/recent")
def get_recent_logs():
    logs = [json.loads(log) for log in redis_client.lrange("recent_logs", 0, -1)]
    return {"logs": logs}

@router.get("/history")
def get_log_history(
    level: str | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
):
    """Logs archivés dans MongoDB (toutes les 5 min par Celery), du plus récent au plus ancien."""
    query: dict = {"message": {"$exists": True}}
    if level:
        levels = ["error", "critical"] if level.lower() == "error" else [level.lower()]
        query["level"] = {"$in": levels + [lvl.upper() for lvl in levels]}
    if q:
        query["message"] = {"$regex": re.escape(q), "$options": "i"}
    total = db.logs.count_documents(query)
    rows = db.logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit)
    logs = [
        {**row, "timestamp": row["timestamp"].isoformat() if isinstance(row.get("timestamp"), datetime) else row.get("timestamp")}
        for row in rows
    ]
    return {"total": total, "logs": logs}


@router.get("/critical")
def get_critical_logs():
    logs = [json.loads(log) for log in redis_client.lrange("critical_logs", 0, -1)]
    return {"logs": logs}

# Configuration du logger
logger = logging.getLogger(__name__)

class RedisLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = {
            "level": record.levelname,
            "message": self.format(record),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Envoyer le log à Redis
        redis_client.lpush("recent_logs", json.dumps(log_entry))

# Ajouter le handler au logger
logger.addHandler(RedisLogHandler())