from pydantic import BaseModel, Field


class FitnessInput(BaseModel):
    bmi: float = Field(..., gt=0)
    age: int = Field(..., ge=1)
    workout_count: int = Field(..., ge=0)
    workout_duration: int = Field(..., ge=0)
