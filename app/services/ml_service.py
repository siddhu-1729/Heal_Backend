import os
from datetime import date
from typing import Any, Dict, List, Union

import torch
import torch.nn as nn


class WorkoutRecommender(nn.Module):
    """Inference architecture that matches workout_recommender.pt."""

    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(14, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
        )

        self.category_head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 7),
        )
        self.intensity_head = nn.Sequential(
            nn.Linear(64, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )
        self.duration_head = nn.Sequential(
            nn.Linear(64, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor):
        shared = self.encoder(x)
        category_logits = self.category_head(shared)
        intensity = self.intensity_head(shared)
        duration = self.duration_head(shared)
        return category_logits, intensity, duration


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "workout_recommender.pt")


FITNESS_LEVEL_MAP = {
    "beginner": 0.0,
    "intermediate": 0.5,
    "advanced": 1.0,
}

RECOVERY_PHASE_MAP = {
    "normal": 0.0,
    "remodeling": 0.33,
    "subacute": 0.66,
    "acute": 1.0,
}

GOAL_ONE_HOT = {
    "weight_loss": [1.0, 0.0, 0.0, 0.0],
    "muscle_gain": [0.0, 1.0, 0.0, 0.0],
    "endurance": [0.0, 0.0, 1.0, 0.0],
    "rehabilitation": [0.0, 0.0, 0.0, 1.0],
}

CARDIAC_CONDITIONS = {
    "heart_disease",
    "hypertension",
    "arrhythmia",
    "coronary_artery_disease",
    "cardiac",
}

CATEGORY_NAMES = {
    0: "bodyweight",
    1: "strength",
    2: "hiit",
    3: "yoga",
    4: "cardio",
    5: "stretching",
    6: "rehabilitation",
}

CATEGORY_EXERCISES = {
    0: ["push-ups", "bodyweight squats", "forward lunges", "plank"],
    1: ["dumbbell deadlift", "goblet squat", "dumbbell bench press", "rows"],
    2: ["jumping jacks", "burpees", "mountain climbers", "high knees"],
    3: ["cat-cow", "downward dog", "child's pose", "warrior II"],
    4: ["brisk walking", "cycling", "elliptical", "swimming"],
    5: ["hamstring stretch", "hip flexor stretch", "quad stretch", "shoulder stretch"],
    6: ["heel slides", "sit-to-stand", "wall slides", "ankle pumps"],
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def estimate_sleep_hours(age: int) -> float:
    """Age-based fallback when sleep_hours is not provided by client."""
    if age <= 5:
        return 11.0
    if age <= 13:
        return 9.5
    if age <= 17:
        return 8.5
    if age <= 64:
        return 7.5
    return 7.0


def _days_since_surgery_score(is_post_surgery: bool, surgery_date_value: Union[date, None]) -> float:
    if not is_post_surgery or surgery_date_value is None:
        return 0.0

    days = (date.today() - surgery_date_value).days
    if days < 0:
        return 1.0
    # Fresh surgery near 1.0, and linearly decays to 0 by ~6 months.
    return _clamp(1.0 - (days / 180.0), 0.0, 1.0)


def encode_user_profile(user: Dict[str, Any]) -> List[float]:
    age = float(user.get("age", 25))
    weight_kg = float(user.get("weight_kg", 70.0))
    height_cm = float(user.get("height_cm", 170.0))

    height_m = max(height_cm / 100.0, 0.5)
    bmi = weight_kg / (height_m * height_m)

    fitness_level = str(user.get("fitness_level", "beginner")).lower()
    is_post_surgery = bool(user.get("is_post_surgery", False))
    recovery_phase = str(user.get("recovery_phase", "normal")).lower()

    pain_level = float(user.get("pain_level", 0.0))
    sleep_hours_raw = user.get("sleep_hours", None)
    sleep_hours = float(sleep_hours_raw) if sleep_hours_raw is not None else estimate_sleep_hours(int(age))

    goal = str(user.get("goal", "maintenance")).lower()
    medical_conditions = [str(item).lower() for item in user.get("medical_conditions", [])]

    age_norm = _clamp(age / 100.0, 0.0, 1.0)
    bmi_norm = _clamp(bmi / 40.0, 0.0, 1.0)
    fitness_norm = FITNESS_LEVEL_MAP.get(fitness_level, 0.0)
    recovery_norm = RECOVERY_PHASE_MAP.get(recovery_phase, 0.0)
    days_since_surgery_norm = _days_since_surgery_score(is_post_surgery, user.get("surgery_date"))
    pain_norm = _clamp(pain_level / 10.0, 0.0, 1.0)
    sleep_norm = _clamp(sleep_hours / 9.0, 0.0, 1.0)

    goal_one_hot = GOAL_ONE_HOT.get(goal, [0.0, 0.0, 0.0, 0.0])

    num_conditions_norm = _clamp(min(len(medical_conditions), 5) / 5.0, 0.0, 1.0)
    has_cardiac = 1.0 if any(cond in CARDIAC_CONDITIONS for cond in medical_conditions) else 0.0

    return [
        age_norm,
        bmi_norm,
        fitness_norm,
        1.0 if is_post_surgery else 0.0,
        recovery_norm,
        days_since_surgery_norm,
        pain_norm,
        sleep_norm,
        *goal_one_hot,
        num_conditions_norm,
        has_cardiac,
    ]


def _load_model() -> WorkoutRecommender:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    state_dict = (
        checkpoint["model_state_dict"]
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint
        else checkpoint
    )

    model = WorkoutRecommender()
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    if missing_keys or unexpected_keys:
        raise RuntimeError(
            "Checkpoint architecture mismatch. "
            f"Missing keys: {missing_keys}; Unexpected keys: {unexpected_keys}"
        )

    model.eval()
    return model


model = _load_model()


def _safe_category_from_features(predicted_category: int, features: List[float]) -> int:
    """Enforce hard safety constraints from normalized features before returning category."""
    is_post_surgery = features[3] >= 0.5
    recovery_phase_norm = features[4]
    pain_level = features[6] * 10.0
    sleep_hours = features[7] * 9.0
    has_cardiac = features[13] >= 0.5

    # closest phase bucket from encoded values [0.0, 0.33, 0.66, 1.0]
    recovery_phase_candidates = [0.0, 0.33, 0.66, 1.0]
    closest_phase = min(recovery_phase_candidates, key=lambda x: abs(x - recovery_phase_norm))

    if is_post_surgery and closest_phase >= 0.95:  # acute
        return 6
    if pain_level >= 7.0:
        return 6 if predicted_category != 5 else 5
    if is_post_surgery and abs(closest_phase - 0.66) < 0.05:  # subacute
        return 6 if predicted_category != 5 else 5

    disallowed = set()
    if pain_level >= 4.0:
        disallowed.update({1, 2})
    if has_cardiac:
        disallowed.add(2)
    if sleep_hours < 5.0:
        disallowed.add(2)
    if predicted_category in disallowed:
        if 4 not in disallowed:
            return 4
        if 5 not in disallowed:
            return 5
        return 6
    return predicted_category


def predict(features: List[float]) -> Dict[str, Union[int, float, str, List[str]]]:
    if len(features) != 14:
        raise ValueError(f"Expected 14 input features, got {len(features)}")

    x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        category_logits, intensity_pred, duration_pred = model(x)

    category_id = int(torch.argmax(category_logits, dim=1).item())
    category_id = _safe_category_from_features(category_id, features)

    return {
        "category_id": category_id,
        "category_name": CATEGORY_NAMES.get(category_id, "unknown"),
        "exercises": CATEGORY_EXERCISES.get(category_id, []),
        "intensity": float(intensity_pred.squeeze(1).item()),
        "duration": float(duration_pred.squeeze(1).item()),
    }
