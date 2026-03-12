"""
Seed script to populate the MongoDB questions collection with 20+ GRE-style questions.
Each question has a difficulty score (0.1-1.0), topic, tags, and correct_answer.
"""
from app.database import get_database

GRE_QUESTIONS = [
    # ── Algebra (Easy → Hard) ──────────────────────────────────────
    {
        "question_text": "Solve for x: 2x + 6 = 14",
        "options": ["2", "4", "6", "8"],
        "correct_answer": "4",
        "difficulty": 0.15,
        "topic": "Algebra",
        "tags": ["linear-equations", "basic"],
    },
    {
        "question_text": "What is the value of x in the equation 3(x - 2) = 12?",
        "options": ["4", "6", "8", "10"],
        "correct_answer": "6",
        "difficulty": 0.3,
        "topic": "Algebra",
        "tags": ["linear-equations", "distributive"],
    },
    {
        "question_text": "If x² - 5x + 6 = 0, what are the values of x?",
        "options": ["2 and 3", "1 and 6", "-2 and -3", "3 and 6"],
        "correct_answer": "2 and 3",
        "difficulty": 0.5,
        "topic": "Algebra",
        "tags": ["quadratic", "factoring"],
    },
    {
        "question_text": "For which value of k does the system x + ky = 3, 2x + 6y = 6 have infinitely many solutions?",
        "options": ["3", "2", "6", "1"],
        "correct_answer": "3",
        "difficulty": 0.75,
        "topic": "Algebra",
        "tags": ["systems-of-equations", "advanced"],
    },
    {
        "question_text": "If f(x) = x³ - 3x² + 2x, how many distinct real roots does f(x) = 0 have?",
        "options": ["1", "2", "3", "0"],
        "correct_answer": "3",
        "difficulty": 0.85,
        "topic": "Algebra",
        "tags": ["polynomials", "roots", "advanced"],
    },
    # ── Vocabulary (Easy → Hard) ───────────────────────────────────
    {
        "question_text": "Choose the synonym of 'Happy':",
        "options": ["Sad", "Joyful", "Angry", "Tired"],
        "correct_answer": "Joyful",
        "difficulty": 0.1,
        "topic": "Vocabulary",
        "tags": ["synonyms", "basic"],
    },
    {
        "question_text": "What does 'Benevolent' mean?",
        "options": ["Cruel", "Well-meaning and kindly", "Indifferent", "Aggressive"],
        "correct_answer": "Well-meaning and kindly",
        "difficulty": 0.35,
        "topic": "Vocabulary",
        "tags": ["definitions", "intermediate"],
    },
    {
        "question_text": "Choose the word that best completes: 'The politician's _____ remarks alienated even his supporters.'",
        "options": ["Eloquent", "Incendiary", "Mundane", "Placid"],
        "correct_answer": "Incendiary",
        "difficulty": 0.55,
        "topic": "Vocabulary",
        "tags": ["sentence-completion", "context-clues"],
    },
    {
        "question_text": "The word 'Obsequious' most nearly means:",
        "options": ["Rebellious", "Obedient to an excessive degree", "Observant", "Obscure"],
        "correct_answer": "Obedient to an excessive degree",
        "difficulty": 0.7,
        "topic": "Vocabulary",
        "tags": ["definitions", "advanced"],
    },
    {
        "question_text": "'Perspicacious' is best defined as:",
        "options": ["Sweating profusely", "Having keen insight", "Being persistent", "Showing perspiration"],
        "correct_answer": "Having keen insight",
        "difficulty": 0.9,
        "topic": "Vocabulary",
        "tags": ["definitions", "advanced", "rare-words"],
    },
    # ── Geometry (Easy → Hard) ─────────────────────────────────────
    {
        "question_text": "What is the area of a rectangle with length 8 and width 5?",
        "options": ["13", "26", "40", "45"],
        "correct_answer": "40",
        "difficulty": 0.15,
        "topic": "Geometry",
        "tags": ["area", "rectangles", "basic"],
    },
    {
        "question_text": "What is the length of the hypotenuse of a right triangle with legs 3 and 4?",
        "options": ["5", "6", "7", "8"],
        "correct_answer": "5",
        "difficulty": 0.35,
        "topic": "Geometry",
        "tags": ["pythagorean-theorem", "triangles"],
    },
    {
        "question_text": "A circle has a circumference of 31.4 cm. What is its approximate radius?",
        "options": ["5 cm", "10 cm", "15 cm", "7.5 cm"],
        "correct_answer": "5 cm",
        "difficulty": 0.5,
        "topic": "Geometry",
        "tags": ["circles", "circumference"],
    },
    {
        "question_text": "In a triangle with sides 7, 10, and 12, what type of triangle is it?",
        "options": ["Acute", "Right", "Obtuse", "Equilateral"],
        "correct_answer": "Acute",
        "difficulty": 0.7,
        "topic": "Geometry",
        "tags": ["triangle-classification", "advanced"],
    },
    # ── Reading Comprehension ──────────────────────────────────────
    {
        "question_text": "A passage states: 'The invention of the printing press democratized knowledge.' What does 'democratized' imply here?",
        "options": [
            "Made knowledge political",
            "Made knowledge accessible to more people",
            "Made knowledge expensive",
            "Made knowledge less reliable",
        ],
        "correct_answer": "Made knowledge accessible to more people",
        "difficulty": 0.3,
        "topic": "Reading Comprehension",
        "tags": ["inference", "vocabulary-in-context"],
    },
    {
        "question_text": "An author writes: 'Despite mounting evidence, the committee remained intransigent.' The author's tone toward the committee is most likely:",
        "options": ["Admiring", "Critical", "Neutral", "Supportive"],
        "correct_answer": "Critical",
        "difficulty": 0.6,
        "topic": "Reading Comprehension",
        "tags": ["tone", "inference", "advanced"],
    },
    {
        "question_text": "Which of the following best describes the function of a 'topic sentence' in a paragraph?",
        "options": [
            "It summarizes the entire essay",
            "It introduces the main idea of the paragraph",
            "It provides a counter-argument",
            "It restates the thesis",
        ],
        "correct_answer": "It introduces the main idea of the paragraph",
        "difficulty": 0.2,
        "topic": "Reading Comprehension",
        "tags": ["paragraph-structure", "basic"],
    },
    # ── Quantitative Reasoning ─────────────────────────────────────
    {
        "question_text": "If the ratio of boys to girls in a class is 3:5 and there are 40 students, how many boys are there?",
        "options": ["15", "20", "24", "25"],
        "correct_answer": "15",
        "difficulty": 0.4,
        "topic": "Quantitative Reasoning",
        "tags": ["ratios", "word-problems"],
    },
    {
        "question_text": "A store marks up the price of an item by 25% and then offers a 20% discount. What is the net effect on the original price?",
        "options": ["No change", "5% increase", "5% decrease", "0% exactly"],
        "correct_answer": "No change",
        "difficulty": 0.6,
        "topic": "Quantitative Reasoning",
        "tags": ["percentages", "markup-discount"],
    },
    {
        "question_text": "The probability of drawing a red ball from a bag is 1/4. If 3 balls are drawn with replacement, what is the probability that exactly 2 are red?",
        "options": ["9/64", "3/16", "3/64", "27/64"],
        "correct_answer": "9/64",
        "difficulty": 0.8,
        "topic": "Quantitative Reasoning",
        "tags": ["probability", "binomial", "advanced"],
    },
    {
        "question_text": "What is 15% of 240?",
        "options": ["34", "36", "38", "40"],
        "correct_answer": "36",
        "difficulty": 0.2,
        "topic": "Quantitative Reasoning",
        "tags": ["percentages", "basic"],
    },
    {
        "question_text": "If a train travels 300 km in 4 hours, and then 200 km in 3 hours, what is its average speed for the entire journey?",
        "options": ["65 km/h", "70 km/h", "71.4 km/h", "75 km/h"],
        "correct_answer": "71.4 km/h",
        "difficulty": 0.55,
        "topic": "Quantitative Reasoning",
        "tags": ["speed-distance-time", "averages"],
    },
]


async def seed_questions() -> int:
    """Insert seed questions into MongoDB. Returns the number of questions inserted."""
    db = get_database()

    existing_count = await db.questions.count_documents({})
    if existing_count >= len(GRE_QUESTIONS):
        return 0  # Already seeded

    # Clear and re-seed for idempotency
    await db.questions.delete_many({})
    result = await db.questions.insert_many(GRE_QUESTIONS)
    return len(result.inserted_ids)
