# AI-Driven Adaptive Diagnostic Engine

A **1-Dimension Adaptive Testing Prototype** that dynamically assesses a student's proficiency level using **Item Response Theory (IRT)** and generates personalized study plans powered by **Groq LLM**.

Built with **FastAPI**, **MongoDB**, and **Python** — clean, modular, and production-ready.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Adaptive Algorithm Logic](#adaptive-algorithm-logic)
- [AI Log](#ai-log)

---

## Features

- **User Authentication** — Secure register/login with password hashing
- **AI-Generated Questions** — Dynamic subject-specific questions powered by Groq LLM (Algebra, Geometry, Vocabulary, Reading, etc.)
- **Adaptive Question Selection** — Questions adapt to student's current ability level
- **IRT-Based Ability Estimation** — Uses the 1-Parameter Rasch Model with real-time MLE updates
- **Multi-Subject Support** — Algebra, Geometry, Vocabulary, Reading, and more
- **Proficiency Badges** — Auto-calculated from test performance (PRO/AVERAGE/WEAK)
- **AI Study Plans** — Groq LLM generates personalized 3-step study recommendations
- **Test History** — Track all past tests with ability progression graphs
- **Session Tracking** — Full history of responses, ability updates, and analytics
- **Interactive API Docs** — Swagger UI at `/docs`

---

## Tech Stack

| Component       | Technology              |
|-----------------|-------------------------|
| Backend         | Python 3.11+ / FastAPI  |
| Database        | MongoDB Atlas (Cloud)   |
| AI Integration  | Groq API (LLaMA 3.3 70B)|
| Async Driver    | Motor (async MongoDB)   |
| Algorithm       | IRT Rasch Model (1PL)   |
| Authentication  | Password hashing (bcrypt)|
| Frontend        | HTML5/CSS3/JavaScript SPA|
| Deployment      | Render                  |

---

## Project Structure

```
adaptie-diagnosist/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + lifespan events
│   ├── config.py                # Environment settings (Pydantic)
│   ├── database.py              # MongoDB connection (Motor async)
│   ├── seed.py                  # 22 GRE-style seed questions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── question.py          # Question & QuestionOut schemas
│   │   └── session.py           # UserSession, Request/Response models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── diagnostic.py        # Core adaptive test endpoints
│   │   └── questions.py         # Question bank management
│   └── services/
│       ├── __init__.py
│       ├── adaptive.py          # IRT algorithm (Rasch model)
│       ├── question_service.py  # Question selection logic
│       └── ai_insights.py       # Groq LLM study plan generation
├── .env.example
├── .gitignore
├── requirements.txt
├── run.py                       # Entry point
└── README.md
```

---

## Setup & Installation

### Prerequisites

- **Python 3.11+**
- **MongoDB Atlas account** (free at [mongodb.com/cloud](https://mongodb.com/cloud))
- **Groq API key** (free at [console.groq.com](https://console.groq.com))

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/adaptie-diagnostist.git
   cd adaptie-diagnostist
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add:
   ```
   MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/
   GROQ_API_KEY=gsk_your_actual_key_here
   DATABASE_NAME=adaptive_diagnostic
   ```

5. **Run the application**
   ```bash
   python run.py
   ```
   The server starts at **http://localhost:8000**

---

## API Documentation

### Endpoints

| Method | Endpoint                          | Description                            |
|--------|-----------------------------------|----------------------------------------|
| `GET`  | `/`                               | Health check & endpoint listing        |
| `POST` | `/diagnostic/start`               | Start a new adaptive test session      |
| `GET`  | `/diagnostic/next-question`       | Get the next adaptively-selected question |
| `POST` | `/diagnostic/submit-answer`       | Submit an answer & update ability      |
| `GET`  | `/diagnostic/session-summary`     | Get results + AI study plan            |
| `GET`  | `/questions/`                     | List all questions (with filters)      |
| `POST` | `/questions/seed`                 | Re-seed the question bank              |
| `GET`  | `/questions/topics`               | List all question topics               |

### Test Flow Example

**Step 1: Start a session**
```bash
curl -X POST http://localhost:8000/diagnostic/start
```
Response:
```json
{
  "session_id": "a1b2c3d4-...",
  "message": "Adaptive test session started...",
  "initial_ability": 0.5
}
```

**Step 2: Get next question**
```bash
curl "http://localhost:8000/diagnostic/next-question?session_id=a1b2c3d4-..."
```
Response:
```json
{
  "id": "665f...",
  "question_text": "If x² - 5x + 6 = 0, what are the values of x?",
  "options": ["2 and 3", "1 and 6", "-2 and -3", "3 and 6"],
  "difficulty": 0.5,
  "topic": "Algebra",
  "tags": ["quadratic", "factoring"],
  "question_number": 1,
  "total_questions": 10
}
```

**Step 3: Submit answer**
```bash
curl -X POST http://localhost:8000/diagnostic/submit-answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": "a1b2c3d4-...", "question_id": "665f...", "selected_answer": "2 and 3"}'
```
Response:
```json
{
  "is_correct": true,
  "correct_answer": "2 and 3",
  "previous_ability": 0.5,
  "updated_ability": 0.575,
  "questions_remaining": 9,
  "is_complete": false
}
```

**Step 4: Repeat steps 2-3** until `is_complete: true`

**Step 5: Get summary + study plan**
```bash
curl "http://localhost:8000/diagnostic/session-summary?session_id=a1b2c3d4-..."
```

---

## Adaptive Algorithm Logic

### Overview

The engine uses the **1-Parameter IRT Rasch Model** — a well-established psychometric model for adaptive testing.

### Mathematical Foundation

**Item Characteristic Curve (ICC):**

$$P(\text{correct} \mid \theta, b) = \frac{1}{1 + e^{-a(\theta - b)}}$$

Where:
- $\theta$ = student ability (latent trait, scale 0–1)
- $b$ = item difficulty (0.1–1.0)
- $a$ = discrimination parameter (fixed at 4.0)

**Ability Update (Gradient-Ascent MLE):**

After each response:

$$\theta_{\text{new}} = \theta_{\text{old}} + \eta \cdot (y - P(\theta, b))$$

Where:
- $y = 1$ if correct, $0$ if incorrect
- $\eta = 0.15$ (learning rate)
- The residual $(y - P)$ is positive when the student outperforms the model

**Question Selection (Maximum Information):**

The next question maximizes Fisher Information:

$$I(\theta, b) = a^2 \cdot P(\theta, b) \cdot (1 - P(\theta, b))$$

This peaks when $b = \theta$, so the engine targets questions at the student's current estimated ability.

**Final Ability (Full MLE):**

After all questions, ability is recomputed from scratch using iterative Newton-Raphson over ALL responses for a more stable final estimate.

### Adaptive Flow

```
1. Student starts → θ = 0.5 (baseline)
2. Engine selects question with b ≈ θ (max information)
3. Student answers → θ updated via IRT
4. Repeat for 10 questions
5. Final θ computed via full MLE
6. Performance sent to LLM → 3-step study plan
```

---

## Deployment to Render

### Quick Start (3 Steps)

#### 1. Push to GitHub

If you haven't already:
```bash
git remote add origin https://github.com/YOUR_USERNAME/adaptie-diagnostist.git
git branch -M main
git push -u origin main
```

#### 2. Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Select your `adaptie-diagnostist` GitHub repository
4. Configure:
   - **Name**: `adaptie-diagnostist`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Paid for 24/7 uptime)

#### 3. Set Environment Variables

In the Render dashboard, go to **Settings** → **Environment** and add:

| Key | Value |
|-----|-------|
| `MONGODB_URI` | Your MongoDB Atlas connection string (see below) |
| `GROQ_API_KEY` | Your Groq API key from https://console.groq.com/keys |
| `DATABASE_NAME` | `adaptive_diagnostic` |
| `APP_NAME` | `Adaptive-Diagnostist` |

**Getting Your MongoDB URI:**
1. Go to https://cloud.mongodb.com
2. Navigate to **Atlas** → Your Cluster
3. Click **"Connect"** → **"Drivers"**
4. Copy the connection string (it looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)

### Troubleshooting Deployment

**Issue: "ModuleNotFoundError: No module named 'motor'"**
- Solution: Ensure `requirements.txt` includes all dependencies. It's already configured.

**Issue: "MongoDB Connection Timeout"**
- Solution: Verify `MONGODB_URI` is correct and your MongoDB cluster has Render's IP whitelisted (or "Allow access from anywhere")

**Issue: "Groq API Error"**
- Solution: Verify `GROQ_API_KEY` is correct in Render's environment variables

### Live Application

Once deployed, your app will be available at:
```
https://adaptie-diagnostist-xxxx.onrender.com
```

---

## AI Log

### How AI Tools Were Used

- **GitHub Copilot** — Primary development tool. Used for:
  - Scaffolding the FastAPI project structure
  - Generating the 22 seed questions with realistic GRE content
  - Implementing the IRT Rasch model math (ICC, Fisher Information, MLE)
  - Building the Groq integration for study plan generation
  - Writing comprehensive API documentation

### Challenges AI Couldn't Fully Solve

1. **IRT Parameter Tuning** — The discrimination constant (`a = 4.0`) and learning rate (`η = 0.15`) required manual tuning to keep ability estimates within [0, 1] and responsive but not volatile. AI suggested reasonable defaults but the final values were verified through testing.

2. **Question Selection Strategy** — The initial AI suggestion was simple nearest-difficulty matching. I enhanced it to use Fisher Information maximization, which is the mathematically optimal approach for adaptive testing.

3. **MongoDB Index Design** — Compound indexes on `(difficulty, topic)` for the question selection queries required understanding the specific access patterns of the adaptive algorithm.

---

## License

MIT
