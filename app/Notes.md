# AI Gateway - Hands-on

This is a hands-on I did to understand how an AI Gateway works.

Instead of an application directly calling an AI model, I created a gateway in between.

The basic flow is:

Client → AI Gateway → AI Provider

The gateway receives the request, decides which model/provider to use, handles errors, and sends the response back to the client.

---

## What I Used

- Python
- FastAPI
- OpenAI Python SDK
- Groq
- OpenRouter
- Pydantic
- python-dotenv

---

## What I Built

I started with a basic AI Gateway and gradually added different features to make it more reliable and useful.

The features I implemented are:

1. Basic AI Gateway
2. Model aliases
3. Multiple AI providers
4. API key authentication
5. Retry handling
6. Fallback handling
7. Token usage tracking
8. Request logging
9. Latency tracking
10. Rate limiting
11. Health check and model endpoints

---

## 1. Basic AI Gateway

I first created a simple FastAPI application with a `/chat` endpoint.

The client can send a message like:

    {
      "message": "What is MCP?",
      "model": "fast"
    }

The gateway receives the request and sends the message to the selected AI provider.

The response is then returned to the client.

---

## 2. Model Aliases

Instead of making the client know the actual model names, I created simple aliases.

For example:

    fast      → Groq → GPT-OSS 20B
    powerful  → Groq → GPT-OSS 120B
    backup    → OpenRouter → Free model router

So the client only needs to send:

    {
      "message": "Hello",
      "model": "fast"
    }

The gateway internally decides which actual model should be called.

I also created a `/models` endpoint to see the available models.

---

## 3. Multiple AI Providers

I wanted the gateway to work with more than one AI service.

I used:

- Groq as the primary provider
- OpenRouter as the backup provider

The client does not need to know how each provider works.

The gateway handles the provider communication.

    Client
       ↓
    AI Gateway
       ↓
    ┌───────────────┐
    │               │
    Groq        OpenRouter
    │               │
    └───────────────┘

---

## 4. API Key Authentication

I added API key authentication to protect the gateway.

The gateway expects an `X-API-Key` header.

For example:

    X-API-Key: my-gateway-key

If the API key is missing:

    401 - Missing API key

If the API key is incorrect:

    401 - Invalid API key

The gateway key is stored in the `.env` file instead of directly inside the Python code.

The `.env` file is also added to `.gitignore` so that API keys are not pushed to GitHub.

---

## 5. Retry Handling

AI providers can sometimes fail temporarily.

For example:

- Rate limits
- Server errors
- Connection problems
- Timeouts

I added retry handling for these types of errors.

The gateway can try the primary provider up to 3 times.

The basic flow is:

    Request
       ↓
    Try 1 → Failed
       ↓
    Try 2 → Failed
       ↓
    Try 3 → Failed
       ↓
    Fallback

I also added a check so that errors that are likely to be temporary can be retried.

---

## 6. Fallback

If the primary provider fails, the gateway switches to the backup provider.

For example:

    Client
       ↓
    AI Gateway
       ↓
    Groq ❌
       ↓
    OpenRouter ✅
       ↓
    Response

I tested this by temporarily changing the Groq model to an invalid model.

The gateway detected the error and switched to OpenRouter.

The response showed:

    "fallback": true

Even if the primary AI provider fails, the application can still receive a response from another provider.

---

## 7. Token Usage Tracking

The gateway also returns token usage from the AI provider.

For example:

    "usage": {
        "prompt_tokens": 91,
        "completion_tokens": 132,
        "total_tokens": 223
    }

This tells me how many tokens were used for the request.

This can be useful for monitoring usage and estimating AI costs.

---

## 8. Request Logging

I added logging to understand what is happening inside the gateway.

The gateway logs things such as:

- Request received
- Provider errors
- Successful requests
- Fallback events
- Selected model
- Provider
- Request latency

This makes it easier to understand and debug what is happening inside the gateway.

---

## 9. Latency Tracking

I added latency tracking to measure how long a request takes.

For example:

    "latency_seconds": 1.242

This tells me approximately how long the complete request took.

This can be useful for monitoring the performance of the gateway and the AI provider.

---

## 10. Rate Limiting

I added a basic rate limiter to prevent too many requests from being sent to the gateway.

Currently the limit is:

    10 requests per 60 seconds

for each gateway API key.

If the limit is exceeded, the gateway returns:

    429 - Rate limit exceeded

I tested this by sending multiple requests automatically from PowerShell.

The gateway successfully blocked requests after the limit was reached.

---

## 11. Health Check

I added a `/health` endpoint.

Calling:

    GET /health

returns:

    {
      "status": "healthy"
    }

This provides a simple way to check whether the gateway is running.

---

# API Endpoints

## GET /

Checks whether the gateway is running.

Example response:

    {
      "message": "AI Gateway is running"
    }

---

## GET /health

Checks the health of the gateway.

Example response:

    {
      "status": "healthy"
    }

---

## GET /models

Returns the models and providers available through the gateway.

Example:

    {
      "available_models": {
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
    }

---

## POST /chat

Sends a message to an AI model through the gateway.

Example request:

    {
      "message": "Explain MCP in simple terms.",
      "model": "fast"
    }

Example response:

    {
      "model": "fast",
      "provider": "groq",
      "response": "AI response...",
      "usage": {
        "prompt_tokens": 91,
        "completion_tokens": 132,
        "total_tokens": 223
      },
      "fallback": false,
      "attempts": 1,
      "latency_seconds": 0.706
    }

---

# Overall Architecture

The final flow of the project is:

    Client
       ↓
    API Key Authentication
       ↓
    Rate Limiting
       ↓
    Model Selection
       ↓
    AI Gateway
       ↓
    ┌─────────────────────────────┐
    │                             │
    │  Groq                       │
    │  ├── GPT-OSS 20B            │
    │  └── GPT-OSS 120B           │
    │                             │
    │  OpenRouter                 │
    │  └── Backup                 │
    │                             │
    └─────────────────────────────┘
       ↓
    Retry / Error Handling
       ↓
    Fallback if required
       ↓
    Token Usage
       ↓
    Logging
       ↓
    Latency Tracking
       ↓
    Response

The gateway acts as a single entry point for AI requests.

---

# What I Learned

Through this hands-on project, I learned the basic idea of an AI Gateway and how it can act as a middle layer between an application and AI providers.

I learned how to:

- Build a basic FastAPI gateway
- Connect the gateway to an LLM
- Use model aliases
- Route requests to different models
- Work with multiple AI providers
- Protect an API using an API key
- Handle provider errors
- Implement retry logic
- Implement fallback between providers
- Track token usage
- Add request logging
- Track request latency
- Add rate limiting
- Create health and model endpoints