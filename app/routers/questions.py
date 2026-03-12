"""
Questions admin router — browse and manage the question bank.
"""
from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId

from app.database import get_database
from app.models.question import Question, QuestionOut
from app.seed import seed_questions

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("/", response_model=list[QuestionOut])
async def list_questions(
    topic: str | None = Query(None, description="Filter by topic"),
    min_difficulty: float = Query(0.1, ge=0.1, le=1.0),
    max_difficulty: float = Query(1.0, ge=0.1, le=1.0),
):
    """List all questions, optionally filtered by topic and difficulty range."""
    db = get_database()
    query: dict = {"difficulty": {"$gte": min_difficulty, "$lte": max_difficulty}}
    if topic:
        query["topic"] = topic

    docs = await db.questions.find(query).sort("difficulty", 1).to_list(length=100)
    return [
        QuestionOut(
            id=str(doc["_id"]),
            question_text=doc["question_text"],
            options=doc["options"],
            difficulty=doc["difficulty"],
            topic=doc["topic"],
            tags=doc["tags"],
        )
        for doc in docs
    ]


@router.post("/seed")
async def seed():
    """Seed the database with GRE-style questions (idempotent)."""
    count = await seed_questions()
    if count == 0:
        return {"message": "Questions already seeded", "count": 0}
    return {"message": f"Successfully seeded {count} questions", "count": count}


@router.get("/topics")
async def list_topics():
    """Get all distinct question topics."""
    db = get_database()
    topics = await db.questions.distinct("topic")
    return {"topics": topics}
