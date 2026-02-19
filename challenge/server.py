import uvicorn

from challenge.utils import get_uvicorn_config


def run() -> None:
    uvicorn.run("challenge.api:app", **get_uvicorn_config())


if __name__ == "__main__":
    run()
