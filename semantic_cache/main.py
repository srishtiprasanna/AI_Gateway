from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import os
import time
import numpy as np

load_dotenv()

app = FastAPI(title="AI Gateway - Semantic Cache")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "openai/gpt-oss-20b"

# Load a small local embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Store previous questions and answers
cache = []

# Similarity threshold
SIMILARITY_THRESHOLD = 0.60


class ChatRequest(BaseModel):
    message: str


def calculate_similarity(vector1, vector2):
    return np.dot(vector1, vector2) / (
        np.linalg.norm(vector1) * np.linalg.norm(vector2)
    )


@app.get("/")
def home():
    return {"message": "Semantic Cache Gateway is running"}


@app.post("/chat")
def chat(request: ChatRequest):

    # Convert the new question into an embedding
    query_embedding = embedding_model.encode(request.message)

    # Check existing cached questions
    for item in cache:

        similarity = calculate_similarity(
            query_embedding,
            item["embedding"]
        )

        if similarity >= SIMILARITY_THRESHOLD:
            return {
                "response": item["response"],
                "cache_hit": True,
                "similarity": round(float(similarity), 3),
                "model_used": MODEL
            }

    # Cache miss - call the LLM
    start_time = time.time()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": request.message}
        ]
    )

    answer = response.choices[0].message.content

    latency = round(time.time() - start_time, 3)

    # Save question, embedding and answer
    cache.append({
        "question": request.message,
        "embedding": query_embedding,
        "response": answer
    })

    return {
        "response": answer,
        "cache_hit": False,
        "similarity": None,
        "model_used": MODEL,
        "latency": latency
    }