# 🛒 E-commerce Monitoring System

Un système combinant **paiement en temps réel** et **monitoring avancé des logs**. Ce projet est conçu pour être **modulaire, scalable** et proche d'un environnement de production.

---

## 🚀 Technologies Utilisées

- **Backend** : FastAPI (Python)
- **Frontend** : Angular
- **Base de données** : MongoDB
- **Cache** : Redis
- **Monitoring** : Grafana & Prometheus
- **Tâches en arrière-plan** : Celery & Celery Beat
- **Déploiement** : Docker & Docker Compose
- **Paiement** : Stripe/PayPal (intégration optionnelle)

---

## 📌 Fonctionnalités

### 🔹 Module de Paiement en Temps Réel
✅ **Intégration Stripe/PayPal** pour traiter les paiements.  
✅ **Stockage des paiements** et utilisateurs dans MongoDB.  
✅ **Mise en cache des transactions** récentes avec Redis.  
✅ **Gestion des statuts de paiement** (succès, échec, en attente).  
✅ **WebSockets** pour mise à jour en temps réel.  
✅ **Interface Angular** avec historique des paiements et graphiques.  

### 🔹 Module de Gestion des Logs et Monitoring
✅ **Collecte des logs** des paiements et erreurs API.  
✅ **Stockage des logs** dans MongoDB.  
✅ **Cache des logs critiques** récents avec Redis.  
✅ **WebSockets** pour affichage en temps réel des logs.  
✅ **Tableau de bord Angular** avec filtres et graphiques.  
✅ **Intégration avec Grafana & Prometheus** pour visualisation avancée.  

---

## 📌 Prérequis

Avant d'exécuter le projet, assure-toi d'avoir installé :

- **Docker & Docker Compose**
- **Python 3.10+** (si exécution hors Docker)
- **Node.js 16+ & Angular CLI** (pour le frontend si hors Docker)

```bash
docker --version
python3 --version
node -v
ng version
```

---

## 📌 Installation & Configuration

### **1️⃣ Cloner le projet**
```bash
git clone https://github.com/ton-repo/ecommerce-monitoring.git
cd ecommerce-monitoring
```

### **2️⃣ Configurer les variables d'environnement**
Crée un fichier `.env` dans `backend/` et ajoute :

```ini
MONGO_URI=mongodb://mongodb:27017
MONGO_DB_NAME=ecommerce_db
REDIS_HOST=redis
REDIS_PORT=6379
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLIC_KEY=pk_test_xxx
```

---

## 📌 Lancer le projet avec Docker
```bash
docker compose up -d --build
```
✅ **Services inclus :**  
- Backend : `FastAPI + WebSockets`  
- Frontend : `Angular`  
- Base de données : `MongoDB`  
- Stockage temporaire : `Redis`  
- Tâches en arrière-plan : `Celery + Celery Beat`  
- Gestion des paiements : `Stripe/PayPal`  

---

## 📌 Vérifier les Logs & WebSockets

### **🎯 Accéder au Backend (FastAPI)**
- **Swagger API Docs** : [http://localhost:8000/docs](http://localhost:8000/docs)  

### **🎯 Affichage des logs en temps réel**
- **Vérifier la connexion WebSocket des logs**  
```bash
docker logs -f ecommerce_monitoring-backend-1
```

- **Se connecter à WebSocket depuis le navigateur**  
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/logs");
ws.onmessage = (event) => console.log("Logs:", event.data);
```

### **🎯 Vérifier les logs enregistrés dans MongoDB**
```bash
docker exec -it ecommerce_monitoring-mongodb-1 mongosh
use ecommerce_db
db.logs.find().pretty()
```

---

## 📌 API Endpoints

### 📌 Paiements
- `POST /payments` : Créer un nouveau paiement.
- `GET /payments/{id}` : Récupérer les détails d'un paiement.
- `GET /payments/recent` : Obtenir les derniers paiements (cache Redis).

### 📌 Logs
- `POST /logs` : Enregistrer un log.
- `GET /logs/recent` : Récupérer les logs récents.
- `GET /logs/stats` : Obtenir les statistiques des logs.

### 📌 Interface Utilisateur
- **Dashboard Angular** : Accédez à l'interface pour visualiser les paiements et les logs en temps réel.

---

## 📌 Contribution

Les contributions sont les bienvenues ! Voici comment vous pouvez aider :

1. **Forker le projet**
2. **Créer une branche** pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. **Commiter vos changements** (`git commit -m 'Ajout d'une fonctionnalité incroyable'`)
4. **Pusher la branche** (`git push origin feature/AmazingFeature`)
5. **Ouvrir une Pull Request**

---

## 📌 Structure du Projet
```bash
ecommerce_monitoring/
│-- backend/               # 📌 API FastAPI + WebSockets
│   ├-- app/
│   │   ├-- config.py      # 📌 Configuration (MongoDB, Redis, Celery, Stripe)
│   │   ├-- routes/        # 📌 Routes API (logs, paiements)
│   │   ├-- tasks.py       # 📌 Tâches Celery (sauvegarde des logs, paiements)
│   │   ├-- websockets.py  # 📌 Gestion WebSocket en temps réel
│   ├-- Dockerfile
│   ├-- requirements.txt
│-- frontend/              # 📌 Application Angular
│   ├-- src/app/
│   │   ├-- services/      # 📌 WebSocketService (logs en temps réel, paiements)
│   │   ├-- components/    # 📌 UI pour affichage des logs et paiements
│   ├-- Dockerfile
│-- docker-compose.yml     # 📌 Orchestration des services
│-- README.md              # 📌 Documentation
```

---

## 📌 Prochaine Étape 🔥
1️⃣ **Mettre en place un système d’alertes (Slack, Email)**  
2️⃣ **Créer un Dashboard avec des statistiques en temps réel**  
3️⃣ **Intégrer une API Gateway (NGINX) pour améliorer la sécurité**  

---

## 📌 Auteurs
👨‍💻 **RAKOTOARINOSY Fehizoro Andry** – _Dev Back & Monitoring_  
👨‍💻 **None** – _Contributeurs_  
📅 **Mise à jour :** `2025-02-14`  

🔥 **Bon monitoring !** 🚀
