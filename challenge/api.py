import pandas as pd
from fastapi import FastAPI, HTTPException, status

from challenge.schema import PredictRequest
from challenge.utils import bootstrap_model, load_allowed_operators, validate_flights


app = FastAPI()


def _ensure_runtime_state() -> None:
    # Some test runners may invoke endpoints without triggering startup hooks.
    if not hasattr(app.state, "valid_operators"):
        app.state.valid_operators = load_allowed_operators()
    if not hasattr(app.state, "model"):
        app.state.model = bootstrap_model()


@app.on_event("startup")
def _startup() -> None:
    _ensure_runtime_state()


@app.get("/health", status_code=status.HTTP_200_OK)
async def get_health() -> dict:
    return {"status": "OK"}


@app.post("/predict", status_code=status.HTTP_200_OK)
async def post_predict(request: PredictRequest) -> dict:
    _ensure_runtime_state()
    flight_payloads = [flight.dict() for flight in request.flights]
    validate_flights(flight_payloads, app.state.valid_operators)
    flights_df = pd.DataFrame(flight_payloads)
    features = app.state.model.preprocess(data=flights_df)

    try:
        predictions = app.state.model.predict(features=features)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    return {"predict": predictions}