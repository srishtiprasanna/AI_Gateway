import logging
import time
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("middleware_demo")


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(title="AI Gateway - Middleware Hands-on")


# --------------------------------------------------
# Request Logging Middleware
# --------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):

    start_time = perf_counter()

    logger.info(
        "Request received | method=%s | path=%s",
        request.method,
        request.url.path
    )

    try:
        response = await call_next(request)

        latency = round(
            perf_counter() - start_time,
            3
        )

        logger.info(
            "Request completed | method=%s | path=%s | status=%s | latency=%ss",
            request.method,
            request.url.path,
            response.status_code,
            latency
        )

        return response

    except Exception as e:

        latency = round(
            perf_counter() - start_time,
            3
        )

        logger.error(
            "Request failed | method=%s | path=%s | latency=%ss | error=%s",
            request.method,
            request.url.path,
            latency,
            str(e)
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error"
            }
        )


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Middleware demo is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/slow")
def slow_endpoint():

    time.sleep(2)

    return {
        "message": "This endpoint intentionally takes 2 seconds"
    }


@app.get("/error")
def error_endpoint():

    raise Exception("This is a test error")


@app.get("/users")
def users():

    return {
        "users": [
            {
                "id": 1,
                "name": "Alice"
            },
            {
                "id": 2,
                "name": "Bob"
            }
        ]
    }