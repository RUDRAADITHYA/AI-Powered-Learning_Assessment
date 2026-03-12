"""
Service layer for question retrieval from MongoDB.
"""
from typing import Optional
from bson import ObjectId
from app.database import get_database
from app.services.adaptive import select_next_difficulty, information_function


async def get_question_by_id(question_id: str) -> Optional[dict]:
    """Fetch a single question by its ObjectId."""
    db = get_database()
    doc = await db.questions.find_one({"_id": ObjectId(question_id)})
    return doc


async def select_next_question(
    current_ability: float,
    answered_ids: list[str],
) -> Optional[dict]:
    """
    Select the most informative unanswered question for the student's current ability.

    Strategy:
      1. Compute the target difficulty (= current ability under Rasch).
      2. Fetch candidate questions within a difficulty window around the target.
      3. Among candidates, pick the one with the highest Fisher Information
         at the student's current ability (maximizes measurement precision).
    """
    db = get_database()
    target = select_next_difficulty(current_ability)

    # Convert answered IDs to ObjectId for exclusion
    exclude_oids = [ObjectId(qid) for qid in answered_ids]

    # Widen search window progressively until we find candidates
    for window in [0.15, 0.25, 0.4, 0.6, 1.0]:
        low = max(0.1, target - window)
        high = min(1.0, target + window)
        query = {
            "difficulty": {"$gte": low, "$lte": high},
            "_id": {"$nin": exclude_oids},
        }
        candidates = await db.questions.find(query).to_list(length=50)
        if candidates:
            break

    if not candidates:
        # Absolute fallback — any unanswered question
        candidates = await db.questions.find(
            {"_id": {"$nin": exclude_oids}}
        ).to_list(length=50)

    if not candidates:
        return None  # No more questions available

    # Rank by Fisher Information (most informative first)
    best = max(
        candidates,
        key=lambda q: information_function(current_ability, q["difficulty"]),
    )
    return best
