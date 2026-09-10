# FastAPI Middleware - Hands-on

Today I explored FastAPI middleware and how it can be used in an AI Gateway.

## What is Middleware?

Middleware is a layer that runs when a request comes into the application.

It can process something before the request reaches the endpoint and also do something after the endpoint finishes.

The flow is:

Client
↓
Middleware
↓
API Endpoint
↓
Response
↓
Middleware
↓
Client

## What I Implemented

I created a request logging middleware that tracks:

- HTTP method
- Request path
- Response status code
- Request latency
- Errors

The middleware is applied to all the endpoints in the application.

## Testing

I tested the following endpoints:

- `/`
- `/health`
- `/users`
- `/slow`
- `/error`

I used the `/slow` endpoint to test latency tracking.

The endpoint intentionally waits for 2 seconds, and the middleware records the request latency in the terminal.

## Example Log

    Request received | method=GET | path=/slow
    Request completed | method=GET | path=/slow | status=200 | latency=2.xxxs

## What I Learned

I understood that middleware is useful when I want the same functionality to apply to multiple endpoints.

For an AI Gateway, middleware can be useful for:

- Request logging
- Monitoring
- Authentication
- Rate limiting
- Measuring latency
- Error handling

Instead of writing the same logic inside every endpoint, middleware allows this functionality to be handled in one place.