from datetime import date
from pathlib import Path

import pandas as pd


def _load_csv(file_path: str, columns: list[str]) -> pd.DataFrame:
    path = Path(file_path)

    if not path.exists():
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(path)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    return df


def load_weight_data() -> pd.DataFrame:
    df = _load_csv(
        "data/weight.csv",
        ["date", "weight_kg"]
    )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    df = df.dropna(subset=["date", "weight_kg"])
    df = df.sort_values("date")

    return df


def load_runs_data() -> pd.DataFrame:
    df = _load_csv(
        "data/runs.csv",
        ["date", "distance_km", "duration_min", "comment"]
    )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date", "distance_km", "duration_min"])
    df = df.sort_values("date")

    return df


def load_boxing_data() -> pd.DataFrame:
    df = _load_csv(
        "data/boxing.csv",
        ["date", "session_type", "comment"]
    )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["session_type"] = df["session_type"].fillna("")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    return df


def load_gym_data() -> pd.DataFrame:
    df = _load_csv(
        "data/gym.csv",
        ["date", "exercise", "sets", "reps", "weight_kg", "comment"]
    )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["exercise"] = df["exercise"].fillna("")
    df["sets"] = pd.to_numeric(df["sets"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    return df


def get_latest_weight() -> float:
    df = load_weight_data()

    if df.empty:
        return 0.0

    return float(df.iloc[-1]["weight_kg"])


def save_weight(weight: float) -> None:
    df = load_weight_data()

    new_row = {
        "date": date.today().isoformat(),
        "weight_kg": weight
    }

    df.loc[len(df)] = new_row
    df.to_csv("data/weight.csv", index=False)