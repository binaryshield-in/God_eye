# utils/storage.py
import json
from pathlib import Path

def save_json(data, filename: str):
    """
    Save a Python dictionary or list as a JSON file.
    Automatically creates parent directories if needed.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
