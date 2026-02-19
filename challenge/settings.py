import os
from pathlib import Path
from typing import Optional, Set


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _get_optional_int(name: str) -> Optional[int]:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    return int(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_csv_set(name: str, default: str) -> Set[str]:
    raw = os.getenv(name, default)
    return {item.strip() for item in raw.split(",") if item.strip()}


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data and model artifact locations
DATA_PATH = Path(os.getenv("DATA_PATH", str(PROJECT_ROOT / "data" / "data.csv")))
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(Path(__file__).resolve().parent / "delay_model.pkl")))
BOOTSTRAP_MODEL_ON_STARTUP = _get_bool("BOOTSTRAP_MODEL_ON_STARTUP", True)

# Domain validation tunables
ALLOWED_TIPOVUELO = _get_csv_set("ALLOWED_TIPOVUELO", "I,N")
MIN_VALID_MONTH = _get_int("MIN_VALID_MONTH", 1)
MAX_VALID_MONTH = _get_int("MAX_VALID_MONTH", 12)

# Uvicorn runtime tunables (Part II/III readiness)
UVICORN_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")
UVICORN_PORT = _get_int("UVICORN_PORT", 8000)
UVICORN_WORKERS = _get_int("UVICORN_WORKERS", max(1, (os.cpu_count() or 1)))
UVICORN_BACKLOG = _get_int("UVICORN_BACKLOG", 2048)
UVICORN_TIMEOUT_KEEP_ALIVE = _get_int("UVICORN_TIMEOUT_KEEP_ALIVE", 5)
UVICORN_LIMIT_CONCURRENCY = _get_optional_int("UVICORN_LIMIT_CONCURRENCY")
UVICORN_LOG_LEVEL = os.getenv("UVICORN_LOG_LEVEL", "info")
