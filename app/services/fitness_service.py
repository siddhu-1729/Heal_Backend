from typing import Dict

from app.Schemas.fitness_schema import FitnessInput
from app import models
from sqlalchemy.orm import Session


def calculate_sleep_hours(age: int) -> float:
    if age <= 5:
        return 11.0
    if age <= 13:
        return 9.5
    if age <= 17:
        return 8.5
    if age <= 64:
        return 7.5
    return 7.0


def calculate_fitness_score(data: FitnessInput, sleep_hours: float) -> int:
    score = 0

    # BMI
    if 18.5 <= data.bmi <= 24.9:
        score += 3
    elif 25 <= data.bmi <= 29.9:
        score += 2
    else:
        score += 1

    # Sleep
    if 7 <= sleep_hours <= 9:
        score += 3
    elif 6 <= sleep_hours < 7:
        score += 2
    else:
        score += 1

    # Workout frequency
    if data.workout_count >= 4:
        score += 3
    elif 2 <= data.workout_count <= 3:
        score += 2
    else:
        score += 1

    # Workout duration
    total_minutes = data.workout_count * data.workout_duration
    if total_minutes >= 150:
        score += 3
    elif total_minutes >= 90:
        score += 2
    else:
        score += 1

    return score


def classify_fitness(score: int) -> str:
    if score >= 10:
        return "Excellent"
    if score >= 7:
        return "Good"
    if score >= 5:
        return "Average"
    return "Needs Improvement"


def analyze_fitness(data: FitnessInput) -> Dict[str, int | float | str]:
    sleep_hours = calculate_sleep_hours(data.age)
    total_minutes = data.workout_count * data.workout_duration
    score = calculate_fitness_score(data, sleep_hours)
    level = classify_fitness(score)
    return {
        "fitness_score": score,
        "fitness_level": level,
        "sleep_hours_used": sleep_hours,
        "total_weekly_minutes": total_minutes,
    }


def update_user_fitness_analysis(
    db: Session, current_user_email: str, data: FitnessInput
) -> Dict[str, int | float | str]:
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise ValueError("User not found")

    analysis = analyze_fitness(data)
    user.fitness_score = int(analysis["fitness_score"])
    user.fitness_level = str(analysis["fitness_level"])
    db.commit()
    db.refresh(user)
    return analysis


def get_user_fitness_summary(db: Session, current_user_email: str) -> Dict[str, int | str | None]:
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user:
        raise ValueError("User not found")

    return {
        "fitness_score": user.fitness_score,
        "fitness_level": user.fitness_level,
        "sleep_hours":user.sleep_hours,
    }


def generate_recommendations(level, bmi, sleep, total_minutes):

    recommendations = []
    advice = []

    # Fitness level based suggestions
    if level == "Needs Improvement":
        recommendations.append("Brisk walking 20-30 mins, 3 times/week")
        recommendations.append("Light bodyweight training")
        advice.append("Start gradually and build consistency")

    elif level == "Average":
        recommendations.append("3-4 workouts per week")
        recommendations.append("Combine strength and cardio")
        advice.append("Increase weekly activity to 150 mins")

    elif level == "Good":
        recommendations.append("Progressive strength training")
        recommendations.append("Add HIIT once per week")
        advice.append("Track performance improvements")

    elif level == "Excellent":
        recommendations.append("Structured training split")
        recommendations.append("Include mobility & recovery sessions")
        advice.append("Avoid overtraining")

    # BMI adjustments
    if bmi > 30:
        advice.append("Focus on low-impact cardio like cycling or swimming")

    if bmi < 18.5:
        advice.append("Include strength training and improve nutrition")

    # Sleep adjustments
    if sleep is not None and sleep < 6:
        advice.append("Improve sleep to enhance recovery")

    if total_minutes < 150:
        advice.append("Increase weekly workout duration to at least 150 minutes")

    return {
        "recommendations": recommendations,
        "advice": advice
    }
