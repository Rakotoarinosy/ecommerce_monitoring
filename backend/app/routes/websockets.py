import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

# 🔹 Listes des connexions WebSocket actives
active_payment_connections: List[WebSocket] = []
active_log_connections: List[WebSocket] = []

# ✅ WebSocket pour les paiements
async def websocket_payments_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_payment_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Garde la connexion active
    except WebSocketDisconnect:
        active_payment_connections.remove(websocket)

# ✅ WebSocket pour les logs
async def websocket_logs_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_log_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Garde la connexion active
    except WebSocketDisconnect:
        active_log_connections.remove(websocket)

# ✅ Notifier les clients WebSocket pour les paiements
async def notify_payment_clients(payment_data: dict):
    disconnected_clients = []  # Connexions à supprimer

    for connection in active_payment_connections:
        try:
            await connection.send_json(payment_data)  # 🔹 Envoi asynchrone
        except Exception as e:
            print(f"⚠️ Erreur WebSocket: {e}")
            disconnected_clients.append(connection)

    # Supprimer les connexions inactives
    for conn in disconnected_clients:
        active_payment_connections.remove(conn)

# ✅ Notifier les clients WebSocket pour les logs
async def notify_log_clients(log_data: dict):
    disconnected_clients = []  # Connexions à supprimer

    for connection in active_log_connections:
        try:
            await connection.send_json(log_data)  # 🔹 Envoi asynchrone
        except Exception as e:
            print(f"⚠️ Erreur WebSocket: {e}")
            disconnected_clients.append(connection)

    # Supprimer les connexions inactives
    for conn in disconnected_clients:
        active_log_connections.remove(conn)
