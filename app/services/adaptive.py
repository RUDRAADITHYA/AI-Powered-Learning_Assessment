"""
1-Parameter IRT (Rasch Model) Adaptive Engine

Core Concepts:
    - θ (theta) : Student ability — a latent trait on a continuous scale [0, 1]
    - b          : Item difficulty — each question's difficulty on the same scale
    - P(θ, b)   : Probability the student answers correctly

Rasch Model:
    P(correct | θ, b) = 1 / (1 + exp(-a * (θ - b)))

    where a = discrimination constant (set to 4.0 for a reasonable logistic curve
    that keeps probabilities sensitive within the [0, 1] range).

Ability Update (EAP / Bayesian-like step):
    After each response, we update θ using a simplified MLE gradient step:

        θ_new = θ_old + learning_rate * (response - P(θ_old, b))

    where response = 1 if correct, 0 if incorrect.
    This pushes θ up when the student outperforms the model prediction,
    and down when they underperform.
"""

import math
from typing import Optional

# Discrimination parameter — controls steepness of the ICC
DISCRIMINATION: float = 4.0

# Learning rate for ability update — controls how fast θ changes
LEARNING_RATE: float = 0.15

# Clamp bounds to keep ability in a valid range
ABILITY_MIN: float = 0.05
ABILITY_MAX: float = 0.95


def icc_probability(theta: float, difficulty: float) -> float:
    """
    Item Characteristic Curve — returns P(correct | θ, b).

    Uses the 1PL Rasch model with a fixed discrimination parameter.
    """
    exponent = -DISCRIMINATION * (theta - difficulty)
    # Guard against overflow
    if exponent > 500:
        return 0.0
    if exponent < -500:
        return 1.0
    return 1.0 / (1.0 + math.exp(exponent))


def update_ability(
    current_theta: float,
    difficulty: float,
    is_correct: bool,
) -> float:
    """
    Update the student's ability estimate after a single response.

    Uses a gradient-ascent step on the log-likelihood:
        θ_new = θ + lr * (response - P(θ, b))

    This is a simplified form of Maximum Likelihood Estimation (MLE) update.
    """
    response = 1.0 if is_correct else 0.0
    p = icc_probability(current_theta, difficulty)
    residual = response - p  # positive if outperformed, negative if underperformed
    new_theta = current_theta + LEARNING_RATE * residual
    return max(ABILITY_MIN, min(ABILITY_MAX, new_theta))


def information_function(theta: float, difficulty: float) -> float:
    """
    Fisher Information for the Rasch model at a given θ and b.

    I(θ, b) = a² * P(θ, b) * (1 - P(θ, b))

    Higher information → the item is more informative at this ability level.
    We use this to select the *most informative* next question.
    """
    p = icc_probability(theta, difficulty)
    return DISCRIMINATION ** 2 * p * (1.0 - p)


def select_next_difficulty(current_theta: float) -> float:
    """
    Return the target difficulty for the next question.

    Under the Rasch model, maximum information occurs when b = θ.
    So the ideal next question has difficulty equal to current ability.
    """
    return max(0.1, min(1.0, current_theta))


def compute_final_ability(responses: list[dict]) -> float:
    """
    Recompute ability from scratch given all responses using iterative MLE.

    This is more stable than the incremental update for the final score.
    Each response is a dict with 'difficulty' (float) and 'is_correct' (bool).
    """
    if not responses:
        return 0.5

    theta = 0.5  # start from baseline
    # Run several iterations of Newton-Raphson-like updates
    for _ in range(20):
        numerator = 0.0
        denominator = 0.0
        for r in responses:
            b = r["difficulty"]
            y = 1.0 if r["is_correct"] else 0.0
            p = icc_probability(theta, b)
            numerator += DISCRIMINATION * (y - p)
            denominator += DISCRIMINATION ** 2 * p * (1.0 - p)
        if denominator == 0:
            break
        theta += numerator / denominator
        theta = max(ABILITY_MIN, min(ABILITY_MAX, theta))
    return round(theta, 4)
