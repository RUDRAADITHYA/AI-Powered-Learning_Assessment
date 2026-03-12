"""
AI-Driven Adaptive Diagnostic Engine — FastAPI Application

An adaptive testing system with:
- User authentication (MongoDB)
- AI-generated questions (Groq LLM)
- Dynamic test configuration (subject, level, num questions)
- IRT-based ability tracking
- Personalized study plans
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import connect_to_mongo, close_mongo_connection
from app.routers import diagnostic, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    print("✓ Ready to accept requests")
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="AI-Driven Adaptive Diagnostic Engine",
    description=(
        "An adaptive testing platform with AI-generated questions, "
        "user authentication, and personalized study recommendations. "
        "Questions are generated dynamically based on subject, level, and count."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(diagnostic.router)


@app.get("/", tags=["Health"])
async def root():
    """Serve the frontend UI."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "Adaptive Diagnostic Engine",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "history": "GET /auth/history/{username}",
            "start_test": "POST /diagnostic/start",
            "get_question": "GET /diagnostic/question?session_id=<id>",
            "submit_answer": "POST /diagnostic/answer",
            "get_summary": "GET /diagnostic/summary?session_id=<id>",
        },
    }
