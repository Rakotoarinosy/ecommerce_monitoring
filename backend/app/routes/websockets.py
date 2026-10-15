import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
from fastapi import APIRouter, WebSocket
from app.config import redis_client
import json

router = APIRouter()

# 🔹 Listes des connexions WebSocket actives
active_payment_connections: List[WebSocket] = []
active_log_connections: List[WebSocket] = []
active_connections = []

# 🔹 Verrous pour protéger les accès concurrents
payment_lock = asyncio.Lock()
log_lock = asyncio.Lock()

from app.tasks import log_to_redis  # Importer la fonction log_to_redis

# ✅ WebSocket pour les paiements
async def websocket_payments_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with payment_lock:  # 🔒 Protection de l'accès
        active_payment_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Garde la connexion active
    except WebSocketDisconnect:
        async with payment_lock:  # 🔒 Protection de l'accès
            active_payment_connections.remove(websocket)

# ✅ WebSocket pour les logs
async def websocket_logs_endpoint(websocket: WebSocket):
    """ Gère les connexions WebSocket pour les logs en temps réel. """
    await websocket.accept()
    async with log_lock:
        active_log_connections.append(websocket)

    try:
        while True:
            logs = redis_client.lrange("recent_logs", 0, 49)  # 50 plus récents (non encore archivés)
            logs = [json.loads(log) for log in logs]
            await websocket.send_json({"logs": logs})
            await asyncio.sleep(1)  # 🔄 Rafraîchissement automatique
    except WebSocketDisconnect:
        async with log_lock:
            active_log_connections.remove(websocket)

# ✅ Notifier les clients WebSocket pour les paiements
async def notify_payment_clients(payment_data: dict):
    disconnected_clients = []

    async with payment_lock:  # 🔒 Protection de l'accès
        for connection in active_payment_connections:
            try:
                await connection.send_json(payment_data)
            except Exception as e:
                print(f"⚠️ Erreur WebSocket: {e}")
                log_to_redis(f"⚠️ Erreur WebSocket: {e}", level="error")            
                disconnected_clients.append(connection)

        # Supprimer les connexions inactives
        for conn in disconnected_clients:
            active_payment_connections.remove(conn)

# ✅ Notifier les clients WebSocket pour les logs
async def notify_log_clients(log_data: dict):
    disconnected_clients = []

    async with log_lock:  # 🔒 Protection de l'accès
        for connection in active_log_connections:
            try:
                await connection.send_json(log_data)
            except Exception as e:
                print(f"⚠️ Erreur WebSocket: {e}")
                log_to_redis(f"⚠️ Erreur WebSocket: {e}", level="error")      
                disconnected_clients.append(connection)

        # Supprimer les connexions inactives
        for conn in disconnected_clients:
            active_log_connections.remove(conn)