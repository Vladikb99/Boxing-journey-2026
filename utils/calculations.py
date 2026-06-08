from datetime import date, timedelta

import pandas as pd


def calculate_weight_change(df):
    if len(df) >= 2:
        latest_weight = df.iloc[-1]["weight_kg"]
        previous_weight = df.iloc[-2]["weight_kg"]

        change = latest_weight - previous_weight

        return f"{change:+.1f} kg"

    return "No previous data"


def get_current_week_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_start = pd.Timestamp(week_start)
    week_end = pd.Timestamp(week_end)

    return df[
        (df["date"] >= week_start) &
        (df["date"] <= week_end)
    ]


def calculate_weekly_run_distance(runs_df: pd.DataFrame) -> str:
    week_df = get_current_week_data(runs_df)

    if week_df.empty:
        return "0 km"

    total_distance = week_df["distance_km"].sum()

    return f"{total_distance:.1f} km"


def calculate_weekly_boxing_sessions(boxing_df: pd.DataFrame) -> str:
    week_df = get_current_week_data(boxing_df)

    return str(len(week_df))


def calculate_weekly_gym_sessions(gym_df: pd.DataFrame) -> str:
    week_df = get_current_week_data(gym_df)

    if week_df.empty:
        return "0"

    unique_training_days = week_df["date"].dt.date.nunique()

    return str(unique_training_days)