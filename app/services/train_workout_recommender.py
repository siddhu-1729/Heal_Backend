import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split


SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

GOALS = [
    "weight_loss",
    "muscle_gain",
    "endurance",
    "rehabilitation",
    "flexibility",
    "maintenance",
]
FITNESS_LEVELS = ["beginner", "intermediate", "advanced"]
RECOVERY_PHASES = ["normal", "remodeling", "subacute", "acute"]
AGE_BINS = ["minor", "adult", "older"]

FITNESS_LEVEL_MAP = {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0}
RECOVERY_PHASE_MAP = {"normal": 0.0, "remodeling": 0.33, "subacute": 0.66, "acute": 1.0}
GOAL_ONE_HOT = {
    "weight_loss": [1.0, 0.0, 0.0, 0.0],
    "muscle_gain": [0.0, 1.0, 0.0, 0.0],
    "endurance": [0.0, 0.0, 1.0, 0.0],
    "rehabilitation": [0.0, 0.0, 0.0, 1.0],
    "flexibility": [0.0, 0.0, 0.0, 0.0],
    "maintenance": [0.0, 0.0, 0.0, 0.0],
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
GOAL_PRIORITIES = {
    "weight_loss": [2, 4, 0],
    "muscle_gain": [1, 0],
    "endurance": [4, 2],
    "rehabilitation": [6, 5, 3],
    "flexibility": [3, 5],
    "maintenance": [0, 4, 5],
}
CARDIAC_CONDITIONS = {
    "heart_disease",
    "hypertension",
    "arrhythmia",
    "coronary_artery_disease",
}
NON_CARDIAC_CONDITIONS = {
    "diabetes",
    "asthma",
    "arthritis",
    "thyroid_disorder",
}
FEATURE_NAMES = [
    "age_norm",
    "bmi_norm",
    "fitness_norm",
    "is_post_surgery",
    "recovery_phase_norm",
    "days_since_surgery_norm",
    "pain_norm",
    "sleep_norm",
    "goal_weight_loss",
    "goal_muscle_gain",
    "goal_endurance",
    "goal_rehabilitation",
    "num_conditions_norm",
    "has_cardiac",
]


def clamp(x: float, low: float, high: float) -> float:
    return max(low, min(high, x))


def age_from_bin(age_bin: str) -> int:
    if age_bin == "minor":
        return random.randint(14, 17)
    if age_bin == "older":
        return random.randint(51, 75)
    return random.randint(18, 50)


def estimate_sleep_hours(age: int) -> float:
    if age <= 5:
        return 11.0
    if age <= 13:
        return 9.5
    if age <= 17:
        return 8.5
    if age <= 64:
        return 7.5
    return 7.0


@dataclass
class Profile:
    age: int
    bmi: float
    fitness_level: str
    is_post_surgery: bool
    recovery_phase: str
    days_since_surgery: int
    pain_level: float
    sleep_hours: float
    goal: str
    medical_conditions: List[str]
    has_cardiac: bool
    age_bin: str


def generate_conditions(has_cardiac_hint: bool) -> Tuple[List[str], bool]:
    conditions: List[str] = []
    if has_cardiac_hint:
        conditions.append(random.choice(list(CARDIAC_CONDITIONS)))
    if random.random() < 0.25:
        conditions.append("diabetes")
    if random.random() < 0.15:
        conditions.append("hypertension")
    if random.random() < 0.2:
        conditions.append(random.choice(list(NON_CARDIAC_CONDITIONS)))
    conditions = sorted(set(conditions))
    has_cardiac = any(c in CARDIAC_CONDITIONS for c in conditions)
    return conditions, has_cardiac


def generate_profile(goal: str, fitness_level: str, age_bin: str, surgery_mode: str) -> Profile:
    age = age_from_bin(age_bin)
    bmi = round(np.random.normal(25.5, 4.8), 1)
    bmi = clamp(bmi, 16.0, 40.0)

    is_post_surgery = surgery_mode != "none"
    if surgery_mode == "acute":
        recovery_phase = "acute"
        days_since_surgery = random.randint(0, 14)
    elif surgery_mode == "subacute":
        recovery_phase = "subacute"
        days_since_surgery = random.randint(15, 60)
    elif surgery_mode == "remodeling":
        recovery_phase = "remodeling"
        days_since_surgery = random.randint(61, 180)
    else:
        recovery_phase = "normal"
        days_since_surgery = 0

    base_pain = 1.5
    if recovery_phase == "acute":
        base_pain = 7.8
    elif recovery_phase == "subacute":
        base_pain = 5.1
    elif recovery_phase == "remodeling":
        base_pain = 3.0
    pain_level = clamp(np.random.normal(base_pain, 1.4), 0.0, 10.0)

    sleep_hours = clamp(np.random.normal(estimate_sleep_hours(age), 1.1), 3.5, 10.5)
    has_cardiac_hint = random.random() < 0.18
    medical_conditions, has_cardiac = generate_conditions(has_cardiac_hint)
    return Profile(
        age=age,
        bmi=bmi,
        fitness_level=fitness_level,
        is_post_surgery=is_post_surgery,
        recovery_phase=recovery_phase,
        days_since_surgery=days_since_surgery,
        pain_level=float(pain_level),
        sleep_hours=float(sleep_hours),
        goal=goal,
        medical_conditions=medical_conditions,
        has_cardiac=has_cardiac,
        age_bin=age_bin,
    )


def allowed_categories(profile: Profile) -> List[int]:
    if profile.is_post_surgery and profile.recovery_phase == "acute":
        return [6]
    if profile.pain_level >= 7.0:
        return [6, 5]
    if profile.is_post_surgery and profile.recovery_phase == "subacute":
        return [6, 5]

    disallowed = set()
    if profile.pain_level >= 4.0:
        disallowed.update({1, 2})
    if profile.has_cardiac:
        disallowed.add(2)
    if profile.sleep_hours < 5.0:
        disallowed.add(2)
    if profile.age < 18:
        disallowed.add(1)
    if profile.bmi > 30:
        disallowed.add(2)

    base = [0, 1, 2, 3, 4, 5, 6]
    return [c for c in base if c not in disallowed]


def choose_category(profile: Profile) -> int:
    allowed = allowed_categories(profile)
    priorities = list(GOAL_PRIORITIES[profile.goal])
    if "diabetes" in profile.medical_conditions:
        priorities = [c for c in [4, 0, 5, 6, 3, 1, 2] if c in priorities or c not in [2]]

    for c in priorities:
        if c in allowed:
            return c
    if not allowed:
        return 6
    return random.choice(allowed)


def target_intensity(profile: Profile, category_id: int) -> float:
    base = {"beginner": 0.32, "intermediate": 0.53, "advanced": 0.74}[profile.fitness_level]
    if profile.goal in {"weight_loss", "endurance"}:
        base += 0.08
    if profile.goal in {"flexibility", "rehabilitation"}:
        base -= 0.1

    if profile.pain_level >= 7:
        base = min(base, 0.22)
    elif profile.pain_level >= 4:
        base = min(base, 0.4)
    if profile.is_post_surgery and profile.recovery_phase == "acute":
        base = min(base, 0.2)
    if profile.is_post_surgery and profile.recovery_phase == "subacute":
        base = min(base, 0.35)
    if profile.has_cardiac:
        base = min(base, 0.6)
    if profile.sleep_hours < 5:
        base -= 0.12
    if category_id in {5, 6, 3}:
        base -= 0.08
    return clamp(base, 0.1, 0.95)


def target_duration(profile: Profile, category_id: int) -> float:
    minutes = {"beginner": 30, "intermediate": 40, "advanced": 48}[profile.fitness_level]
    if profile.goal == "weight_loss":
        minutes += 5
    if profile.goal == "muscle_gain":
        minutes += 3
    if profile.goal == "rehabilitation":
        minutes -= 10
    if profile.goal == "flexibility":
        minutes -= 6
    if profile.pain_level >= 7:
        minutes = min(minutes, 20)
    elif profile.pain_level >= 4:
        minutes = min(minutes, 30)
    if profile.sleep_hours < 5:
        minutes -= 6
    if category_id in {5, 6, 3}:
        minutes -= 4
    return clamp(minutes / 60.0, 0.2, 1.0)


def to_features(profile: Profile) -> List[float]:
    age_norm = clamp(profile.age / 100.0, 0.0, 1.0)
    bmi_norm = clamp(profile.bmi / 40.0, 0.0, 1.0)
    fitness_norm = FITNESS_LEVEL_MAP[profile.fitness_level]
    recovery_norm = RECOVERY_PHASE_MAP[profile.recovery_phase]
    days_norm = clamp(1.0 - (profile.days_since_surgery / 180.0), 0.0, 1.0) if profile.is_post_surgery else 0.0
    pain_norm = clamp(profile.pain_level / 10.0, 0.0, 1.0)
    sleep_norm = clamp(profile.sleep_hours / 9.0, 0.0, 1.0)
    num_conditions = clamp(min(len(profile.medical_conditions), 5) / 5.0, 0.0, 1.0)
    return [
        age_norm,
        bmi_norm,
        fitness_norm,
        1.0 if profile.is_post_surgery else 0.0,
        recovery_norm,
        days_norm,
        pain_norm,
        sleep_norm,
        *GOAL_ONE_HOT[profile.goal],
        num_conditions,
        1.0 if profile.has_cardiac else 0.0,
    ]


def generate_dataset(samples_per_cell: int = 22) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Sequence[str]]]:
    features: List[List[float]] = []
    y_category: List[int] = []
    y_intensity: List[float] = []
    y_duration: List[float] = []
    goals_meta: List[str] = []
    fitness_meta: List[str] = []
    age_meta: List[str] = []

    surgery_modes = ["none", "remodeling", "subacute", "acute"]
    for goal in GOALS:
        for fitness in FITNESS_LEVELS:
            for age_bin in AGE_BINS:
                for surgery_mode in surgery_modes:
                    for _ in range(samples_per_cell):
                        profile = generate_profile(goal, fitness, age_bin, surgery_mode)
                        category_id = choose_category(profile)
                        intensity = target_intensity(profile, category_id)
                        duration = target_duration(profile, category_id)
                        features.append(to_features(profile))
                        y_category.append(category_id)
                        y_intensity.append(intensity)
                        y_duration.append(duration)
                        goals_meta.append(goal)
                        fitness_meta.append(fitness)
                        age_meta.append(age_bin)

    metadata = {"goal": goals_meta, "fitness": fitness_meta, "age_bin": age_meta}
    return (
        np.asarray(features, dtype=np.float32),
        np.asarray(y_category, dtype=np.int64),
        np.asarray(y_intensity, dtype=np.float32).reshape(-1, 1),
        np.asarray(y_duration, dtype=np.float32).reshape(-1, 1),
        metadata,
    )


class WorkoutRecommender(nn.Module):
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
        self.category_head = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 7))
        self.intensity_head = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1))
        self.duration_head = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1))

    def forward(self, x: torch.Tensor):
        shared = self.encoder(x)
        return self.category_head(shared), self.intensity_head(shared), self.duration_head(shared)


def evaluate(model: nn.Module, x: torch.Tensor, y_cat: torch.Tensor, y_i: torch.Tensor, y_d: torch.Tensor) -> Dict[str, float]:
    model.eval()
    with torch.no_grad():
        cat_logits, p_i, p_d = model(x)
    cat_pred = torch.argmax(cat_logits, dim=1)
    acc = (cat_pred == y_cat).float().mean().item()
    mse_i = torch.mean((p_i - y_i) ** 2).item()
    mse_d = torch.mean((p_d - y_d) ** 2).item()
    return {"category_acc": acc, "intensity_mse": mse_i, "duration_mse": mse_d}


def subgroup_accuracy(pred: np.ndarray, y: np.ndarray, group: Sequence[str]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for g in sorted(set(group)):
        idx = np.where(np.asarray(group) == g)[0]
        out[g] = float(np.mean(pred[idx] == y[idx])) if len(idx) else 0.0
    return out


def train_and_save() -> None:
    x, y_cat, y_i, y_d, meta = generate_dataset(samples_per_cell=22)
    idx = np.arange(len(x))
    train_idx, val_idx = train_test_split(idx, test_size=0.2, random_state=SEED, stratify=y_cat)

    x_train = torch.tensor(x[train_idx], dtype=torch.float32)
    yc_train = torch.tensor(y_cat[train_idx], dtype=torch.long)
    yi_train = torch.tensor(y_i[train_idx], dtype=torch.float32)
    yd_train = torch.tensor(y_d[train_idx], dtype=torch.float32)
    x_val = torch.tensor(x[val_idx], dtype=torch.float32)
    yc_val = torch.tensor(y_cat[val_idx], dtype=torch.long)
    yi_val = torch.tensor(y_i[val_idx], dtype=torch.float32)
    yd_val = torch.tensor(y_d[val_idx], dtype=torch.float32)

    model = WorkoutRecommender()
    optim = torch.optim.Adam(model.parameters(), lr=8e-4, weight_decay=1e-5)
    ce = nn.CrossEntropyLoss()
    mse = nn.MSELoss()

    batch_size = 128
    n_epochs = 60
    best = {"loss": float("inf"), "epoch": 0, "state": None}
    n_train = x_train.shape[0]

    for epoch in range(1, n_epochs + 1):
        model.train()
        order = torch.randperm(n_train)
        total = 0.0
        for start in range(0, n_train, batch_size):
            b = order[start : start + batch_size]
            xb = x_train[b]
            ycb = yc_train[b]
            yib = yi_train[b]
            ydb = yd_train[b]
            cat_logits, p_i, p_d = model(xb)
            loss = ce(cat_logits, ycb) + 0.5 * mse(p_i, yib) + 0.5 * mse(p_d, ydb)
            optim.zero_grad()
            loss.backward()
            optim.step()
            total += loss.item()

        model.eval()
        with torch.no_grad():
            vc, vi, vd = model(x_val)
            vloss = ce(vc, yc_val) + 0.5 * mse(vi, yi_val) + 0.5 * mse(vd, yd_val)
        if vloss.item() < best["loss"]:
            best["loss"] = float(vloss.item())
            best["epoch"] = epoch
            best["state"] = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if epoch % 10 == 0:
            print(f"epoch={epoch} train_loss={total:.4f} val_loss={vloss.item():.6f}")

    assert best["state"] is not None
    model.load_state_dict(best["state"])

    metrics = evaluate(model, x_val, yc_val, yi_val, yd_val)
    with torch.no_grad():
        val_pred = torch.argmax(model(x_val)[0], dim=1).cpu().numpy()

    goal_acc = subgroup_accuracy(val_pred, y_cat[val_idx], [meta["goal"][i] for i in val_idx])
    fitness_acc = subgroup_accuracy(val_pred, y_cat[val_idx], [meta["fitness"][i] for i in val_idx])
    age_acc = subgroup_accuracy(val_pred, y_cat[val_idx], [meta["age_bin"][i] for i in val_idx])

    def gap(d: Dict[str, float]) -> float:
        values = list(d.values())
        return float(max(values) - min(values)) if values else 0.0

    audit = {
        "overall": metrics,
        "goal_accuracy": goal_acc,
        "fitness_accuracy": fitness_acc,
        "age_bin_accuracy": age_acc,
        "fairness_gaps": {
            "goal_gap": gap(goal_acc),
            "fitness_gap": gap(fitness_acc),
            "age_gap": gap(age_acc),
        },
        "val_size": int(len(val_idx)),
        "train_size": int(len(train_idx)),
    }
    print("audit:", json.dumps(audit, indent=2))

    out_path = Path(__file__).resolve().parents[1] / "models" / "workout_recommender.pt"
    payload = {
        "epoch": best["epoch"],
        "val_loss": best["loss"],
        "model_state_dict": model.state_dict(),
        "metadata": {
            "seed": SEED,
            "feature_names": FEATURE_NAMES,
            "category_names": CATEGORY_NAMES,
            "goals": GOALS,
            "safety_rules_hard_enforced_in_inference": True,
            "audit": audit,
        },
    }
    torch.save(payload, out_path)
    print(f"saved: {out_path}")


if __name__ == "__main__":
    train_and_save()
