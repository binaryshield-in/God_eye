# utils/config.py
"""
Configuration management for GodEye.
Handles .env file loading and environment variable access.
"""


import os
from pathlib import Path
from dotenv import load_dotenv

def load_env(env_path: str = None) -> dict:
    env_file = Path(env_path or Path.cwd() / ".env")
    if env_file.exists():
        try:
            load_dotenv(dotenv_path=env_file)
        except Exception as e:
            print(f"[ERROR] Failed to load .env: {e}")
            return {}
    else:
        print(f"[WARN] .env not found at {env_file}")
    return dict(os.environ)

def get_env(key: str, default=None):
    """
    Safely get an environment variable with optional default.
    """
    return os.getenv(key, default)