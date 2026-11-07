import json
import os
import threading

PATH = os.getenv("PLANS_FILE", "plans.json")
_lock = threading.Lock()


def _load() -> dict:
    if not os.path.exists(PATH):
        return {}
    try:
        with open(PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def save_plan(plan: dict) -> None:
    with _lock:
        data = _load()
        data[plan["id"]] = plan
        with open(PATH, "w") as f:
            json.dump(data, f)


def get_plan(plan_id: str) -> dict | None:
    with _lock:
        return _load().get(plan_id)
