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

## Passerelle de paiement pour BazarStore

L'API sert aussi de **passerelle de paiement** : BazarStore ne détient plus aucune clé Stripe.
Montants en ariary (`MGA`, devise sans centimes chez Stripe).

```
Client ─► BazarStore API ── POST /v1/payment-intents ──► Passerelle ──► Stripe Checkout | Simulateur
              ▲                                              │
              └──── webhook signé HMAC-SHA256 ───────────────┘──► MongoDB · ML · Prometheus/Grafana
```

| Endpoint | Rôle |
| --- | --- |
| `POST /v1/payment-intents` | Crée une intention (`Authorization: Bearer <GATEWAY_API_KEY>`), renvoie `checkout_url` |
| `GET /v1/payment-intents/{id}` | Statut (`pending`, `success`, `failed`, `cancelled`), relit Stripe si besoin |
| `GET/POST /v1/simulator/checkout/{id}` | Page de paiement factice (mode `simulator`) : payer, refuser, annuler |
| `POST /payments/webhook` | Webhook Stripe (sessions de la passerelle reconnues par `metadata.payment_intent_id`) |

À chaque état final, la passerelle envoie au marchand `payment_intent.succeeded|failed|cancelled`
avec l'en-tête `X-Gateway-Signature: t=<unix>,v1=<hmac_sha256(secret, "<t>.<corps>")>`. BazarStore
vérifie la signature (fenêtre de 5 min contre le rejeu) et relit aussi l'intention au retour du client :
un webhook perdu ne bloque jamais une commande. Une transition `pending → final` n'a lieu qu'une fois
(écriture conditionnelle Mongo), donc un seul webhook par paiement.

Le modèle d'anomalies ayant été entraîné en USD, les montants MGA sont convertis
(`MGA_PER_USD`, 4500 par défaut) avant la prédiction ; l'affichage reste en ariary.
Métriques : `gateway_payment_intents_total{status,provider}`, `gateway_merchant_webhooks_total{result}`.

### En local

```bash
docker compose -f docker-compose.gateway.yml up -d --build    # API + Mongo + Redis
# STRIPE_SECRET_KEY=sk_test_… dans backend/.env → vraie page Stripe Checkout (carte 4242 4242 4242 4242)
# sans clé, ou GATEWAY_PROVIDER=simulator → page de paiement simulée (utilisée par la CI)
# BazarStore/backend/.env :
#   PAYMENTS_ENABLED=true
#   PAYMENT_GATEWAY_URL=http://localhost:8011
#   PAYMENT_GATEWAY_API_KEY=local-gateway-key
#   PAYMENT_GATEWAY_WEBHOOK_SECRET=local-gateway-webhook-secret
```

Tests : `cd backend && pip install -r requirements-dev.txt && pytest -q` (MongoDB et Redis sur localhost).

### En production

Dans `backend/.env` du VPS : `GATEWAY_PROVIDER=stripe`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`GATEWAY_API_KEY`, `GATEWAY_WEBHOOK_SECRET`, `GATEWAY_MERCHANT_WEBHOOK_URL` (voir `backend/.env.template`).
Les deux secrets sont partagés avec BazarStore (`PAYMENT_GATEWAY_API_KEY`, `PAYMENT_GATEWAY_WEBHOOK_SECRET`).
Endpoint du webhook Stripe : `https://ecommerce-api.rakotoarinosy.com/payments/webhook`.

## Déploiement continu avec GitHub Actions

Le workflow `.github/workflows/ci-cd.yml` lance les tests de la passerelle (MongoDB et Redis
réels en services GitHub), construit l'image backend et le frontend sur chaque pull request et
chaque push vers `main`. Après leur succès, un push vers `main` déploie `backend`, `frontend`,
`celery_worker` et `celery_beat` sur le VPS avec `--no-deps` (MongoDB, Redis, Grafana… et leurs
volumes ne sont jamais recréés), puis vérifie `https://ecommerce-api.rakotoarinosy.com/health`.
Côté BazarStore, un job « contrat » démarre cette passerelle (`docker-compose.gateway.yml`) et
paie une vraie commande de bout en bout avant tout déploiement.

Dans **Settings > Secrets and variables > Actions** du dépôt, ajouter les variables :

| Variable | Valeur |
| --- | --- |
| `DEPLOY_HOST` | Adresse IP ou nom DNS du VPS |
| `DEPLOY_USER` | Utilisateur SSH du VPS |
| `DEPLOY_PATH` | Chemin du clone, par défaut `/srv/ecommerce_monitoring` |

Ajouter les secrets :

| Secret | Valeur |
| --- | --- |
| `DEPLOY_SSH_KEY` | Clé privée SSH dédiée au déploiement |
| `DEPLOY_KNOWN_HOSTS` | Clé d'hôte SSH du VPS, vérifiée avant de l'enregistrer |

Le compte SSH doit pouvoir accéder au dépôt Git sur le VPS, exécuter Docker Compose et
déployer depuis la branche `main`. Le dépôt doit déjà être cloné dans `DEPLOY_PATH`, avec
`backend/.env` et le fichier `.env` racine configurés localement sur le serveur. Ces fichiers
ne sont ni transférés ni modifiés par GitHub Actions ; ne placez aucun secret dans le dépôt.
Les valeurs `MONGO_ROOT_USER`, `MONGO_ROOT_PASSWORD` et `GMAIL_APP_PASSWORD` utilisées par
`docker-compose.yml` doivent notamment être renseignées dans l'environnement Compose du VPS.

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
| Backend FastAPI  | http://localhost:8011      |
| Swagger API      | http://localhost:8011/docs |
| Grafana          | http://localhost:3000      |
| Prometheus       | http://localhost:9090      |

---

# 📡 Exemple de Métriques Prometheus

```bash
curl http://localhost:8011/metrics/metrics
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
