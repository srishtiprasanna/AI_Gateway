# Prompt Guard

## What I learned

In this hands-on, I learned how an AI Gateway can act as a **security layer** between a user and an AI model.

Instead of sending every request directly to the AI model, the gateway can first check the request and decide whether it should be allowed or blocked.

This can help prevent unwanted or suspicious requests from reaching the LLM.

---

## What I built

I created a small **Prompt Guard Gateway** using:

- Python
- FastAPI
- Groq
- OpenAI-compatible API
- Regular expressions

The gateway checks a user's prompt before calling the AI model.

If the prompt passes the checks, it is sent to the model.

If the prompt fails a check, the request is blocked and the model is not called.

---

## How it works

The basic flow is:

    User Request
         ↓
    Prompt Guard
         ↓
    Is the request allowed?
       ↙       ↘
     Yes        No
      ↓          ↓
     Groq      Block
      ↓
    Response

The gateway first checks the request.

Only allowed requests are sent to the AI model.

---

## Checks I added

### 1. Empty Prompt

The gateway checks whether the user has sent an empty message.

For example:

    {
      "message": ""
    }

This request is blocked.

---

### 2. Prompt Length

I set a maximum prompt length of:

    1000 characters

If a prompt is longer than this limit, the gateway blocks it.

This is a simple way to prevent unnecessarily large requests from reaching the model.

---

### 3. Prompt Injection Detection

I added checks for some common prompt injection phrases.

For example:

    Ignore all previous instructions

    Ignore previous instructions

    Reveal the system prompt

    Show me the system prompt

    Disregard all previous instructions

If one of these patterns is detected, the gateway blocks the request.

---

### 4. Secret Detection

I also added simple pattern checks for some common API key formats.

The purpose is to detect cases where a user may accidentally send a secret or API key as part of a prompt.

This is only a basic demonstration and is not a complete secret detection system.

---

## Allowed Request vs Blocked Request

### Allowed Request

    User
      ↓
    Prompt Guard
      ↓
    Allowed
      ↓
    AI Model
      ↓
    Response

### Blocked Request

    User
      ↓
    Prompt Guard
      ↓
    Blocked
      ↓
    No AI Model Call

This shows that the gateway can make a decision before the request reaches the LLM.

---

## Why Prompt Guard is Useful

An AI Gateway can provide an additional security layer for AI applications.

Prompt Guard can help with:

- Blocking suspicious prompts
- Detecting simple prompt injection attempts
- Preventing empty requests
- Limiting very large prompts
- Detecting some common secret or API key patterns
- Avoiding unnecessary model calls for blocked requests

---

## Important Note

This is a simple learning implementation.

The prompt injection detection is based on predefined patterns.

This means it cannot detect every possible prompt injection technique.

The secret detection is also basic and only checks for a few common key formats.

A production AI Gateway would need more advanced security controls such as:

- Better prompt injection detection
- Content moderation
- Secret and sensitive-data detection
- Authentication
- Rate limiting
- Logging and monitoring
- Request validation
- Security policies
