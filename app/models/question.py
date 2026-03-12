from pydantic import BaseModel, Field
from typing import Optional


class Question(BaseModel):
    """Schema for a GRE-style question stored in MongoDB."""
    question_text: str = Field(..., description="The question prompt")
    options: list[str] = Field(..., min_length=2, description="Answer options")
    correct_answer: str = Field(..., description="The correct answer text")
    difficulty: float = Field(..., ge=0.1, le=1.0, description="Difficulty from 0.1 (easy) to 1.0 (hard)")
    topic: str = Field(..., description="Subject area, e.g., Algebra, Vocabulary")
    tags: list[str] = Field(default_factory=list, description="Additional category tags")


class QuestionOut(BaseModel):
    """Question returned to the client (no correct_answer exposed)."""
    id: str = Field(..., description="MongoDB document ID")
    question_text: str
    options: list[str]
    difficulty: float
    topic: str
    tags: list[str]
    question_number: Optional[int] = Field(None, description="Current question number in the session")
    total_questions: Optional[int] = Field(None, description="Total questions in the test")
