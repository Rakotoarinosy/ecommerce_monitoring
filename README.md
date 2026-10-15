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
* les logs restent **5 minutes** dans Redis (onglet « En direct » de la page Logs), puis Celery
  Beat les archive dans MongoDB (onglet « Historique », API `GET /logs/history?level=&q=&skip=&limit=`)
* l'archivage lit et vide Redis de façon atomique : aucun log n'est perdu entre deux passages
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

## 💳 Passerelle de paiement réutilisable

L'API sert de **passerelle de paiement** pour n'importe quel projet : BazarStore l'utilise déjà,
et tout autre projet (boutique, réservation, SaaS…) peut s'y brancher sans détenir de clé Stripe.
Chaque paiement apparaît ensuite dans ce tableau de bord, passe par le modèle d'anomalies et
alimente Prometheus/Grafana.

```
Client ─► Backend du projet ── POST /v1/payment-intents ──► Passerelle ──► Stripe Checkout | Simulateur
                 ▲                                              │
                 └──── webhook signé HMAC-SHA256 ───────────────┘──► MongoDB · ML · Prometheus/Grafana
```

### Le webhook seul ne suffit pas : 3 échanges

| # | Qui | Quoi |
| --- | --- | --- |
| 1 | Backend du projet → passerelle | `POST /v1/payment-intents` crée le paiement et renvoie `checkout_url` |
| 2 | Navigateur du client | Redirigé vers `checkout_url`, il paie, puis revient sur `success_url` ou `cancel_url` |
| 3 | Passerelle → backend du projet | Webhook signé `payment_intent.succeeded` / `failed` / `cancelled` |

Le webhook est une **accélération**, pas la seule source de vérité : au retour du client sur
`success_url`, le projet relit l'intention (`GET /v1/payment-intents/{id}`). Un webhook perdu
(réseau, redéploiement) ne bloque donc jamais une commande. En local, Stripe ne peut pas
joindre la passerelle : c'est cette relecture qui confirme le paiement.

### Étape 1 — Déclarer le projet sur la passerelle

Chaque projet a son nom, sa clé API et son webhook. Dans `backend/.env` de la passerelle :

```env
# Plusieurs projets (JSON sur une ligne). Générer chaque secret : openssl rand -hex 32
GATEWAY_MERCHANTS=[{"name":"BazarStore","api_key":"<clé-1>","webhook_url":"https://api.bazarstore.rakotoarinosy.com/api/v1/orders/payments/gateway/webhook","webhook_secret":"<secret-1>"},{"name":"MonProjet","api_key":"<clé-2>","webhook_url":"https://api.monprojet.com/payments/webhook","webhook_secret":"<secret-2>"}]
```

Un seul projet ? Les variables `GATEWAY_API_KEY`, `GATEWAY_WEBHOOK_SECRET`,
`GATEWAY_MERCHANT_WEBHOOK_URL` et `GATEWAY_MERCHANT_NAME` suffisent (configuration actuelle de BazarStore).
`webhook_url` et `webhook_secret` sont facultatifs : sans eux, le projet se contente de relire l'intention.
Un projet ne voit **jamais** les paiements d'un autre (réponse 404). Redémarrer le backend après modification.

Dans le `.env` **serveur** du projet (jamais dans un frontend ni dans Git) :

```env
PAYMENT_GATEWAY_URL=https://ecommerce-api.rakotoarinosy.com
PAYMENT_GATEWAY_API_KEY=<clé-2>
PAYMENT_GATEWAY_WEBHOOK_SECRET=<secret-2>
```

### Étape 2 — Créer le paiement (côté serveur)

```http
POST /v1/payment-intents
Authorization: Bearer <clé API du projet>
Content-Type: application/json

{
  "merchant_reference": "order-42",          // identifiant de la commande dans le projet (obligatoire)
  "amount": 301000,                          // entier, en ariary (MGA n'a pas de centimes)
  "currency": "MGA",
  "description": "Commande CMD-42",
  "order_reference": "CMD-42",               // facultatif : affiché dans le tableau de bord
  "customer_name": "Rasoa Hanta",            // facultatif
  "customer_email": "hanta@example.com",     // facultatif : pré-rempli sur Stripe
  "lines": [                                 // facultatif ; si présent, la somme doit égaler amount
    {"name": "Coffret détente", "unit_amount": 185000, "quantity": 1},
    {"name": "T-shirt bleu", "unit_amount": 116000, "quantity": 1}
  ],
  "success_url": "https://monprojet.com/commandes/42?payment=success",
  "cancel_url": "https://monprojet.com/commandes/42?payment=cancelled"
}
```

Réponse `201` :

```json
{ "id": "pi_3b65a7d42ae316c7f3976cb2", "merchant_reference": "order-42", "amount": 301000,
  "currency": "MGA", "status": "pending", "provider": "stripe",
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_…", "created_at": "…", "paid_at": null }
```

Enregistrer `id` sur la commande, puis rediriger le navigateur vers `checkout_url`.
En mode Stripe, un montant inférieur à l'équivalent de 0,50 € (≈ 2 500 Ar) est refusé par Stripe :
la passerelle répond alors `502 Fournisseur de paiement indisponible`.
Relancer un paiement pour la même `merchant_reference` annule l'intention précédente encore en attente.

### Étape 3 — Confirmer le paiement

**Au retour du client** : `GET /v1/payment-intents/{id}` (même en-tête `Authorization`).

| `status` | Signification | Action du projet |
| --- | --- | --- |
| `pending` | Pas encore payé | Attendre, proposer de vérifier à nouveau |
| `success` | Payé | Confirmer la commande (une seule fois) |
| `failed` | Carte refusée ou session expirée | Proposer de réessayer |
| `cancelled` | Annulé, ou remplacé par une nouvelle tentative | Proposer de réessayer |

**Webhook** : la passerelle envoie un `POST` sur `webhook_url` à chaque état final, une seule fois :

```http
POST <webhook_url>
X-Gateway-Signature: t=1760572800,v1=5f2b…   ← HMAC-SHA256(webhook_secret, "<t>.<corps brut>")
Content-Type: application/json

{"id":"evt_…","type":"payment_intent.succeeded","created":1760572800,
 "data":{"id":"pi_…","merchant_reference":"order-42","amount":301000,"currency":"MGA","status":"success",…}}
```

À vérifier **sur le corps brut**, avant tout parsing : signature, puis horodatage (5 min maximum
contre le rejeu), puis que `data.id` est bien l'intention en cours de la commande. Répondre `2xx`.

Python (FastAPI) :

```python
import hashlib, hmac, json, os, time
from fastapi import HTTPException, Request

SECRET = os.environ["PAYMENT_GATEWAY_WEBHOOK_SECRET"]

async def gateway_webhook(request: Request):
    body = await request.body()
    try:
        parts = dict(p.split("=", 1) for p in request.headers["x-gateway-signature"].split(","))
        expected = hmac.new(SECRET.encode(), f"{parts['t']}.".encode() + body, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(parts["v1"], expected) and abs(time.time() - int(parts["t"])) <= 300
    except (KeyError, ValueError):
        valid = False
    if not valid:
        raise HTTPException(400, "Signature invalide")
    intent = json.loads(body)["data"]
    # Retrouver la commande par intent["merchant_reference"], vérifier intent["id"],
    # puis appliquer intent["status"] si la commande est encore en attente.
```

Node.js (Express) :

```js
const crypto = require('crypto');
const SECRET = process.env.PAYMENT_GATEWAY_WEBHOOK_SECRET;

app.post('/payments/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const parts = Object.fromEntries((req.get('x-gateway-signature') || '').split(',').map(p => p.split('=')));
  const expected = crypto.createHmac('sha256', SECRET).update(`${parts.t}.`).update(req.body).digest('hex');
  const valid = parts.v1 && parts.v1.length === expected.length
    && crypto.timingSafeEqual(Buffer.from(parts.v1), Buffer.from(expected))
    && Math.abs(Date.now() / 1000 - Number(parts.t)) <= 300;
  if (!valid) return res.status(400).send('Signature invalide');
  const intent = JSON.parse(req.body).data;   // appliquer intent.status à la commande intent.merchant_reference
  res.sendStatus(204);
});
```

Implémentation de référence complète (client, routes, tests) : BazarStore,
`backend/src/infrastructure/external/payment_gateway.py`.

### Checklist d'intégration

- [ ] Projet déclaré dans `GATEWAY_MERCHANTS`, backend de la passerelle redémarré
- [ ] Clé API et secret uniquement dans le `.env` serveur du projet
- [ ] Intention créée côté serveur, `id` enregistré sur la commande
- [ ] Relecture `GET /v1/payment-intents/{id}` au retour sur `success_url`
- [ ] Webhook : signature vérifiée sur le corps brut, rejeu refusé, traitement idempotent
- [ ] Montants en entiers MGA, identiques à ceux de la commande
- [ ] Testé en local avec le simulateur, puis avec Stripe test (carte `4242 4242 4242 4242`)

### Fournisseurs, local et production

| Mode | Quand | Page de paiement |
| --- | --- | --- |
| `stripe` | `STRIPE_SECRET_KEY` défini (prod, ou local avec clé de test) | Stripe Checkout |
| `simulator` | Aucune clé, ou `GATEWAY_PROVIDER=simulator` (CI, démo) | Page « Payer / Refuser / Annuler » |

```bash
# Passerelle seule en local (API + Mongo + Redis) → http://localhost:8011/docs
docker compose -f docker-compose.gateway.yml up -d --build
```

En production : `GATEWAY_PROVIDER=stripe`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` et les projets
dans `backend/.env` (voir `backend/.env.template`). Webhook Stripe à déclarer une seule fois pour
tous les projets : `https://ecommerce-api.rakotoarinosy.com/payments/webhook`, événement
`checkout.session.completed`.

Le modèle d'anomalies ayant été entraîné en USD, les montants MGA sont convertis
(`MGA_PER_USD`, 4500 par défaut) avant la prédiction ; l'affichage reste en ariary.
Métriques : `gateway_payment_intents_total{status,provider}`, `gateway_merchant_webhooks_total{result}`.
Tests : `cd backend && pip install -r requirements-dev.txt && pytest -q` (MongoDB et Redis sur localhost).

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
