from typing import Dict, List, Set

import pandas as pd
from fastapi import HTTPException, status

from challenge import settings
from challenge.model import DelayModel

VALID_TIPOVUELO: Set[str] = settings.ALLOWED_TIPOVUELO
VALID_MONTHS: Set[int] = set(range(settings.MIN_VALID_MONTH, settings.MAX_VALID_MONTH + 1))


def load_allowed_operators() -> Set[str]:
    data = pd.read_csv(settings.DATA_PATH)
    return set(data["OPERA"].dropna().unique().tolist())


def validate_flights(flights: List[Dict[str, object]], valid_operators: Set[str]) -> None:
    for flight in flights:
        opera = str(flight["OPERA"])
        tipovuelo = str(flight["TIPOVUELO"])
        mes = int(flight["MES"])

        if opera not in valid_operators:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown OPERA value: {opera}",
            )
        if tipovuelo not in VALID_TIPOVUELO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown TIPOVUELO value: {tipovuelo}",
            )
        if mes not in VALID_MONTHS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown MES value: {mes}",
            )


def bootstrap_model() -> DelayModel:
    model = DelayModel()
    if model._model is not None or not settings.BOOTSTRAP_MODEL_ON_STARTUP:
        return model

    training_data = pd.read_csv(settings.DATA_PATH)
    features, target = model.preprocess(data=training_data, target_column="delay")
    model.fit(features=features, target=target)
    return model


def get_uvicorn_config() -> Dict[str, object]:
    config: Dict[str, object] = {
        "host": settings.UVICORN_HOST,
        "port": settings.UVICORN_PORT,
        "workers": settings.UVICORN_WORKERS,
        "backlog": settings.UVICORN_BACKLOG,
        "timeout_keep_alive": settings.UVICORN_TIMEOUT_KEEP_ALIVE,
        "log_level": settings.UVICORN_LOG_LEVEL,
    }
    if settings.UVICORN_LIMIT_CONCURRENCY is not None:
        config["limit_concurrency"] = settings.UVICORN_LIMIT_CONCURRENCY
    return config
