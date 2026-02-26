"""
Utility Functions
=================
Helper functions used across the project.
"""

import yaml
import os
from loguru import logger


def load_config(config_path="config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def ensure_directories():
    """Create all necessary directories."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/cache",
        "logs",
        "models",
        "notebooks",
        "docs",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("✅ All directories verified")


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage."""
    return f"{value * 100:.2f}%"