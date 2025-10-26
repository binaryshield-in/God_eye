# utils/logger.py
"""
Centralized logger utility for GodEye.
Provides a standardized logging setup accessible across modules.
"""

import logging
import os
from datetime import datetime

# Define log directory
LOG_FILE = os.getenv("LOG_FILE", "godeye.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True) if os.path.dirname(LOG_FILE) else None

def get_logger(name: str = "GodEye") -> logging.Logger:
    """
    Returns a pre-configured logger instance.

    Args:
        name (str): Name of the logger (e.g., 'collector', 'core.pipeline')

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File Handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Attach handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Optional: default project-wide logger
logger = get_logger("GodEye")
