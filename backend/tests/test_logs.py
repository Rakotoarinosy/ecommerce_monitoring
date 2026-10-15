import json

from app.config import db, redis_client
from app.tasks import log_to_redis, save_logs


def test_logs_are_archived_then_listed_in_history(client):
    redis_client.delete("recent_logs")
    log_to_redis("Paiement pi_1 : success", level="info")
    log_to_redis("Stripe indisponible", level="error")

    # Les plus récents d'abord dans Redis (page « En direct »).
    assert json.loads(redis_client.lindex("recent_logs", 0))["message"] == "Stripe indisponible"

    assert save_logs()["logs_saved"] == 2
    assert redis_client.llen("recent_logs") == 0

    history = client.get("/logs/history").json()
    assert history["total"] == 2
    assert history["logs"][0]["message"] == "Stripe indisponible"

    errors = client.get("/logs/history", params={"level": "error"}).json()
    assert [log["message"] for log in errors["logs"]] == ["Stripe indisponible"]
    assert client.get("/logs/history", params={"q": "pi_1"}).json()["total"] == 1
    db.logs.delete_many({})
