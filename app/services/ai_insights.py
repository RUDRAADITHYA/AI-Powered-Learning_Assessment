"""
Groq LLM integration for generating personalized study plans.
"""
from groq import AsyncGroq
from app.config import get_settings


async def generate_study_plan(
    topics_missed: list[str],
    topics_strong: list[str],
    final_ability: float,
    difficulty_reached: float,
    total_correct: int,
    total_questions: int,
) -> str:
    """
    Send performance summary to Groq LLM and get a personalized 3-step study plan.
    """
    settings = get_settings()

    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        return (
            "⚠️ Study plan unavailable — GROQ_API_KEY not configured.\n"
            "Set your Groq API key in the .env file to enable AI-powered study plans."
        )

    prompt = f"""You are an expert GRE tutor. A student just completed an adaptive diagnostic test.
Here are their results:

- Final Ability Score: {final_ability:.2f} (scale 0-1, where 1 is highest)
- Difficulty Level Reached: {difficulty_reached:.2f}
- Score: {total_correct}/{total_questions} correct
- Weak Topics (missed questions): {', '.join(topics_missed) if topics_missed else 'None'}
- Strong Topics (answered correctly): {', '.join(topics_strong) if topics_strong else 'None'}

Based on this data, generate a concise, actionable **3-step personalized study plan** that:
1. Targets their specific weaknesses
2. Builds on their strengths
3. Includes concrete practice recommendations

Format the plan clearly with numbered steps. Be specific about *what* to study and *how*."""

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful GRE tutor providing personalized study advice."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=800,
    )

    return response.choices[0].message.content
