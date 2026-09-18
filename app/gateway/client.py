import os
import time
import asyncio

from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()


# =========================================================
# OPENROUTER API KEY
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set.")


# =========================================================
# OPENROUTER CLIENT
# =========================================================

client = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


# =========================================================
# MODEL
# =========================================================

MODEL = "openrouter/free"


# =========================================================
# GENERATE RESPONSE
# =========================================================

async def generate(
    prompt: str,
    model: str = MODEL,
):
    if model == "fast":
        model = "openrouter/free"

    start_time = time.perf_counter()

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    latency = time.perf_counter() - start_time

    usage = response.usage

    return {
        "response": response.choices[0].message.content,
        "provider": "OpenRouter",
        "model": response.model or model,
        "latency": round(latency, 3),
        "usage": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        },
    }


# =========================================================
# TEST
# =========================================================

async def main():

    print("OPENROUTER AI GATEWAY TEST")
    print("=" * 50)

    result = await generate(
        "Explain MCP in simple words in 3 sentences."
    )

    print("\nPROVIDER:")
    print(result["provider"])

    print("\nMODEL:")
    print(result["model"])

    print("\nRESPONSE:")
    print(result["response"])

    print("\nUSAGE:")
    print(result["usage"])

    print("\nLATENCY:")
    print(f"{result['latency']} seconds")


if __name__ == "__main__":
    asyncio.run(main())