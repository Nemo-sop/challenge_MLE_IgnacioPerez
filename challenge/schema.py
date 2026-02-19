from typing import List

from pydantic import BaseModel


class FlightInput(BaseModel):
    OPERA: str
    TIPOVUELO: str
    MES: int


class PredictRequest(BaseModel):
    flights: List[FlightInput]
