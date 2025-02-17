from datetime import datetime
import json
import logging
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter
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
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Stocker le log dans Redis sous la clé "recent_logs"
    redis_client.lpush("recent_logs", json.dumps(log_entry))
    redis_client.ltrim("recent_logs", 0, 99)  # Garde les 100 derniers logs

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
#             "timestamp": datetime.utcnow().isoformat()  # Conversion datetime en string
#         }
#         log_entries.append(log_entry)
        
#         # Stocker le log dans Redis sous la clé "recent_logs" (pour les logs récents)
#         redis_client.lpush("recent_logs", json.dumps(log_entry))
#         redis_client.ltrim("recent_logs", 0, 99)  # Garde les 100 derniers logs
        
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
            "timestamp": datetime.utcnow().isoformat()
        }
        # Envoyer le log à Redis
        redis_client.lpush("recent_logs", json.dumps(log_entry))

# Ajouter le handler au logger
logger.addHandler(RedisLogHandler())