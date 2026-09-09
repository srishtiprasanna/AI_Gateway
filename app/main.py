import logging
import os
import time
from collections import defaultdict, deque
from time import perf_counter

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from openai import OpenAI
from pydantic import BaseModel


# --------------------------------------------------
# Environment
# --------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY")


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ai_gateway")


# --------------------------------------------------
# Clients
# --------------------------------------------------

groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


# --------------------------------------------------
# FastAPI
# --------------------------------------------------

app = FastAPI(title="AI Gateway")


# --------------------------------------------------
# Model / Provider Configuration
# --------------------------------------------------

AVAILABLE_MODELS = {
    "fast": {
        "provider": "groq",
        "model": "openai/gpt-oss-20b"
    },
    "powerful": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b"
    },
    "backup": {
        "provider": "openrouter",
        "model": "openrouter/free"
    }
}


# --------------------------------------------------
# Rate Limiting
# --------------------------------------------------

RATE_LIMIT = 10
RATE_WINDOW = 60

request_history = defaultdict(deque)


def check_rate_limit(api_key: str):
    current_time = time.time()

    requests = request_history[api_key]

    # Remove requests older than the current window
    while requests and current_time - requests[0] > RATE_WINDOW:
        requests.popleft()

    if len(requests) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )

    requests.append(current_time)


# --------------------------------------------------
# Request Model
# --------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    model: str = "fast"


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def authenticate(api_key: str | None):
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    if not GATEWAY_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gateway API key is not configured"
        )

    if api_key != GATEWAY_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )


def get_client(provider: str):
    if provider == "groq":
        return groq_client

    if provider == "openrouter":
        return openrouter_client

    raise ValueError(f"Unsupported provider: {provider}")


def is_retryable_error(error: Exception) -> bool:
    error_message = str(error)

    retryable_errors = [
        "429",
        "500",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "connection"
    ]

    return any(
        error_code.lower() in error_message.lower()
        for error_code in retryable_errors
    )


def call_provider(
    provider: str,
    model: str,
    message: str
):
    client = get_client(provider)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": message
            }
        ]
    )

    usage = None

    if response.usage:
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

    return {
        "response": response.choices[0].message.content,
        "usage": usage
    }


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "AI Gateway is running"
    }


@app.get("/models")
def get_models():
    return {
        "available_models": {
            name: {
                "provider": config["provider"],
                "model": config["model"]
            }
            for name, config in AVAILABLE_MODELS.items()
        }
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(
    request: ChatRequest,
    x_api_key: str | None = Header(default=None)
):

    # ----------------------------------------------
    # Authentication
    # ----------------------------------------------

    authenticate(x_api_key)

    # ----------------------------------------------
    # Rate limiting
    # ----------------------------------------------

    check_rate_limit(x_api_key)

    # ----------------------------------------------
    # Validate model
    # ----------------------------------------------

    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model}' is not available"
        )

    selected = AVAILABLE_MODELS[request.model]

    provider = selected["provider"]
    provider_model = selected["model"]

    start_time = perf_counter()

    logger.info(
        "Request received | model=%s | provider=%s | provider_model=%s",
        request.model,
        provider,
        provider_model
    )

    # ----------------------------------------------
    # Primary provider
    # ----------------------------------------------

    last_error = None

    for attempt in range(3):

        try:

            result = call_provider(
                provider=provider,
                model=provider_model,
                message=request.message
            )

            latency = round(
                perf_counter() - start_time,
                3
            )

            logger.info(
                "Request successful | model=%s | provider=%s | latency=%ss",
                request.model,
                provider,
                latency
            )

            return {
                "model": request.model,
                "provider": provider,
                "response": result["response"],
                "usage": result["usage"],
                "fallback": False,
                "attempts": attempt + 1,
                "latency_seconds": latency
            }

        except Exception as e:

            last_error = e

            logger.warning(
                "Provider error | attempt=%s | provider=%s | error=%s",
                attempt + 1,
                provider,
                str(e)
            )

            # Don't retry permanent errors
            if not is_retryable_error(e):
                break

            # Don't sleep after the final attempt
            if attempt < 2:
                time.sleep(1)

    # ----------------------------------------------
    # Fallback provider
    # ----------------------------------------------

    fallback = AVAILABLE_MODELS["backup"]

    logger.warning(
        "Primary provider failed | switching to fallback | provider=%s",
        fallback["provider"]
    )

    try:

        result = call_provider(
            provider=fallback["provider"],
            model=fallback["model"],
            message=request.message
        )

        latency = round(
            perf_counter() - start_time,
            3
        )

        logger.info(
            "Fallback successful | provider=%s | latency=%ss",
            fallback["provider"],
            latency
        )

        return {
            "model": "backup",
            "provider": fallback["provider"],
            "response": result["response"],
            "usage": result["usage"],
            "fallback": True,
            "primary_error": str(last_error),
            "latency_seconds": latency
        }

    except Exception as fallback_error:

        logger.error(
            "Primary and fallback providers failed | primary=%s | fallback=%s",
            str(last_error),
            str(fallback_error)
        )

        raise HTTPException(
            status_code=502,
            detail={
                "message": "Primary and fallback providers failed",
                "primary_error": str(last_error),
                "fallback_error": str(fallback_error)
            }
        )