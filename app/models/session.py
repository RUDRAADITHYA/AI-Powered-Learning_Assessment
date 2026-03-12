from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ResponseRecord(BaseModel):
    """Single question-response pair within a session."""
    question_id: str
    question_text: str
    topic: str
    difficulty: float
    selected_answer: str
    correct_answer: str
    is_correct: bool
    ability_after: float = Field(..., description="Ability estimate after this response")


class UserSession(BaseModel):
    """Schema for a student's adaptive test session."""
    session_id: str = Field(..., description="Unique session identifier")
    current_ability: float = Field(default=0.5, description="Current estimated ability (theta)")
    responses: list[ResponseRecord] = Field(default_factory=list)
    is_complete: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    study_plan: Optional[str] = Field(None, description="AI-generated study plan")


class StartSessionResponse(BaseModel):
    """Response when a new session is created."""
    session_id: str
    message: str
    initial_ability: float


class SubmitAnswerRequest(BaseModel):
    """Request body to submit an answer."""
    session_id: str
    question_id: str
    selected_answer: str


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    is_correct: bool
    correct_answer: str
    previous_ability: float
    updated_ability: float
    questions_remaining: int
    is_complete: bool


class SessionSummary(BaseModel):
    """Full session summary after test completion."""
    session_id: str
    total_questions: int
    correct_count: int
    incorrect_count: int
    final_ability: float
    difficulty_reached: float
    topics_missed: list[str]
    topics_strong: list[str]
    responses: list[ResponseRecord]
    study_plan: Optional[str] = None
