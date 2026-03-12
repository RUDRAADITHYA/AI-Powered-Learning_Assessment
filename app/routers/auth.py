"""
User authentication router - registration, login, and profile management.
"""
import uuid
import hashlib
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.database import get_database


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Request/Response Models ───────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserResponse] = None


class TestHistoryItem(BaseModel):
    test_id: str
    subject: str
    level: str
    num_questions: int
    score: int
    percentage: float
    proficiency: str
    completed_at: datetime


# ─── Helper Functions ──────────────────────────────────────────

def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def generate_token(username: str) -> str:
    """Generate a simple session token."""
    return f"{username}_{uuid.uuid4().hex}"


# ─── Endpoints ─────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user account."""
    db = get_database()
    
    # Check if username already exists
    existing_user = await db.users.find_one({"username": request.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": request.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user document
    user_doc = {
        "username": request.username,
        "email": request.email,
        "hashed_password": hash_password(request.password),
        "full_name": request.full_name,
        "created_at": datetime.utcnow(),
        "is_active": True,
    }
    
    await db.users.insert_one(user_doc)
    
    token = generate_token(request.username)
    
    return AuthResponse(
        success=True,
        message="Registration successful!",
        token=token,
        user=UserResponse(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            created_at=user_doc["created_at"]
        )
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login with username and password."""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Check if active
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    token = generate_token(request.username)
    
    return AuthResponse(
        success=True,
        message="Login successful!",
        token=token,
        user=UserResponse(
            username=user["username"],
            email=user["email"],
            full_name=user.get("full_name"),
            created_at=user["created_at"]
        )
    )


@router.get("/history/{username}")
async def get_user_history(username: str):
    """Get test history for a user."""
    db = get_database()
    
    # Verify user exists
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get test history sorted by date (newest first)
    history_cursor = db.test_history.find(
        {"username": username}
    ).sort("completed_at", -1).limit(50)
    
    history = []
    async for item in history_cursor:
        history.append({
            "test_id": item["test_id"],
            "subject": item["subject"],
            "level": item["level"],
            "num_questions": item["num_questions"],
            "score": item["score"],
            "percentage": item["percentage"],
            "proficiency": item["proficiency"],
            "completed_at": item["completed_at"],
        })
    
    return {
        "username": username,
        "total_tests": len(history),
        "history": history
    }


@router.get("/stats/{username}")
async def get_user_stats(username: str):
    """Get aggregate statistics for a user."""
    db = get_database()
    
    # Verify user exists
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all test history
    history = await db.test_history.find({"username": username}).to_list(length=1000)
    
    if not history:
        return {
            "username": username,
            "total_tests": 0,
            "average_score": 0,
            "best_score": 0,
            "favorite_subject": None,
            "proficiency_breakdown": {}
        }
    
    total_tests = len(history)
    total_percentage = sum(h["percentage"] for h in history)
    avg_score = total_percentage / total_tests
    best_score = max(h["percentage"] for h in history)
    
    # Count subjects
    subject_counts = {}
    for h in history:
        subj = h["subject"]
        subject_counts[subj] = subject_counts.get(subj, 0) + 1
    favorite_subject = max(subject_counts, key=subject_counts.get) if subject_counts else None
    
    # Count proficiency levels
    proficiency_breakdown = {}
    for h in history:
        prof = h["proficiency"]
        proficiency_breakdown[prof] = proficiency_breakdown.get(prof, 0) + 1
    
    return {
        "username": username,
        "total_tests": total_tests,
        "average_score": round(avg_score, 1),
        "best_score": round(best_score, 1),
        "favorite_subject": favorite_subject,
        "proficiency_breakdown": proficiency_breakdown,
        "subject_breakdown": subject_counts
    }
