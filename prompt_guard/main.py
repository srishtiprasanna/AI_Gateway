from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import re
import time

load_dotenv()

app = FastAPI(title="AI Gateway - Prompt Guard")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "openai/gpt-oss-20b"

MAX_PROMPT_LENGTH = 1000

BLOCKED_PATTERNS = [
    r"ignore all previous instructions",
    r"ignore previous instructions",
    r"reveal the system prompt",
    r"show me the system prompt",
    r"disregard all previous instructions",
]

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{20,}",
    r"gsk_[a-zA-Z0-9]{20,}",
    r"ghp_[a-zA-Z0-9]{20,}",
]


class ChatRequest(BaseModel):
    message: str


def check_prompt(message: str):
    # Check empty prompt
    if not message.strip():
        return False, "Prompt cannot be empty"

    # Check prompt length
    if len(message) > MAX_PROMPT_LENGTH:
        return False, "Prompt is too long"

    # Check prompt injection patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return False, "Potential prompt injection detected"

    # Check for API keys or secrets
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, message):
            return False, "Potential secret or API key detected"

    return True, "Prompt allowed"


@app.get("/")
def home():
    return {
        "message": "Prompt Guard Gateway is running"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    # Step 1: Check the prompt before calling the model
    allowed, reason = check_prompt(request.message)

    if not allowed:
        return {
            "allowed": False,
            "reason": reason,
            "model_called": False
        }

    # Step 2: Call the model only if the prompt is allowed
    start_time = time.time()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": request.message
            }
        ]
    )

    answer = response.choices[0].message.content
    latency = round(time.time() - start_time, 3)

    return {
        "allowed": True,
        "reason": reason,
        "response": answer,
        "model_called": True,
        "model_used": MODEL,
        "latency": latency
    }