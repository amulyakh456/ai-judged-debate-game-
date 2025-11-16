from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .endpoints import router

app = FastAPI(
    title="AI Debate Judge - Backend Orchestrator",
    description="Manages debate rooms, users, and orchestrates STT and LLM services.",
    version="1.0.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routes ---
app.include_router(router)

# --- Root Endpoint ---
@app.get("/")
async def root():
    return {"message": "AI Debate Judge Backend is running."}
