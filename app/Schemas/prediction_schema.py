from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class PredictionInput(BaseModel):
    age: int = 25
    weight_kg: float = 70.0
    height_cm: float = 170.0
    fitness_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    is_post_surgery: bool = False
    recovery_phase: Literal["normal", "remodeling", "subacute", "acute"] = "normal"
    surgery_date: Optional[date] = None
    pain_level: float = 0.0
    sleep_hours: Optional[float] = None
    goal: Literal[
        "weight_loss",
        "muscle_gain",
        "endurance",
        "rehabilitation",
        "flexibility",
        "maintenance",
    ] = "maintenance"
    medical_conditions: List[str] = Field(default_factory=list)
