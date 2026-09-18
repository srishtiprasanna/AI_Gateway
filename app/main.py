from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.research.agent import research


app = FastAPI(
    title="AI Research Agent",
    description="Research agent powered by MCP servers and an AI Gateway.",
    version="1.0.0",
)


# Allow the React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    topic: str


@app.get("/")
async def root():
    return {
        "message": "AI Research Agent is running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/research")
async def start_research(request: ResearchRequest):

    result = await research(request.topic)

    return result