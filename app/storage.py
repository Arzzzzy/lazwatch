import os
import json
from app.config import SEEN_FILE

def ensure_data_dir():
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)

def load_seen():
    ensure_data_dir()
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_seen(data):
    ensure_data_dir()
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
