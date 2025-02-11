from datetime import datetime
import json
from fastapi import APIRouter
from app.config import db, redis_client
from app.routes.websockets import notify_log_clients

router = APIRouter()

@router.post("/")
def create_log(level: str, message: str):
    log_entry = {"level": level, "message": message, "timestamp": datetime.utcnow()}
    db.logs.insert_one(log_entry)
    
    # Stocker les logs critiques dans Redis
    if level in ["error", "critical"]:
        redis_client.lpush("critical_logs", json.dumps(log_entry))
        redis_client.ltrim("critical_logs", 0, 9)  # Garde les 10 derniers logs critiques
    
    # Notifier les clients via WebSocket
    notify_log_clients(log_entry)
    
    return {"message": "Log enregistré"}

@router.get("/recent")
def get_recent_logs():
    logs = [json.loads(log) for log in redis_client.lrange("recent_logs", 0, -1)]
    return {"logs": logs}

@router.get("/critical")
def get_critical_logs():
    logs = [json.loads(log) for log in redis_client.lrange("critical_logs", 0, -1)]
    return {"logs": logs}