## Model Selection Decision

From the experiments in `exploration.ipynb`, we kept **Logistic Regression** with the **top 10 features** and **class balancing**.

### Why this model

1. The notebook shows no meaningful gap versus XGBoost, so we preferred the simpler option.
2. Logistic Regression is easier to explain (clear coefficients and feature impact).
3. Inference is very fast, which matters for a real-time prediction API.
4. It is lightweight in memory and disk footprint.
5. It keeps production dependencies simpler (`scikit-learn` only in `requirements.txt`).

## Model Lifecycle Decision (Part I)

To make the model usable in production-like scenarios, we persist the last trained artifact and load it on `DelayModel` initialization.

### Why we did it

1. Faster startup: if the artifact exists, predictions are available immediately.
2. More consistent behavior across local runs, tests, and API startup.
3. Clear separation between training and inference concerns.
4. Safer failure mode: `predict()` raises a clear error if no model is available.

### What was implemented

- `fit()` trains `LogisticRegression` and saves the artifact.
- `__init__()` tries to load the artifact.
- `predict()` uses the loaded/trained model, or raises an explicit error.

## Test Reliability Update

We changed `tests/model/test_model.py` to read the dataset from `settings.DATA_PATH` instead of `../data/data.csv`.

### Why this matters

1. Relative paths depend on the current working directory and can break in CI.
2. `settings.DATA_PATH` is already the canonical project setting for data location.
3. This fixes the root cause without touching `Makefile` or adding test-only hacks.

## Part II - API Design Decisions

The API design focuses on stability, clarity, and predictable behavior.

### Main decisions

1. Single model instance reused through `app.state`.
2. Startup bootstrap: load persisted model first; if not found (and enabled), train once from `data/data.csv`.
3. Strict input validation for `OPERA`, `TIPOVUELO`, and `MES` (HTTP `400` on invalid values).
4. Explicit service-state error (HTTP `503`) when no model is available for prediction.
5. Modular structure:
   - `api.py`: endpoint flow
   - `schema.py`: request models
   - `utils.py`: bootstrap/validation/runtime helpers
   - `settings.py`: env configuration
6. High-load readiness via `server.py` (worker and concurrency tuning through env vars).
7. Test compatibility:
   - lazy runtime-state init when startup hooks are not executed by tests
   - `anyio<4` pin for FastAPI/Starlette compatibility in this stack

### Suggested command for load tests

```bash
UVICORN_WORKERS=4 UVICORN_LIMIT_CONCURRENCY=1000 UVICORN_BACKLOG=2048 ./.venv/bin/python -m challenge.server
```

Tune those values per CPU/memory profile.

### API entrypoint clarification

- Canonical ASGI app: `challenge.api:app`.
- `challenge/server.py` is only a runtime wrapper around Uvicorn; it does not define a second API.
- This keeps compatibility with evaluators that import `challenge.app` or run `uvicorn challenge.api:app`.

## Part III - Cloud Deployment (GCP Cloud Run)

We selected **Google Cloud Run** because it matches this service profile well.

### Why Cloud Run

1. Autoscaling from 0 based on traffic.
2. Pay only when handling requests.
3. Native fit for our Dockerized service.
4. Straightforward port compatibility (`8080` via `UVICORN_PORT`).

### Docker choices

- Base image: `python:3.10-slim`.
- Runtime env: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`.
- Smaller image: `pip --no-cache-dir`.
- Entrypoint: `python -m challenge.server` for tunable Uvicorn runtime.

### Stress test result (Cloud Run)

With `cpu=2`, `max-instances=10`, `concurrency=20`, `memory=1Gi`, and `timeout=120`, `make stress-test` finished successfully (`exit code 0`):

- Requests: `6931`
- Failures: `0 (0.00%)`
- Throughput: `115.70 req/s`
- Average latency: `260 ms`
- P95 latency: `270 ms`
- P99 latency: `450 ms`

The service stayed stable for the challenge load profile.

## Part IV - CI/CD Decisions

We added GitHub Actions workflows so testing and deployment are consistent and repeatable.

### Why CI is configured this way

1. `make model-test` + `make api-test` on `push`/`pull_request` to `main` catches regressions early.
2. `ubuntu-latest` + Python 3.10 + `make install` gives a predictable environment.
3. Uploading `reports/` helps debug failed runs quickly.

### Why CD is configured this way

1. Workload Identity Federation avoids long-lived service account keys.
2. Image tags with `GITHUB_SHA` + `latest` provide traceability and operational convenience.
3. Build from the repo Dockerfile and deploy to Cloud Run keeps runtime parity.
4. Trigger on `push` to `main` plus manual `workflow_dispatch` gives controlled automation.

## Challenge Package Layout

```text
challenge/
├── __init__.py
├── api.py
├── model.py
├── schema.py
├── server.py
├── settings.py
├── utils.py
└── delay_model.pkl
```

- `__init__.py`: package entrypoint, exposes the ASGI app.
- `api.py`: FastAPI endpoints (`/health`, `/predict`) and request flow.
- `model.py`: preprocessing, training, persistence, prediction.
- `schema.py`: Pydantic request models.
- `server.py`: Uvicorn launcher with env-driven settings.
- `settings.py`: centralized environment configuration.
- `utils.py`: shared helpers for validation/bootstrap/runtime.
- `delay_model.pkl`: latest trained model artifact.
