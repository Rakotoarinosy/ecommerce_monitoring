from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from app.config import db
from enum import Enum

class StatusEnum(str, Enum):
    pending="pending"
    success="success" 
    failed="failed"

class LevelEnum(str, Enum):
    INFO="INFO"
    WARNING="WARNING"
    ERROR="ERROR"

class ServiceLog(str, Enum):
    backend="backend"
    frontend="frontend"
    database="database"
    mongodb="mongodb"
    redis="redis"
    
    

# Modèle des paiements
class Payment:
    def __init__(self, user_id: str, amount: float, status: StatusEnum):
        self.user_id = user_id
        self.amount = amount
        self.status = status.value 
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "amount": self.amount,
            "status": self.status,
            "created_at": self.created_at
        }

    def save(self):
        db.payments.insert_one(self.to_dict())

# Modèle des logs
class Log:
    def __init__(self, level: LevelEnum, message: str, service: ServiceLog):
        self.level = level.value # "INFO", "WARNING", "ERROR"
        self.message = message
        self.service =  service.value  # "backend", "frontend", "database"
        self.timestamp = datetime.utcnow()

    def to_dict(self):
        return {
            "level": self.level,
            "message": self.message,
            "service": self.service,
            "timestamp": self.timestamp
        }

    def save(self):
        db.logs.insert_one(self.to_dict())
