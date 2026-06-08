from datetime import date, timedelta

import pandas as pd


def calculate_weight_change(df: pd.DataFrame) -> str:
    if len(df) >= 2:
        latest_weight = df.iloc[-1]["weight_kg"]
        previous_weight = df.iloc[-2]["weight_kg"]

        change = latest_weight - previous_weight

        return f"{change:+.1f} kg"

    return "No previous data"


def get_last_7_days_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    today = date.today()
    start_date = today - timedelta(days=6)

    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(today)

    return df[
        (df["date"] >= start_date) &
        (df["date"] <= end_date)
    ]


def calculate_last_7_day_weight_change(weight_df: pd.DataFrame) -> str:
    last_7_days_df = get_last_7_days_data(weight_df)

    if len(last_7_days_df) >= 2:
        start_weight = last_7_days_df.iloc[0]["weight_kg"]
        latest_weight = last_7_days_df.iloc[-1]["weight_kg"]

        change = latest_weight - start_weight

        return f"{change:+.1f} kg"

    return calculate_weight_change(weight_df)


def calculate_weekly_run_distance(runs_df: pd.DataFrame) -> str:
    last_7_days_df = get_last_7_days_data(runs_df)

    if last_7_days_df.empty:
        return "0 km"

    total_distance = last_7_days_df["distance_km"].sum()

    return f"{total_distance:.1f} km"


def calculate_weekly_boxing_sessions(boxing_df: pd.DataFrame) -> str:
    last_7_days_df = get_last_7_days_data(boxing_df)

    return str(len(last_7_days_df))


def calculate_weekly_gym_sessions(gym_df: pd.DataFrame) -> str:
    last_7_days_df = get_last_7_days_data(gym_df)

    if last_7_days_df.empty:
        return "0"

    unique_training_days = last_7_days_df["date"].dt.date.nunique()

    return str(unique_training_days)


def format_pace(minutes_per_km: float) -> str:
    minutes = int(minutes_per_km)
    seconds = int(round((minutes_per_km - minutes) * 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}/km"


def get_latest_run_summary(runs_df: pd.DataFrame) -> tuple[str, str]:
    if runs_df.empty:
        return "No run", "No run logged"

    latest_run = runs_df.iloc[-1]

    distance = float(latest_run["distance_km"])
    duration = float(latest_run["duration_min"])

    if distance <= 0:
        return f"{distance:.1f} km", "Invalid distance"

    pace = duration / distance

    return f"{distance:g} km", format_pace(pace)