import json
import os

FILE = "seen_ids.json"


def load_ids():
    if not os.path.exists(FILE):
        return set()

    try:
        with open(FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()


def save_ids(ids):
    try:
        with open(FILE, "w") as f:
            json.dump(list(ids), f)
    except:
        pass
