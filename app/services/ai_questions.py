"""
AI-powered question generation using Groq LLM.
Generates GRE-style questions dynamically based on user's selected subject, 
number of questions, and difficulty level.
"""
import json
import re
from groq import AsyncGroq
from app.config import get_settings


async def generate_questions(
    subject: str,
    num_questions: int,
    difficulty: str,
) -> list[dict]:
    """
    Generate GRE-style questions using Groq LLM.
    
    Args:
        subject: "Math", "Verbal", "Algebra", "Geometry", "Vocabulary", "Reading", etc
        num_questions: Number of questions to generate (3-20)
        difficulty: "easy", "medium", or "hard"
    
    Returns:
        List of question dictionaries with question_text, options, correct_answer, topic, difficulty
    """
    settings = get_settings()
    
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        raise ValueError("GROQ_API_KEY not configured")
    
    # Map difficulty to numeric values
    diff_map = {"easy": 0.3, "medium": 0.5, "hard": 0.8}
    base_difficulty = diff_map.get(difficulty, 0.5)
    
    # Define strict topic mappings and examples
    subject_mapping = {
        "Math": {
            "topics": ["Algebra", "Geometry", "Arithmetic", "Data Analysis", "Quantitative Reasoning"],
            "examples": "Solve for x in 2x + 5 = 13. What is the area of a triangle with base 8 and height 6? If a car travels 120 miles in 2 hours, what is its speed?",
            "exclude": "Do NOT include vocabulary, reading comprehension, grammar, or language questions"
        },
        "Verbal": {
            "topics": ["Vocabulary", "Reading Comprehension", "Text Completion", "Sentence Equivalence"],
            "examples": "What does 'perspicacious' mean? Which word best completes the sentence? What is the main idea of this passage? Choose two words with similar meanings.",
            "exclude": "Do NOT include math, geometry, equations, or numerical calculation questions"
        },
        "Algebra": {
            "topics": ["Linear Equations", "Quadratic Equations", "Functions", "Polynomials", "Systems of Equations"],
            "examples": "Solve x² - 5x + 6 = 0. Simplify: (3x² + 2x - 5) / (x + 1). If f(x) = 2x + 3, find f(5).",
            "exclude": "Do NOT include geometry, vocabulary, reading, or statistics questions"
        },
        "Geometry": {
            "topics": ["Triangles", "Circles", "Polygons", "Volume", "Coordinate Geometry", "Angles"],
            "examples": "A circle has radius 5. What is its circumference? In triangle ABC, angle A = 60°. What is the area? What are the coordinates of the midpoint?",
            "exclude": "Do NOT include algebra, vocabulary, reading, or word problems unrelated to shapes"
        },
        "Vocabulary": {
            "topics": ["Word Definitions", "Synonyms", "Antonyms", "Word Usage", "Contextual Meaning"],
            "examples": "Which word is most similar to 'verbose'? What does 'ephemeral' mean? Choose a word to complete: 'His ___ manner made him unpopular.'",
            "exclude": "Do NOT include math, geometry, reading passages, grammar, or numerical questions"
        },
        "Reading": {
            "topics": ["Reading Comprehension", "Passage Analysis", "Main Idea", "Author's Tone", "Inference"],
            "examples": "Based on this passage, what is the author's main point? Which detail best supports the conclusion? What is the author's tone in this passage?",
            "exclude": "Do NOT include vocabulary definitions, math, geometry, or grammar questions"
        },
    }
    
    # Get mapping or use the subject as-is if custom
    mapping = subject_mapping.get(subject)
    if not mapping:
        mapping = subject_mapping.get("Math")  # Default fallback
    
    prompt = f"""You are a professional GRE test writer. Generate EXACTLY {num_questions} {difficulty}-level multiple choice questions, ALL strictly on: {subject}

SUBJECT REQUIREMENTS:
- Topics to use: {', '.join(mapping['topics'])}
- Example question types: {mapping['examples']}
- {mapping['exclude']}

STRICT REQUIREMENTS:
1. EVERY question MUST be about {subject} ONLY - no exceptions
2. Do NOT mix in questions from other subjects
3. Return ONLY a valid JSON array, no markdown, no explanations
4. Exactly 4 options per question (A, B, C, D style)
5. Correct answer must match an option exactly
6. Difficulty level: {difficulty}
7. Set difficulty field to {base_difficulty}

REQUIRED JSON STRUCTURE - Return ONLY this:
[
  {{
    "question_text": "Full question here",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": "Option A text",
    "topic": "{subject}",
    "difficulty": {base_difficulty}
  }}
]

GENERATE {num_questions} STRICTLY {subject.upper()} QUESTIONS NOW:"""

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a strict GRE test writer specializing in {subject} questions. Output ONLY valid JSON array. No explanations. Every question must be ONLY about {subject}. No mixing subjects."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,  # Lower temperature for consistency
            max_tokens=5000,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from the response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        questions = json.loads(content)
        
        # Keywords to validate subject adherence
        math_keywords = {"algebra", "geometry", "equation", "solve", "calculate", "triangle", "circle", "area", 
                         "angle", "polynomial", "function", "derivative", "integral", "distance", "coordinate", 
                         "perimeter", "volume", "radius", "diameter", "probability", "graph", "matrix"}
        
        verbal_keywords = {"vocabulary", "word", "meaning", "synonym", "antonym", "passage", "reading", "sentence",
                          "idiom", "grammar", "complete", "definition", "illustrates", "author", "tone", "best defines",
                          "most nearly means", "would be most deplored", "suggests that"}
        
        subject_keywords = {
            "Math": math_keywords,
            "Algebra": {"equation", "solve", "polynomial", "quadratic", "linear", "expression", "variable", "coefficient", "factor", "function", "graph"},
            "Geometry": {"triangle", "circle", "polygon", "area", "perimeter", "volume", "angle", "radius", "diameter", "coordinate", "distance", "parallel"},
            "Vocabulary": {"word", "meaning", "best defines", "most nearly means", "synonym", "antonym", "definition", "refers to"},
            "Reading": {"passage", "reading", "author", "main idea", "tone", "infer", "suggest", "paragraph", "illustrate", "excerpt"},
        }
        
        expected_keywords = subject_keywords.get(subject, math_keywords)
        
        # Validate and clean questions
        validated_questions = []
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                continue
            
            # Ensure all required fields exist
            if not all(k in q for k in ["question_text", "options", "correct_answer"]):
                continue
            
            # Ensure options is a list with exactly 4 items
            if not isinstance(q["options"], list) or len(q["options"]) != 4:
                continue
            
            # Verify correct_answer is in options
            if q["correct_answer"] not in q["options"]:
                continue
            
            # Subject validation: Check if question text contains relevant keywords
            question_lower = q["question_text"].lower()
            has_relevant_keyword = any(kw in question_lower for kw in expected_keywords)
            
            # If no relevant keywords found, check for obvious non-matching keywords (optional stricter check)
            if not has_relevant_keyword:
                # Log but allow - the prompt should prevent this
                print(f"Warning: Question {i+1} may not match subject {subject}: {q['question_text'][:80]}")
            
            # Assign unique ID
            q["id"] = f"ai_q_{i+1}"
            
            # Set topic to subject if not provided
            if "topic" not in q or not q["topic"]:
                q["topic"] = subject
            
            # Ensure difficulty exists and is in valid range
            if "difficulty" not in q or not isinstance(q["difficulty"], (int, float)):
                q["difficulty"] = base_difficulty
            q["difficulty"] = max(0.1, min(1.0, q["difficulty"]))
            
            validated_questions.append(q)
        
        if len(validated_questions) < num_questions:
            print(f"Warning: Only got {len(validated_questions)} valid questions out of {num_questions} requested")
        
        if not validated_questions:
            raise ValueError(f"AI generated no valid {subject} questions. Try again.")
        
        return validated_questions[:num_questions]
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {content[:500]}...")
        raise ValueError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        print(f"Error generating questions: {e}")
        raise


async def generate_feedback(
    correct_count: int,
    total_questions: int,
    topics_weak: list[str],
    topics_strong: list[str],
    difficulty: str,
    subject: str,
) -> str:
    """
    Generate personalized feedback and study recommendations.
    """
    settings = get_settings()
    
    if not settings.GROQ_API_KEY:
        return "Study plan unavailable - API key not configured."
    
    score_percent = (correct_count / total_questions) * 100
    
    prompt = f"""A student just completed a GRE practice test. Provide personalized feedback and study advice.

Test Results:
- Subject: {subject}
- Difficulty: {difficulty}
- Score: {correct_count}/{total_questions} ({score_percent:.0f}%)
- Strong Topics: {', '.join(topics_strong) if topics_strong else 'None identified'}
- Weak Topics: {', '.join(topics_weak) if topics_weak else 'None identified'}

Provide:
1. A brief assessment of their performance (2-3 sentences)
2. Specific areas to focus on for improvement
3. 3 actionable study tips tailored to their weak areas
4. Encouragement and next steps

Be concise but helpful. Format with clear sections."""

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a supportive GRE tutor providing personalized feedback."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=600,
    )
    
    return response.choices[0].message.content
