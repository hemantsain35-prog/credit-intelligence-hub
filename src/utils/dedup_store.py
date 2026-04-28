import json
import os

FILE_PATH = "processed_ids.json"


def load_ids():
    if not os.path.exists(FILE_PATH):
        return set()

    with open(FILE_PATH, "r") as f:
        return set(json.load(f))


def save_ids(ids):
    with open(FILE_PATH, "w") as f:
        json.dump(list(ids), f)


def is_new_lead(lead_id, seen_ids):
    return lead_id not in seen_ids
