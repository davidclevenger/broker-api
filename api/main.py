import logging
from rich.logging import RichHandler
import copy
import uvicorn

from fastapi import FastAPI, Response, status

import globals
from router import router

FORMAT = "%(message)s"
logging.basicConfig(
    level="DEBUG", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="broker-api",
    description="An abstracting API for interacting with various brokerages (ETrade, Robinhood, etc.)"
)
app.include_router(router)

@app.get("/health")
def health(resp: Response):
    resp.status_code = status.HTTP_200_OK
    return resp

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
