import json
from config import JSON_FILE

def load_stats():
    try:
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_stats(mod_stats):
    with open(JSON_FILE, "w") as f:
        json.dump(mod_stats, f, indent=4)
