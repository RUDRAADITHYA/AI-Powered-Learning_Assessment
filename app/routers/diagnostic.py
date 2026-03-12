"""
Diagnostic test router - AI-powered question generation and adaptive testing.

New Flow:
    POST /start       → Start test with subject, level, num_questions (generates AI questions)
    GET  /question    → Get current question
    POST /answer      → Submit answer
    GET  /summary     → Get results + AI study plan
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_database
from app.services.ai_questions import generate_questions, generate_feedback
from app.services.adaptive import update_ability, compute_final_ability

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic Test"])


# ─── Request/Response Models ───────────────────────────────────

class StartTestRequest(BaseModel):
    username: str = Field(..., description="Logged-in username")
    subject: str = Field(..., description="Subject (e.g., Math, Science, Programming)")
    level: str = Field(..., description="Difficulty: easy, medium, or hard")
    num_questions: int = Field(..., ge=3, le=20, description="Number of questions (3-20)")


class StartTestResponse(BaseModel):
    session_id: str
    message: str
    subject: str
    level: str
    num_questions: int
    first_question: dict


class QuestionResponse(BaseModel):
    question_id: str
    question_text: str
    options: list[str]
    question_number: int
    total_questions: int
    topic: str
    difficulty: float


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str
    previous_ability: float
    updated_ability: float
    questions_remaining: int
    is_complete: bool
    next_question: Optional[dict] = None


class TestSummary(BaseModel):
    session_id: str
    username: str
    subject: str
    level: str
    total_questions: int
    correct_count: int
    incorrect_count: int
    percentage: float
    final_ability: float
    proficiency: str  # PRO, AVERAGE, WEAK
    responses: list
    study_plan: str


# ─── Helper Functions ──────────────────────────────────────────

def get_proficiency(correct_count: int, total: int, ability: float) -> str:
    """Determine proficiency level based on score and ability."""
    pct = (correct_count / total * 100) if total > 0 else 0
    if pct >= 80 and ability >= 0.7:
        return "PRO"
    elif pct >= 50 and ability >= 0.4:
        return "AVERAGE"
    else:
        return "WEAK"


# ─── Endpoints ─────────────────────────────────────────────────

@router.post("/start", response_model=StartTestResponse)
async def start_test(request: StartTestRequest):
    """
    Start a new test session.
    
    - Validates user exists
    - Generates questions using AI based on subject, level, count
    - Stores session with generated questions
    - Returns first question
    """
    db = get_database()
    
    # Verify user exists
    user = await db.users.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")
    
    # Generate questions using AI
    try:
        questions = await generate_questions(
            subject=request.subject,
            num_questions=request.num_questions,
            difficulty=request.level,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")
    
    if not questions:
        raise HTTPException(status_code=500, detail="AI failed to generate questions. Please try again.")
    
    # Create session
    session_id = str(uuid.uuid4())
    session_doc = {
        "session_id": session_id,
        "username": request.username,
        "subject": request.subject,
        "level": request.level,
        "num_questions": request.num_questions,
        "questions": questions,  # Store AI-generated questions
        "current_question_index": 0,
        "current_ability": 0.5,
        "responses": [],
        "is_complete": False,
        "created_at": datetime.utcnow(),
    }
    
    await db.user_sessions.insert_one(session_doc)
    
    # Return first question
    first_q = questions[0]
    
    return StartTestResponse(
        session_id=session_id,
        message=f"Test started! {request.num_questions} {request.level} questions on {request.subject}",
        subject=request.subject,
        level=request.level,
        num_questions=request.num_questions,
        first_question={
            "question_id": first_q["id"],
            "question_text": first_q["question_text"],
            "options": first_q["options"],
            "question_number": 1,
            "total_questions": request.num_questions,
            "topic": first_q.get("topic", request.subject),
            "difficulty": first_q.get("difficulty", 0.5),
        }
    )


@router.get("/question")
async def get_current_question(session_id: str = Query(...)):
    """Get the current question for a session."""
    db = get_database()
    
    session = await db.user_sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("is_complete"):
        raise HTTPException(status_code=400, detail="Test is complete. Get your summary.")
    
    idx = session["current_question_index"]
    questions = session["questions"]
    
    if idx >= len(questions):
        raise HTTPException(status_code=400, detail="No more questions")
    
    q = questions[idx]
    
    return QuestionResponse(
        question_id=q["id"],
        question_text=q["question_text"],
        options=q["options"],
        question_number=idx + 1,
        total_questions=session["num_questions"],
        topic=q.get("topic", session["subject"]),
        difficulty=q.get("difficulty", 0.5),
    )


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest):
    """
    Submit an answer to the current question.
    
    - Checks correctness
    - Updates ability estimate
    - Returns feedback and next question (if any)
    """
    db = get_database()
    
    session = await db.user_sessions.find_one({"session_id": request.session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("is_complete"):
        raise HTTPException(status_code=400, detail="Test is already complete")
    
    # Find the question
    idx = session["current_question_index"]
    questions = session["questions"]
    
    if idx >= len(questions):
        raise HTTPException(status_code=400, detail="No more questions")
    
    question = questions[idx]
    
    if question["id"] != request.question_id:
        raise HTTPException(status_code=400, detail="Question ID mismatch")
    
    # Check correctness
    is_correct = request.selected_answer.strip() == question["correct_answer"].strip()
    
    # Update ability
    previous_ability = session["current_ability"]
    difficulty = question.get("difficulty", 0.5)
    new_ability = update_ability(previous_ability, difficulty, is_correct)
    
    # Record response
    response_record = {
        "question_id": question["id"],
        "question_text": question["question_text"],
        "topic": question.get("topic", session["subject"]),
        "difficulty": difficulty,
        "selected_answer": request.selected_answer,
        "correct_answer": question["correct_answer"],
        "explanation": question.get("explanation", ""),
        "is_correct": is_correct,
        "ability_after": new_ability,
    }
    
    responses = session.get("responses", [])
    responses.append(response_record)
    
    # Move to next question
    next_idx = idx + 1
    questions_remaining = len(questions) - next_idx
    is_complete = questions_remaining <= 0
    
    # If complete, compute final ability
    final_ability = new_ability
    if is_complete:
        final_ability = compute_final_ability(
            [{"difficulty": r["difficulty"], "is_correct": r["is_correct"]} for r in responses]
        )
        
        # Save to test history
        correct_count = sum(1 for r in responses if r["is_correct"])
        percentage = (correct_count / len(responses)) * 100
        
        history_doc = {
            "test_id": session["session_id"],
            "username": session["username"],
            "subject": session["subject"],
            "level": session["level"],
            "num_questions": session["num_questions"],
            "score": correct_count,
            "percentage": percentage,
            "final_ability": final_ability,
            "proficiency": get_proficiency(correct_count, len(responses), final_ability),
            "completed_at": datetime.utcnow(),
        }
        await db.test_history.insert_one(history_doc)
    
    # Update session
    await db.user_sessions.update_one(
        {"session_id": request.session_id},
        {
            "$set": {
                "current_question_index": next_idx,
                "current_ability": final_ability if is_complete else new_ability,
                "responses": responses,
                "is_complete": is_complete,
            }
        }
    )
    
    # Prepare next question if available
    next_question = None
    if not is_complete:
        next_q = questions[next_idx]
        next_question = {
            "question_id": next_q["id"],
            "question_text": next_q["question_text"],
            "options": next_q["options"],
            "question_number": next_idx + 1,
            "total_questions": session["num_questions"],
            "topic": next_q.get("topic", session["subject"]),
            "difficulty": next_q.get("difficulty", 0.5),
        }
    
    return AnswerResponse(
        is_correct=is_correct,
        correct_answer=question["correct_answer"],
        explanation=question.get("explanation", ""),
        previous_ability=round(previous_ability, 4),
        updated_ability=round(final_ability if is_complete else new_ability, 4),
        questions_remaining=questions_remaining,
        is_complete=is_complete,
        next_question=next_question,
    )


@router.get("/summary", response_model=TestSummary)
async def get_test_summary(session_id: str = Query(...)):
    """Get the complete test summary with AI-generated study plan."""
    db = get_database()
    
    session = await db.user_sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.get("is_complete"):
        raise HTTPException(status_code=400, detail="Test is not complete yet")
    
    responses = session["responses"]
    correct_count = sum(1 for r in responses if r["is_correct"])
    incorrect_count = len(responses) - correct_count
    percentage = (correct_count / len(responses)) * 100 if responses else 0
    final_ability = session["current_ability"]
    
    proficiency = get_proficiency(correct_count, len(responses), final_ability)
    
    # Get weak and strong topics
    topics_weak = list({r["topic"] for r in responses if not r["is_correct"]})
    topics_strong = list({r["topic"] for r in responses if r["is_correct"]})
    
    # Generate study plan if not cached
    study_plan = session.get("study_plan")
    if not study_plan:
        try:
            study_plan = await generate_feedback(
                correct_count=correct_count,
                total_questions=len(responses),
                topics_weak=topics_weak,
                topics_strong=topics_strong,
                difficulty=session["level"],
                subject=session["subject"],
            )
            # Cache it
            await db.user_sessions.update_one(
                {"session_id": session_id},
                {"$set": {"study_plan": study_plan}}
            )
        except Exception as e:
            study_plan = f"Study plan unavailable: {str(e)}"
    
    return TestSummary(
        session_id=session_id,
        username=session["username"],
        subject=session["subject"],
        level=session["level"],
        total_questions=len(responses),
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        percentage=round(percentage, 1),
        final_ability=round(final_ability, 4),
        proficiency=proficiency,
        responses=responses,
        study_plan=study_plan,
    )
