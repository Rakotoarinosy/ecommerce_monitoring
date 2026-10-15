"""Tests de la passerelle contre un vrai MongoDB/Redis (services GitHub Actions ou Docker local).

    docker run -d --rm -p 27017:27017 mongo:6 && docker run -d --rm -p 6379:6379 redis:alpine
    pip install -r requirements-dev.txt && pytest -q
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

WEBHOOK_PORT = 8765
os.environ.update(
    MONGO_URI=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    MONGO_DB_NAME="gateway_test",
    # Deux projets : BazarStore (avec webhook) et un second projet sans webhook.
    GATEWAY_MERCHANTS=json.dumps([
        {
            "name": "BazarStore",
            "api_key": "test-api-key",
            "webhook_url": f"http://127.0.0.1:{WEBHOOK_PORT}/webhook",
            "webhook_secret": "test-webhook-secret",
        },
        {"name": "AutreProjet", "api_key": "other-api-key"},
    ]),
    GATEWAY_PROVIDER="simulator",
    GATEWAY_PUBLIC_URL="http://gateway.test",
)
os.environ.pop("STRIPE_SECRET_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.config import db  # noqa: E402
from app.main import app  # noqa: E402


class WebhookInbox(BaseHTTPRequestHandler):
    received: list[tuple[dict, bytes]] = []

    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers["Content-Length"]))
        WebhookInbox.received.append((dict(self.headers), body))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def merchant_inbox():
    server = HTTPServer(("127.0.0.1", WEBHOOK_PORT), WebhookInbox)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield WebhookInbox.received
    server.shutdown()


@pytest.fixture
def client(merchant_inbox):
    db.payments.delete_many({"source": {"$in": ["BazarStore", "AutreProjet"]}})
    db.logs.delete_many({})
    merchant_inbox.clear()
    with TestClient(app) as test_client:
        yield test_client
