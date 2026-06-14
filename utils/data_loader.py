from datetime import date
from pathlib import Path

import pandas as pd


def _load_csv(file_path: str, columns: list[str]) -> pd.DataFrame:
    path = Path(file_path)

    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)

    df.columns = df.columns.str.strip()

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    return df[columns]


def _save_csv(df: pd.DataFrame, file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


# -------------------------
# WEIGHT
# -------------------------

def load_weight_data() -> pd.DataFrame:
    path = Path("data/weight.csv")

    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "weight_kg"])

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    if "weight_kg" not in df.columns and "weight" in df.columns:
        df = df.rename(columns={"weight": "weight_kg"})

    if "date" not in df.columns:
        df["date"] = ""

    if "weight_kg" not in df.columns:
        df["weight_kg"] = ""

    df = df[["date", "weight_kg"]]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    df = df.dropna(subset=["date", "weight_kg"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def get_latest_weight() -> float:
    df = load_weight_data()

    if df.empty:
        return 0.0

    return float(df.iloc[-1]["weight_kg"])


def save_weight(weight: float) -> None:
    df = load_weight_data()

    new_row = pd.DataFrame(
        [
            {
                "date": date.today().isoformat(),
                "weight_kg": float(weight),
            }
        ]
    )

    df = pd.concat([df, new_row], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    df = df.dropna(subset=["date", "weight_kg"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[["date", "weight_kg"]]

    _save_csv(df, "data/weight.csv")


def delete_latest_weight() -> bool:
    df = load_weight_data()

    if df.empty:
        return False

    df = df.iloc[:-1].copy()

    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    df = df[["date", "weight_kg"]]
    _save_csv(df, "data/weight.csv")

    return True


def update_weight_entry(row_index: int, new_date, new_weight: float) -> bool:
    df = load_weight_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df.loc[row_index, "date"] = pd.Timestamp(new_date)
    df.loc[row_index, "weight_kg"] = float(new_weight)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    df = df.dropna(subset=["date", "weight_kg"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[["date", "weight_kg"]]

    _save_csv(df, "data/weight.csv")

    return True


def delete_weight_entry(row_index: int) -> bool:
    df = load_weight_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df = df.drop(index=row_index).reset_index(drop=True)

    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    df = df[["date", "weight_kg"]]
    _save_csv(df, "data/weight.csv")

    return True


# -------------------------
# RUNNING
# -------------------------

RUN_COLUMNS = ["date", "distance_km", "duration_min", "comment"]


def load_runs_data() -> pd.DataFrame:
    df = _load_csv("data/runs.csv", RUN_COLUMNS)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date", "distance_km", "duration_min"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def save_run(run_date, distance_km: float, duration_min: float, comment: str = "") -> None:
    df = load_runs_data()

    new_row = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(run_date),
                "distance_km": float(distance_km),
                "duration_min": float(duration_min),
                "comment": comment.strip(),
            }
        ]
    )

    df = pd.concat([df, new_row], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date", "distance_km", "duration_min"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[RUN_COLUMNS]

    _save_csv(df, "data/runs.csv")


def update_run_entry(
    row_index: int,
    new_date,
    new_distance_km: float,
    new_duration_min: float,
    new_comment: str = "",
) -> bool:
    df = load_runs_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df.loc[row_index, "date"] = pd.Timestamp(new_date)
    df.loc[row_index, "distance_km"] = float(new_distance_km)
    df.loc[row_index, "duration_min"] = float(new_duration_min)
    df.loc[row_index, "comment"] = new_comment.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date", "distance_km", "duration_min"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[RUN_COLUMNS]

    _save_csv(df, "data/runs.csv")

    return True


def delete_run_entry(row_index: int) -> bool:
    df = load_runs_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df = df.drop(index=row_index).reset_index(drop=True)

    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    df = df[RUN_COLUMNS]
    _save_csv(df, "data/runs.csv")

    return True


# -------------------------
# BOXING
# -------------------------

BOXING_COLUMNS = [
    "date",
    "session_type",
    "activities",
    "duration_min",
    "rounds",
    "round_length_min",
    "intensity",
    "feeling_score",
    "focus",
    "sparring",
    "comment",
]


def load_boxing_data() -> pd.DataFrame:
    df = _load_csv("data/boxing.csv", BOXING_COLUMNS)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["session_type"] = df["session_type"].fillna("")
    df["activities"] = df["activities"].fillna("")

    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(90.0)
    df["rounds"] = pd.to_numeric(df["rounds"], errors="coerce").fillna(0)
    df["round_length_min"] = pd.to_numeric(df["round_length_min"], errors="coerce").fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(df["feeling_score"], errors="coerce").fillna(0)

    df["focus"] = df["focus"].fillna("")
    df["sparring"] = df["sparring"].fillna("No")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def save_boxing_session(
    session_date,
    session_type: str,
    rounds: int = 0,
    round_length_min: float = 0.0,
    intensity: int = 7,
    focus: str = "",
    sparring: str = "No",
    comment: str = "",
    activities: str = "",
    duration_min: float = 90.0,
    feeling_score: int = 7,
) -> None:
    df = load_boxing_data()

    new_row = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(session_date),
                "session_type": session_type.strip(),
                "activities": activities.strip(),
                "duration_min": float(duration_min),
                "rounds": int(rounds),
                "round_length_min": float(round_length_min),
                "intensity": int(intensity),
                "feeling_score": int(feeling_score),
                "focus": focus.strip(),
                "sparring": sparring,
                "comment": comment.strip(),
            }
        ]
    )

    df = pd.concat([df, new_row], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(90.0)
    df["rounds"] = pd.to_numeric(df["rounds"], errors="coerce").fillna(0)
    df["round_length_min"] = pd.to_numeric(df["round_length_min"], errors="coerce").fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(df["feeling_score"], errors="coerce").fillna(0)

    df["session_type"] = df["session_type"].fillna("")
    df["activities"] = df["activities"].fillna("")
    df["focus"] = df["focus"].fillna("")
    df["sparring"] = df["sparring"].fillna("No")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[BOXING_COLUMNS]

    _save_csv(df, "data/boxing.csv")


def update_boxing_entry(
    row_index: int,
    new_date,
    new_session_type: str,
    new_rounds: int = 0,
    new_round_length_min: float = 0.0,
    new_intensity: int = 7,
    new_focus: str = "",
    new_sparring: str = "No",
    new_comment: str = "",
    new_activities: str = "",
    new_duration_min: float = 90.0,
    new_feeling_score: int = 7,
) -> bool:
    df = load_boxing_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df.loc[row_index, "date"] = pd.Timestamp(new_date)
    df.loc[row_index, "session_type"] = new_session_type.strip()
    df.loc[row_index, "activities"] = new_activities.strip()
    df.loc[row_index, "duration_min"] = float(new_duration_min)
    df.loc[row_index, "rounds"] = int(new_rounds)
    df.loc[row_index, "round_length_min"] = float(new_round_length_min)
    df.loc[row_index, "intensity"] = int(new_intensity)
    df.loc[row_index, "feeling_score"] = int(new_feeling_score)
    df.loc[row_index, "focus"] = new_focus.strip()
    df.loc[row_index, "sparring"] = new_sparring
    df.loc[row_index, "comment"] = new_comment.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(90.0)
    df["rounds"] = pd.to_numeric(df["rounds"], errors="coerce").fillna(0)
    df["round_length_min"] = pd.to_numeric(df["round_length_min"], errors="coerce").fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(df["feeling_score"], errors="coerce").fillna(0)

    df["session_type"] = df["session_type"].fillna("")
    df["activities"] = df["activities"].fillna("")
    df["focus"] = df["focus"].fillna("")
    df["sparring"] = df["sparring"].fillna("No")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[BOXING_COLUMNS]

    _save_csv(df, "data/boxing.csv")

    return True


def delete_boxing_entry(row_index: int) -> bool:
    df = load_boxing_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df = df.drop(index=row_index).reset_index(drop=True)

    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    df = df[BOXING_COLUMNS]
    _save_csv(df, "data/boxing.csv")

    return True


# -------------------------
# GYM
# -------------------------

GYM_COLUMNS = [
    "date",
    "workout_type",
    "exercise",
    "sets",
    "reps",
    "weight_kg",
    "load_adjustment_kg",
    "bodyweight_kg",
    "intensity",
    "feeling_score",
    "comment",
]


def load_gym_data() -> pd.DataFrame:
    df = _load_csv("data/gym.csv", GYM_COLUMNS)

    for column in GYM_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["workout_type"] = df["workout_type"].fillna("")
    df["exercise"] = df["exercise"].fillna("")

    df["sets"] = pd.to_numeric(df["sets"], errors="coerce").fillna(0)
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce").fillna(0)
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce").fillna(0)
    df["load_adjustment_kg"] = pd.to_numeric(
        df["load_adjustment_kg"],
        errors="coerce",
    ).fillna(0)
    df["bodyweight_kg"] = pd.to_numeric(
        df["bodyweight_kg"],
        errors="coerce",
    ).fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(df["feeling_score"], errors="coerce").fillna(0)

    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def save_gym_entry(
    workout_date,
    workout_type: str,
    exercise: str,
    sets: int,
    reps: int,
    weight_kg: float,
    load_adjustment_kg: float = 0.0,
    bodyweight_kg: float = 0.0,
    intensity: int = 7,
    feeling_score: int = 7,
    comment: str = "",
) -> None:
    df = load_gym_data()

    new_row = pd.DataFrame(
        [
            {
                "date": pd.Timestamp(workout_date),
                "workout_type": workout_type.strip(),
                "exercise": exercise.strip(),
                "sets": int(sets),
                "reps": int(reps),
                "weight_kg": float(weight_kg),
                "load_adjustment_kg": float(load_adjustment_kg),
                "bodyweight_kg": float(bodyweight_kg),
                "intensity": int(intensity),
                "feeling_score": int(feeling_score),
                "comment": comment.strip(),
            }
        ]
    )

    df = pd.concat([df, new_row], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sets"] = pd.to_numeric(df["sets"], errors="coerce").fillna(0)
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce").fillna(0)
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce").fillna(0)
    df["load_adjustment_kg"] = pd.to_numeric(
        df["load_adjustment_kg"],
        errors="coerce",
    ).fillna(0)
    df["bodyweight_kg"] = pd.to_numeric(
        df["bodyweight_kg"],
        errors="coerce",
    ).fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(df["feeling_score"], errors="coerce").fillna(0)

    df["workout_type"] = df["workout_type"].fillna("")
    df["exercise"] = df["exercise"].fillna("")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[GYM_COLUMNS]

    _save_csv(df, "data/gym.csv")


def update_gym_entry(
    row_index: int,
    new_date,
    new_workout_type: str,
    new_exercise: str,
    new_sets: int,
    new_reps: int,
    new_weight_kg: float,
    new_load_adjustment_kg: float = 0.0,
    new_bodyweight_kg: float = 0.0,
    new_intensity: int = 7,
    new_feeling_score: int = 7,
    new_comment: str = "",
) -> bool:
    df = load_gym_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df.loc[row_index, "date"] = pd.Timestamp(new_date)
    df.loc[row_index, "workout_type"] = new_workout_type.strip()
    df.loc[row_index, "exercise"] = new_exercise.strip()
    df.loc[row_index, "sets"] = int(new_sets)
    df.loc[row_index, "reps"] = int(new_reps)
    df.loc[row_index, "weight_kg"] = float(new_weight_kg)
    df.loc[row_index, "load_adjustment_kg"] = float(new_load_adjustment_kg)
    df.loc[row_index, "bodyweight_kg"] = float(new_bodyweight_kg)
    df.loc[row_index, "intensity"] = int(new_intensity)
    df.loc[row_index, "feeling_score"] = int(new_feeling_score)
    df.loc[row_index, "comment"] = new_comment.strip()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["sets"] = pd.to_numeric(df["sets"], errors="coerce").fillna(0)
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce").fillna(0)
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce").fillna(0)
    df["load_adjustment_kg"] = pd.to_numeric(
        df["load_adjustment_kg"],
        errors="coerce",
    ).fillna(0)
    df["bodyweight_kg"] = pd.to_numeric(
        df["bodyweight_kg"],
        errors="coerce",
    ).fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(df["feeling_score"], errors="coerce").fillna(0)

    df["workout_type"] = df["workout_type"].fillna("")
    df["exercise"] = df["exercise"].fillna("")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[GYM_COLUMNS]

    _save_csv(df, "data/gym.csv")

    return True


def delete_gym_entry(row_index: int) -> bool:
    df = load_gym_data().reset_index(drop=True)

    if df.empty:
        return False

    if row_index < 0 or row_index >= len(df):
        return False

    df = df.drop(index=row_index).reset_index(drop=True)

    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    df = df[GYM_COLUMNS]
    _save_csv(df, "data/gym.csv")

    return True