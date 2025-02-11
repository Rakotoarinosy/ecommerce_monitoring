# backend/app/config.py
from pymongo import MongoClient
import redis
import os
from dotenv import load_dotenv
import logging

load_dotenv()  # Charger les variables d'environnement

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ecommerce_db")
db = mongo_client[MONGO_DB_NAME]  # Base de données principale

# Configuration Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,  db=0, decode_responses=True)

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Exemple d'utilisation dans une fonction
logger = logging.getLogger(__name__)