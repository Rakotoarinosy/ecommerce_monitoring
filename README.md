# 🚀 E-Commerce Monitoring & MLOps Platform

Une plateforme moderne de supervision e-commerce combinant :

* 📊 observabilité temps réel
* 🤖 détection d’anomalies par Machine Learning
* 📈 monitoring applicatif & infrastructure
* ⚡ traitement asynchrone des logs
* 🔍 centralisation et analyse des événements système
* 🐳 architecture conteneurisée orientée DevOps & MLOps

Le projet a initialement été développé dans le cadre d’un mémoire de Master MIAGE, puis progressivement transformé vers une architecture moderne inspirée des environnements cloud-native et MLOps.

---

# 🎯 Objectifs du Projet

Cette plateforme vise à :

✅ superviser les paiements e-commerce en temps réel
✅ détecter automatiquement des comportements suspects
✅ centraliser les logs applicatifs
✅ observer les performances backend & infrastructure
✅ industrialiser progressivement les workflows ML
✅ explorer les pratiques modernes DevOps / MLOps

---

# 🧠 Fonctionnalités Principales

## 📌 Monitoring & Observabilité

* Monitoring temps réel avec Prometheus & Grafana
* Dashboards dynamiques de supervision
* Métriques HTTP personnalisées
* Monitoring CPU / RAM / endpoints
* Visualisation des performances applicatives
* Centralisation des logs avec Loki
* Analyse temps réel des événements backend

---

## 🤖 Détection d’Anomalies ML

Le système intègre un moteur de détection d’anomalies permettant d’identifier automatiquement des paiements suspects.

### Exemple :

Un paiement inhabituel de `$1900` a été automatiquement détecté comme anomalie et visualisé dans les dashboards Grafana.

Fonctionnalités :

* prédiction temps réel
* classification normal/anomalie
* supervision des anomalies détectées
* visualisation dans Grafana
* monitoring des comportements suspects

---

## ⚡ Traitement Asynchrone des Logs

Afin d’améliorer les performances et la scalabilité du système :

* Redis est utilisé comme broker de messages
* Celery permet le traitement asynchrone
* les logs critiques sont enregistrés en arrière-plan
* les tâches longues sont découplées du backend principal

Cela permet :

* une meilleure réactivité API
* une architecture plus scalable
* une meilleure résilience du système

---

# 🏗️ Architecture Technique

## 🔧 Stack Backend

* FastAPI
* Python
* WebSockets
* Celery
* Redis
* MongoDB

---

## 🎨 Frontend

* Angular
* Dashboard temps réel
* Visualisation des paiements
* Affichage des logs
* Interface de monitoring

---

## 📊 Monitoring & Logging

* Prometheus
* Grafana
* Loki

---

## 🐳 DevOps & Infrastructure

* Docker
* Docker Compose
* Architecture conteneurisée
* Préparation Kubernetes
* Approche GitOps (future évolution)

---

# 📸 Aperçu du Projet

## ✅ Dashboard Grafana

* supervision temps réel
* métriques système
* anomalies ML
* monitoring HTTP

## ✅ Interface Frontend

* paiements récents
* détection d’anomalies
* logs applicatifs
* monitoring utilisateur

---

# 📂 Structure du Projet

```bash
ecommerce_monitoring/
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── tasks/
│   │   ├── monitoring/
│   │   ├── websocket/
│   │   └── ml/
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/app/
│   └── Dockerfile
│
├── monitoring/
│   ├── grafana/
│   ├── prometheus/
│   └── loki/
│
├── docker-compose.yml
└── README.md
```

---

# ⚙️ Installation

## 📌 Cloner le projet

```bash
git clone https://github.com/your-username/ecommerce-monitoring.git

cd ecommerce-monitoring
```

---

## 📌 Lancer avec Docker

```bash
docker compose up -d --build
```

---

# 🌐 Services Disponibles

| Service          | URL                        |
| ---------------- | -------------------------- |
| Frontend Angular | http://localhost:4200      |
| Backend FastAPI  | http://localhost:8000      |
| Swagger API      | http://localhost:8000/docs |
| Grafana          | http://localhost:3000      |
| Prometheus       | http://localhost:9090      |

---

# 📡 Exemple de Métriques Prometheus

```bash
curl http://localhost:8000/metrics/metrics
```

Métriques exposées :

* ecommerce_payments_total
* ecommerce_anomalies_detected_total
* ecommerce_http_request_duration_seconds
* ecommerce_logs_total

---

# 🔄 Évolutions Futures

## 🚀 Roadmap MLOps

* MLflow
* Model Registry
* Model Monitoring
* Data Drift Detection
* Automated Retraining
* CI/CD ML Pipelines

---

## ☸️ Roadmap Kubernetes

* Kubernetes deployment
* Helm Charts
* ArgoCD
* GitOps workflow
* Horizontal scaling
* Observabilité cloud-native

---

# 📚 Concepts Explorés

Ce projet explore la convergence entre :

* DevOps
* Observabilité
* Monitoring intelligent
* Machine Learning
* MLOps
* Cloud-native architecture
* Asynchronous processing
* Distributed systems

---

# 👨‍💻 Auteur

**RAKOTOARINOSY Fehizoro Andry**
Master MIAGE — Informatique Appliquée à la Gestion d’Entreprise

https://rakotoarinosy.com
---

# ⭐ Remarque

Ce projet continue d’évoluer progressivement vers une architecture MLOps complète afin d’explorer les problématiques modernes de supervision, d’automatisation et d’industrialisation du Machine Learning.
