from __future__ import annotations

import pandas as pd


def clean_date_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df.copy()

    cleaned_df = df.copy()
    cleaned_df["date"] = pd.to_datetime(cleaned_df["date"], errors="coerce")
    cleaned_df = cleaned_df.dropna(subset=["date"])

    return cleaned_df


def last_7_days_df(df: pd.DataFrame) -> pd.DataFrame:
    cleaned_df = clean_date_column(df)

    if cleaned_df.empty:
        return cleaned_df

    today = pd.Timestamp.today().normalize()
    week_start = today - pd.Timedelta(days=6)

    return cleaned_df[
        (cleaned_df["date"] >= week_start)
        & (cleaned_df["date"] <= today)
    ].copy()


def is_sparring_row(row: pd.Series) -> bool:
    session_type = str(row.get("session_type", "")).lower()
    activities = str(row.get("activities", "")).lower()
    sparring = str(row.get("sparring", "")).lower()

    return (
        "sparring" in session_type
        or "sparring" in activities
        or sparring in ["yes", "true", "1"]
    )


def get_total_sparring_rounds(boxing_df: pd.DataFrame) -> int:
    if boxing_df.empty or "rounds" not in boxing_df.columns:
        return 0

    df = boxing_df.copy()
    df["rounds"] = pd.to_numeric(df["rounds"], errors="coerce").fillna(0)

    sparring_df = df[df.apply(is_sparring_row, axis=1)]

    if sparring_df.empty:
        return 0

    return int(sparring_df["rounds"].sum())


def get_total_sparring_sessions(boxing_df: pd.DataFrame) -> int:
    if boxing_df.empty:
        return 0

    sparring_df = boxing_df[boxing_df.apply(is_sparring_row, axis=1)]

    return len(sparring_df)


def get_total_running_distance(runs_df: pd.DataFrame) -> float:
    if runs_df.empty or "distance_km" not in runs_df.columns:
        return 0.0

    df = runs_df.copy()
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce").fillna(0)

    return float(df["distance_km"].sum())


def get_longest_run(runs_df: pd.DataFrame) -> float:
    if runs_df.empty or "distance_km" not in runs_df.columns:
        return 0.0

    df = runs_df.copy()
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce").fillna(0)

    if df.empty:
        return 0.0

    return float(df["distance_km"].max())


def get_total_gym_volume(gym_df: pd.DataFrame) -> float:
    required_columns = ["sets", "reps", "weight_kg"]

    if gym_df.empty or not all(column in gym_df.columns for column in required_columns):
        return 0.0

    df = gym_df.copy()

    for column in required_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df["volume_kg"] = df["sets"] * df["reps"] * df["weight_kg"]

    return float(df["volume_kg"].sum())


def get_biggest_logged_lift(gym_df: pd.DataFrame) -> float:
    if gym_df.empty or "weight_kg" not in gym_df.columns:
        return 0.0

    df = gym_df.copy()
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce").fillna(0)

    if df.empty:
        return 0.0

    return float(df["weight_kg"].max())


def get_training_days_this_week(
    weight_week_df: pd.DataFrame,
    runs_week_df: pd.DataFrame,
    boxing_week_df: pd.DataFrame,
    gym_week_df: pd.DataFrame,
) -> int:
    all_dates = []

    for df in [weight_week_df, runs_week_df, boxing_week_df, gym_week_df]:
        if df.empty or "date" not in df.columns:
            continue

        dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date.tolist()
        all_dates.extend(dates)

    return len(set(all_dates))


def get_total_training_days(
    weight_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    boxing_df: pd.DataFrame,
    gym_df: pd.DataFrame,
) -> int:
    all_dates = []

    for df in [weight_df, runs_df, boxing_df, gym_df]:
        if df.empty or "date" not in df.columns:
            continue

        dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date.tolist()
        all_dates.extend(dates)

    return len(set(all_dates))


def build_achievements(
    weight_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    boxing_df: pd.DataFrame,
    gym_df: pd.DataFrame,
    current_weight: float,
    start_weight: float,
    goal_weight: float,
) -> list[dict]:
    weight_df = clean_date_column(weight_df)
    runs_df = clean_date_column(runs_df)
    boxing_df = clean_date_column(boxing_df)
    gym_df = clean_date_column(gym_df)

    weight_week_df = last_7_days_df(weight_df)
    runs_week_df = last_7_days_df(runs_df)
    boxing_week_df = last_7_days_df(boxing_df)
    gym_week_df = last_7_days_df(gym_df)

    total_weight_logs = len(weight_df)
    total_runs = len(runs_df)
    total_boxing_sessions = len(boxing_df)
    total_gym_sessions = len(gym_df)

    weekly_weight_logs = len(weight_week_df)
    weekly_runs = len(runs_week_df)
    weekly_boxing_sessions = len(boxing_week_df)
    weekly_gym_sessions = len(gym_week_df)

    total_logs = (
        total_weight_logs
        + total_runs
        + total_boxing_sessions
        + total_gym_sessions
    )

    total_training_days = get_total_training_days(
        weight_df=weight_df,
        runs_df=runs_df,
        boxing_df=boxing_df,
        gym_df=gym_df,
    )

    training_days_this_week = get_training_days_this_week(
        weight_week_df=weight_week_df,
        runs_week_df=runs_week_df,
        boxing_week_df=boxing_week_df,
        gym_week_df=gym_week_df,
    )

    total_run_distance = get_total_running_distance(runs_df)
    longest_run = get_longest_run(runs_df)

    total_sparring_sessions = get_total_sparring_sessions(boxing_df)
    total_sparring_rounds = get_total_sparring_rounds(boxing_df)

    total_gym_volume = get_total_gym_volume(gym_df)
    biggest_logged_lift = get_biggest_logged_lift(gym_df)

    if current_weight > 0:
        weight_lost = max(start_weight - current_weight, 0.0)
        under_85_now = current_weight < 85.0
        under_80_now = current_weight < 80.0
        goal_reached_now = current_weight <= goal_weight
    else:
        weight_lost = 0.0
        under_85_now = False
        under_80_now = False
        goal_reached_now = False

    balanced_week = (
        weekly_weight_logs >= 1
        and weekly_runs >= 1
        and weekly_boxing_sessions >= 2
    )

    fighter_week = (
        weekly_runs >= 2
        and weekly_boxing_sessions >= 3
    )

    full_athlete_week = (
        weekly_weight_logs >= 1
        and weekly_runs >= 2
        and weekly_boxing_sessions >= 3
        and weekly_gym_sessions >= 2
    )

    return [
        # ====================================================
        # GENERAL
        # ====================================================
        {
            "id": "general_first_log",
            "category": "General",
            "name": "Journey started",
            "detail": "Logged your first entry in the app.",
            "kind": "Milestone",
            "unlocked": total_logs >= 1,
        },
        {
            "id": "general_10_logs",
            "category": "General",
            "name": "10 total logs",
            "detail": "Reached 10 total logs across the app.",
            "kind": "Milestone",
            "unlocked": total_logs >= 10,
        },
        {
            "id": "general_30_logs",
            "category": "General",
            "name": "30 total logs",
            "detail": "Reached 30 total logs across the app.",
            "kind": "Milestone",
            "unlocked": total_logs >= 30,
        },
        {
            "id": "general_100_logs",
            "category": "General",
            "name": "100 total logs",
            "detail": "Reached 100 total logs across the app.",
            "kind": "Milestone",
            "unlocked": total_logs >= 100,
        },
        {
            "id": "general_7_training_days",
            "category": "General",
            "name": "7 training days",
            "detail": "Logged training on 7 different dates.",
            "kind": "Milestone",
            "unlocked": total_training_days >= 7,
        },
        {
            "id": "general_30_training_days",
            "category": "General",
            "name": "30 training days",
            "detail": "Logged training on 30 different dates.",
            "kind": "Milestone",
            "unlocked": total_training_days >= 30,
        },
        {
            "id": "general_balanced_week",
            "category": "General",
            "name": "Balanced week",
            "detail": "Weight, running, and boxing all logged in the last 7 days.",
            "kind": "Active",
            "unlocked": balanced_week,
        },
        {
            "id": "general_fighter_week",
            "category": "General",
            "name": "Fighter week",
            "detail": "Logged at least 2 runs and 3 boxing sessions in the last 7 days.",
            "kind": "Active",
            "unlocked": fighter_week,
        },
        {
            "id": "general_full_athlete_week",
            "category": "General",
            "name": "Full athlete week",
            "detail": "Weight, boxing, running, and gym all active in the last 7 days.",
            "kind": "Active",
            "unlocked": full_athlete_week,
        },
        {
            "id": "general_4_active_days_week",
            "category": "General",
            "name": "4 active days this week",
            "detail": "Logged activity on at least 4 different dates in the last 7 days.",
            "kind": "Active",
            "unlocked": training_days_this_week >= 4,
        },

        # ====================================================
        # WEIGHT
        # ====================================================
        {
            "id": "weight_first_weigh_in",
            "category": "Weight",
            "name": "First weigh-in",
            "detail": "Logged your first bodyweight entry.",
            "kind": "Milestone",
            "unlocked": total_weight_logs >= 1,
        },
        {
            "id": "weight_logged_this_week",
            "category": "Weight",
            "name": "Weight checked this week",
            "detail": "Logged weight at least once in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_weight_logs >= 1,
        },
        {
            "id": "weight_7_logs",
            "category": "Weight",
            "name": "7 weigh-ins",
            "detail": "Logged bodyweight 7 times.",
            "kind": "Milestone",
            "unlocked": total_weight_logs >= 7,
        },
        {
            "id": "weight_30_logs",
            "category": "Weight",
            "name": "30 weigh-ins",
            "detail": "Logged bodyweight 30 times.",
            "kind": "Milestone",
            "unlocked": total_weight_logs >= 30,
        },
        {
            "id": "weight_lost_1kg",
            "category": "Weight",
            "name": "Lost 1 kg",
            "detail": "Dropped at least 1 kg from start weight.",
            "kind": "Milestone",
            "unlocked": weight_lost >= 1.0,
        },
        {
            "id": "weight_lost_5kg",
            "category": "Weight",
            "name": "Lost 5 kg",
            "detail": "Dropped at least 5 kg from start weight.",
            "kind": "Milestone",
            "unlocked": weight_lost >= 5.0,
        },
        {
            "id": "weight_lost_10kg",
            "category": "Weight",
            "name": "Lost 10 kg",
            "detail": "Dropped at least 10 kg from start weight.",
            "kind": "Milestone",
            "unlocked": weight_lost >= 10.0,
        },
        {
            "id": "weight_under_85",
            "category": "Weight",
            "name": "Under 85 kg",
            "detail": "Current logged weight is under 85 kg.",
            "kind": "Active",
            "unlocked": under_85_now,
        },
        {
            "id": "weight_under_80",
            "category": "Weight",
            "name": "Under 80 kg",
            "detail": "Current logged weight is under 80 kg.",
            "kind": "Active",
            "unlocked": under_80_now,
        },
        {
            "id": "weight_goal_reached",
            "category": "Weight",
            "name": "Goal weight reached",
            "detail": "Current logged weight is at or below goal weight.",
            "kind": "Active",
            "unlocked": goal_reached_now,
        },

        # ====================================================
        # RUNNING
        # ====================================================
        {
            "id": "run_first_run",
            "category": "Running",
            "name": "First run",
            "detail": "Logged your first roadwork session.",
            "kind": "Milestone",
            "unlocked": total_runs >= 1,
        },
        {
            "id": "run_active_week",
            "category": "Running",
            "name": "Roadwork active",
            "detail": "Logged at least one run in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_runs >= 1,
        },
        {
            "id": "run_2_in_week",
            "category": "Running",
            "name": "2 runs in 7 days",
            "detail": "Logged two or more runs in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_runs >= 2,
        },
        {
            "id": "run_3_in_week",
            "category": "Running",
            "name": "3 runs in 7 days",
            "detail": "Logged three or more runs in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_runs >= 3,
        },
        {
            "id": "run_10km_total",
            "category": "Running",
            "name": "10 km total",
            "detail": "Reached 10 total running kilometers.",
            "kind": "Milestone",
            "unlocked": total_run_distance >= 10.0,
        },
        {
            "id": "run_50km_total",
            "category": "Running",
            "name": "50 km total",
            "detail": "Reached 50 total running kilometers.",
            "kind": "Milestone",
            "unlocked": total_run_distance >= 50.0,
        },
        {
            "id": "run_100km_total",
            "category": "Running",
            "name": "100 km total",
            "detail": "Reached 100 total running kilometers.",
            "kind": "Milestone",
            "unlocked": total_run_distance >= 100.0,
        },
        {
            "id": "run_first_5k",
            "category": "Running",
            "name": "First 5 km run",
            "detail": "Logged a single run of 5 km or longer.",
            "kind": "Milestone",
            "unlocked": longest_run >= 5.0,
        },
        {
            "id": "run_first_10k",
            "category": "Running",
            "name": "First 10 km run",
            "detail": "Logged a single run of 10 km or longer.",
            "kind": "Milestone",
            "unlocked": longest_run >= 10.0,
        },

        # ====================================================
        # BOXING
        # ====================================================
        {
            "id": "boxing_first_session",
            "category": "Boxing",
            "name": "First boxing session",
            "detail": "Logged your first boxing session.",
            "kind": "Milestone",
            "unlocked": total_boxing_sessions >= 1,
        },
        {
            "id": "boxing_active_week",
            "category": "Boxing",
            "name": "Boxing active week",
            "detail": "Logged at least two boxing sessions in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_boxing_sessions >= 2,
        },
        {
            "id": "boxing_full_week",
            "category": "Boxing",
            "name": "Full boxing week",
            "detail": "Logged three or more boxing sessions in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_boxing_sessions >= 3,
        },
        {
            "id": "boxing_10_sessions",
            "category": "Boxing",
            "name": "10 boxing sessions",
            "detail": "Logged 10 boxing sessions.",
            "kind": "Milestone",
            "unlocked": total_boxing_sessions >= 10,
        },
        {
            "id": "boxing_25_sessions",
            "category": "Boxing",
            "name": "25 boxing sessions",
            "detail": "Logged 25 boxing sessions.",
            "kind": "Milestone",
            "unlocked": total_boxing_sessions >= 25,
        },
        {
            "id": "boxing_50_sessions",
            "category": "Boxing",
            "name": "50 boxing sessions",
            "detail": "Logged 50 boxing sessions.",
            "kind": "Milestone",
            "unlocked": total_boxing_sessions >= 50,
        },
        {
            "id": "boxing_first_sparring",
            "category": "Boxing",
            "name": "First sparring logged",
            "detail": "Logged your first sparring session.",
            "kind": "Milestone",
            "unlocked": total_sparring_sessions >= 1,
        },
        {
            "id": "boxing_10_sparring_rounds",
            "category": "Boxing",
            "name": "10 sparring rounds",
            "detail": "Reached 10 total sparring rounds.",
            "kind": "Milestone",
            "unlocked": total_sparring_rounds >= 10,
        },
        {
            "id": "boxing_25_sparring_rounds",
            "category": "Boxing",
            "name": "25 sparring rounds",
            "detail": "Reached 25 total sparring rounds.",
            "kind": "Milestone",
            "unlocked": total_sparring_rounds >= 25,
        },
        {
            "id": "boxing_50_sparring_rounds",
            "category": "Boxing",
            "name": "50 sparring rounds",
            "detail": "Reached 50 total sparring rounds.",
            "kind": "Milestone",
            "unlocked": total_sparring_rounds >= 50,
        },
        {
            "id": "boxing_100_sparring_rounds",
            "category": "Boxing",
            "name": "100 sparring rounds",
            "detail": "Reached 100 total sparring rounds.",
            "kind": "Milestone",
            "unlocked": total_sparring_rounds >= 100,
        },

        # ====================================================
        # GYM
        # ====================================================
        {
            "id": "gym_first_session",
            "category": "Gym",
            "name": "First gym session",
            "detail": "Logged your first gym session.",
            "kind": "Milestone",
            "unlocked": total_gym_sessions >= 1,
        },
        {
            "id": "gym_active_week",
            "category": "Gym",
            "name": "Gym active week",
            "detail": "Logged at least one gym session in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_gym_sessions >= 1,
        },
        {
            "id": "gym_2_in_week",
            "category": "Gym",
            "name": "2 gym sessions in 7 days",
            "detail": "Logged two or more gym sessions in the last 7 days.",
            "kind": "Active",
            "unlocked": weekly_gym_sessions >= 2,
        },
        {
            "id": "gym_10_sessions",
            "category": "Gym",
            "name": "10 gym sessions",
            "detail": "Logged 10 gym sessions.",
            "kind": "Milestone",
            "unlocked": total_gym_sessions >= 10,
        },
        {
            "id": "gym_25_sessions",
            "category": "Gym",
            "name": "25 gym sessions",
            "detail": "Logged 25 gym sessions.",
            "kind": "Milestone",
            "unlocked": total_gym_sessions >= 25,
        },
        {
            "id": "gym_10k_volume",
            "category": "Gym",
            "name": "10,000 kg volume",
            "detail": "Reached 10,000 kg total logged gym volume.",
            "kind": "Milestone",
            "unlocked": total_gym_volume >= 10_000,
        },
        {
            "id": "gym_50k_volume",
            "category": "Gym",
            "name": "50,000 kg volume",
            "detail": "Reached 50,000 kg total logged gym volume.",
            "kind": "Milestone",
            "unlocked": total_gym_volume >= 50_000,
        },
        {
            "id": "gym_100k_volume",
            "category": "Gym",
            "name": "100,000 kg volume",
            "detail": "Reached 100,000 kg total logged gym volume.",
            "kind": "Milestone",
            "unlocked": total_gym_volume >= 100_000,
        },
        {
            "id": "gym_60kg_lift",
            "category": "Gym",
            "name": "60 kg lift logged",
            "detail": "Logged at least one exercise with 60 kg or more.",
            "kind": "Milestone",
            "unlocked": biggest_logged_lift >= 60,
        },
        {
            "id": "gym_100kg_lift",
            "category": "Gym",
            "name": "100 kg lift logged",
            "detail": "Logged at least one exercise with 100 kg or more.",
            "kind": "Milestone",
            "unlocked": biggest_logged_lift >= 100,
        },
    ]