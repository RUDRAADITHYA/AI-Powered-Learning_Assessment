"""User authentication and profile models."""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Request body for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: Optional[str] = Field(None, description="User's full name")


class UserLogin(BaseModel):
    """Request body for user login."""
    username: str
    password: str


class UserInDB(BaseModel):
    """User document as stored in MongoDB."""
    username: str
    email: str
    hashed_password: str
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class UserResponse(BaseModel):
    """User data returned to frontend (no password)."""
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime


class LoginResponse(BaseModel):
    """Response after successful login."""
    message: str
    username: str
    token: str  # Simple token for session management


class TestHistoryItem(BaseModel):
    """Single test attempt in user's history."""
    test_id: str
    subject: str
    level: str
    num_questions: int
    score: int
    total_questions: int
    percentage: float
    final_ability: float
    proficiency_level: str  # PRO, AVERAGE, WEAK
    completed_at: datetime
    study_plan: Optional[str] = None
