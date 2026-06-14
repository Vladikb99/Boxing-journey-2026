from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


DATA_FILES = [
    "weight.csv",
    "runs.csv",
    "boxing.csv",
    "gym.csv",
    "settings.json",
    "quotes.txt",
]


EXPECTED_CSV_COLUMNS = {
    "weight.csv": ["date", "weight_kg"],
    "runs.csv": ["date", "distance_km", "duration_min", "comment"],
    "boxing.csv": [
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
    ],
    "gym.csv": [
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
    ],
}


WEEKLY_TARGETS = {
    "weight_logs": 1,
    "boxing_sessions": 3,
    "sparring_rounds": 6,
    "runs": 2,
    "running_km": 8.0,
    "gym_sessions": 2,
    "active_days": 4,
}


# ============================================================
# PATH HELPERS
# ============================================================

def _project_root() -> Path:
    """
    Returns the project root.

    This assumes the Streamlit app is started from the main project folder.
    """
    return Path.cwd()


def _data_dir() -> Path:
    return _project_root() / "data"


def _now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _add_file_to_zip(zip_file: ZipFile, file_path: Path, zip_path: str) -> bool:
    """
    Adds a file to the zip if it exists.
    Returns True if added, False if missing.
    """
    if not file_path.exists() or not file_path.is_file():
        return False

    zip_file.write(file_path, zip_path)
    return True


# ============================================================
# BACKUP EXPORT
# ============================================================

def create_full_backup_zip() -> tuple[str, bytes]:
    """
    Creates a full backup zip of the data folder.

    Returns:
        filename, zip_bytes
    """
    data_dir = _data_dir()
    filename = f"boxing_journey_full_backup_{_now_stamp()}.zip"

    zip_buffer = BytesIO()

    added_files = []
    missing_files = []

    with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as zip_file:
        for file_name in DATA_FILES:
            file_path = data_dir / file_name
            zip_path = f"data/{file_name}"

            added = _add_file_to_zip(zip_file, file_path, zip_path)

            if added:
                added_files.append(zip_path)
            else:
                missing_files.append(zip_path)

        manifest = _create_backup_manifest(added_files, missing_files)
        zip_file.writestr("backup_manifest.txt", manifest)

        health_report = create_data_health_report_text()
        zip_file.writestr("data_health_report.txt", health_report)

    zip_buffer.seek(0)
    return filename, zip_buffer.getvalue()


def _create_backup_manifest(added_files: list[str], missing_files: list[str]) -> str:
    lines = [
        "Boxing Journey 2026 - Full Backup",
        "",
        f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Included files:",
    ]

    if added_files:
        for file_name in added_files:
            lines.append(f"- {file_name}")
    else:
        lines.append("- No files found")

    lines.extend(["", "Missing files:"])

    if missing_files:
        for file_name in missing_files:
            lines.append(f"- {file_name}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "Restore note:",
            "To restore manually, unzip this backup and copy the files inside the data folder back into your app's data folder.",
        ]
    )

    return "\n".join(lines)


# ============================================================
# DATA HEALTH CHECK
# ============================================================

def get_data_health_check() -> pd.DataFrame:
    """
    Checks whether important data files exist, have rows, expected columns,
    valid date columns, and readable content.

    Returns a dataframe that can be displayed directly in Streamlit.
    """
    data_dir = _data_dir()
    rows = []

    for file_name in DATA_FILES:
        file_path = data_dir / file_name
        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            rows.append(_check_csv_file(file_name, file_path))
        elif suffix == ".json":
            rows.append(_check_json_file(file_name, file_path))
        elif suffix == ".txt":
            rows.append(_check_txt_file(file_name, file_path))
        else:
            rows.append(_check_generic_file(file_name, file_path))

    return pd.DataFrame(rows)


def create_data_health_report_text() -> str:
    """
    Creates a readable text report of the data health check.
    This is added to backup files and can also be shown in Settings.
    """
    health_df = get_data_health_check()

    lines = [
        "Boxing Journey 2026 - Data Health Report",
        "",
        f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    if health_df.empty:
        lines.append("No data health information available.")
        return "\n".join(lines)

    for _, row in health_df.iterrows():
        lines.extend(
            [
                f"File: {row.get('file', '')}",
                f"Status: {row.get('status', '')}",
                f"Rows: {row.get('rows', '')}",
                f"Last date: {row.get('last_date', '')}",
                f"Size: {row.get('size_kb', '')} KB",
                f"Missing columns: {row.get('missing_columns', '')}",
                f"Notes: {row.get('notes', '')}",
                "",
            ]
        )

    return "\n".join(lines)


def _base_health_row(file_name: str, file_path: Path) -> dict:
    exists = file_path.exists() and file_path.is_file()

    return {
        "file": file_name,
        "status": "Missing",
        "rows": 0,
        "last_date": "-",
        "size_kb": 0.0,
        "missing_columns": "-",
        "notes": "File not found.",
        "exists": exists,
    }


def _check_csv_file(file_name: str, file_path: Path) -> dict:
    row = _base_health_row(file_name, file_path)

    if not row["exists"]:
        return row

    row["size_kb"] = round(file_path.stat().st_size / 1024, 2)

    if file_path.stat().st_size == 0:
        row["status"] = "Empty"
        row["notes"] = "File exists, but it is empty."
        return row

    try:
        df = pd.read_csv(file_path)
    except Exception as error:
        row["status"] = "Error"
        row["notes"] = f"Could not read CSV file: {error}"
        return row

    row["rows"] = len(df)

    expected_columns = EXPECTED_CSV_COLUMNS.get(file_name, [])
    missing_columns = [column for column in expected_columns if column not in df.columns]

    if missing_columns:
        row["missing_columns"] = ", ".join(missing_columns)
    else:
        row["missing_columns"] = "None"

    if "date" in df.columns and not df.empty:
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()

        if not dates.empty:
            row["last_date"] = str(dates.max().date())
        else:
            row["last_date"] = "-"
            row["notes"] = "Date column exists, but no valid dates were found."

    if df.empty:
        row["status"] = "Empty"
        row["notes"] = "CSV file exists, but has no rows."
    elif missing_columns:
        row["status"] = "Warning"
        row["notes"] = "Some expected columns are missing."
    else:
        row["status"] = "OK"
        row["notes"] = "File looks good."

    return row


def _check_json_file(file_name: str, file_path: Path) -> dict:
    row = _base_health_row(file_name, file_path)

    if not row["exists"]:
        return row

    row["size_kb"] = round(file_path.stat().st_size / 1024, 2)

    if file_path.stat().st_size == 0:
        row["status"] = "Empty"
        row["notes"] = "File exists, but it is empty."
        return row

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as error:
        row["status"] = "Error"
        row["notes"] = f"Could not read JSON file: {error}"
        return row

    if isinstance(data, dict):
        row["rows"] = len(data)
        row["status"] = "OK"
        row["notes"] = "JSON file looks good."
    else:
        row["rows"] = 1
        row["status"] = "Warning"
        row["notes"] = "JSON file is readable, but it is not a dictionary."

    row["missing_columns"] = "None"
    return row


def _check_txt_file(file_name: str, file_path: Path) -> dict:
    row = _base_health_row(file_name, file_path)

    if not row["exists"]:
        return row

    row["size_kb"] = round(file_path.stat().st_size / 1024, 2)

    if file_path.stat().st_size == 0:
        row["status"] = "Empty"
        row["notes"] = "File exists, but it is empty."
        return row

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = [line for line in file.readlines() if line.strip()]
    except Exception as error:
        row["status"] = "Error"
        row["notes"] = f"Could not read text file: {error}"
        return row

    row["rows"] = len(lines)
    row["missing_columns"] = "None"
    row["status"] = "OK"
    row["notes"] = "Text file looks good."

    return row


def _check_generic_file(file_name: str, file_path: Path) -> dict:
    row = _base_health_row(file_name, file_path)

    if not row["exists"]:
        return row

    row["size_kb"] = round(file_path.stat().st_size / 1024, 2)
    row["status"] = "OK"
    row["missing_columns"] = "None"
    row["notes"] = "File exists."

    return row


# ============================================================
# AI REVIEW EXPORT
# ============================================================

def create_ai_review_export_zip(days: int = 7) -> tuple[str, bytes]:
    """
    Creates an AI review export.

    This zip includes:
    - all data files
    - one readable AI summary text file
    - one data health report
    """
    data_dir = _data_dir()
    filename = f"boxing_journey_ai_review_{_now_stamp()}.zip"

    zip_buffer = BytesIO()

    with ZipFile(zip_buffer, "w", ZIP_DEFLATED) as zip_file:
        for file_name in DATA_FILES:
            file_path = data_dir / file_name
            zip_path = f"data/{file_name}"
            _add_file_to_zip(zip_file, file_path, zip_path)

        summary = create_ai_review_summary(days=days)
        zip_file.writestr("ai_review_summary.txt", summary)

        health_report = create_data_health_report_text()
        zip_file.writestr("data_health_report.txt", health_report)

    zip_buffer.seek(0)
    return filename, zip_buffer.getvalue()


def create_ai_review_summary(days: int = 7) -> str:
    """
    Creates a coaching-focused text summary from recent training data.
    This is meant to be sent to ChatGPT for weekly boxing feedback.
    """
    data_dir = _data_dir()

    weight_df = _read_csv_safe(data_dir / "weight.csv")
    runs_df = _read_csv_safe(data_dir / "runs.csv")
    boxing_df = _read_csv_safe(data_dir / "boxing.csv")
    gym_df = _read_csv_safe(data_dir / "gym.csv")

    latest_date = _get_latest_date([weight_df, runs_df, boxing_df, gym_df])

    if latest_date is None:
        start_date = None
        period_text = "No valid dates found."
    else:
        start_date = latest_date - pd.Timedelta(days=days - 1)
        period_text = f"{start_date.date()} to {latest_date.date()}"

    weight_recent = _filter_recent(weight_df, start_date)
    runs_recent = _filter_recent(runs_df, start_date)
    boxing_recent = _filter_recent(boxing_df, start_date)
    gym_recent = _filter_recent(gym_df, start_date)

    metrics = _build_review_metrics(
        weight_recent=weight_recent,
        runs_recent=runs_recent,
        boxing_recent=boxing_recent,
        gym_recent=gym_recent,
    )

    training_score = _calculate_training_score(metrics)
    coaching_flags = _build_coaching_flags(metrics)

    lines = [
        "Boxing Journey 2026 - AI Review Export",
        "",
        f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Review period: {period_text}",
        "",
        "Purpose:",
        "Use this file together with the CSV files to review boxing progress, training balance, gas tank work, recovery, and next-week focus.",
        "",
        "====================",
        "WEEKLY TRAINING SCORE",
        "====================",
        f"Training score: {training_score['score']}/100",
        f"Rating: {training_score['rating']}",
        "",
        "Score breakdown:",
    ]

    for item in training_score["breakdown"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "====================",
            "KEY WEEKLY NUMBERS",
            "====================",
            f"Active days: {metrics['active_days']}",
            f"Weight logs: {metrics['weight_logs']}",
            f"Boxing sessions: {metrics['boxing_sessions']}",
            f"Sparring sessions: {metrics['sparring_sessions']}",
            f"Sparring rounds: {metrics['sparring_rounds']}",
            f"Sparring minutes: {metrics['sparring_minutes']:.1f}",
            f"Runs: {metrics['runs']}",
            f"Running distance: {metrics['running_km']:.2f} km",
            f"Running duration: {metrics['running_minutes']:.1f} min",
            f"Average running pace: {_format_pace(metrics['average_pace'])}",
            f"Gym entries: {metrics['gym_entries']}",
            f"Gym training days: {metrics['gym_days']}",
            f"Gym volume: {metrics['gym_volume']:.0f} kg",
            "",
            "====================",
            "COACHING FLAGS",
            "====================",
        ]
    )

    if coaching_flags:
        for flag in coaching_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("- No major warning flags from the logged data.")

    lines.extend(
        [
            "",
            "====================",
            "WEIGHT",
            "====================",
            _summarize_weight(weight_recent),
            "",
            "====================",
            "RUNNING / GAS TANK",
            "====================",
            _summarize_running(runs_recent),
            "",
            "====================",
            "BOXING",
            "====================",
            _summarize_boxing(boxing_recent),
            "",
            "====================",
            "GYM / STRENGTH",
            "====================",
            _summarize_gym(gym_recent),
            "",
            "====================",
            "COMMENTS LOGGED THIS PERIOD",
            "====================",
            _collect_recent_comments(
                runs_recent=runs_recent,
                boxing_recent=boxing_recent,
                gym_recent=gym_recent,
            ),
            "",
            "====================",
            "QUESTIONS FOR AI COACH REVIEW",
            "====================",
            "- What should I focus on next week to improve my boxing gas tank?",
            "- Is my sparring volume increasing in a smart way?",
            "- Is my running volume enough for boxing conditioning?",
            "- Am I balancing boxing, running, gym, weight loss, and recovery well?",
            "- Based on my comments, what technical or mental pattern should I fix first?",
            "- What should I do differently next week?",
            "",
            "====================",
            "DATA HEALTH",
            "====================",
            create_data_health_report_text(),
        ]
    )

    return "\n".join(lines)


# ============================================================
# AI REVIEW METRICS
# ============================================================

def _build_review_metrics(
    weight_recent: pd.DataFrame,
    runs_recent: pd.DataFrame,
    boxing_recent: pd.DataFrame,
    gym_recent: pd.DataFrame,
) -> dict:
    active_days = _get_active_days(
        weight_recent=weight_recent,
        runs_recent=runs_recent,
        boxing_recent=boxing_recent,
        gym_recent=gym_recent,
    )

    running_km, running_minutes, average_pace = _get_running_totals(runs_recent)
    sparring_sessions, sparring_rounds, sparring_minutes = _get_sparring_totals(boxing_recent)
    gym_volume = _get_gym_volume(gym_recent)

    return {
        "active_days": active_days,
        "weight_logs": len(weight_recent),
        "boxing_sessions": len(boxing_recent),
        "sparring_sessions": sparring_sessions,
        "sparring_rounds": sparring_rounds,
        "sparring_minutes": sparring_minutes,
        "runs": len(runs_recent),
        "running_km": running_km,
        "running_minutes": running_minutes,
        "average_pace": average_pace,
        "gym_entries": len(gym_recent),
        "gym_days": _count_unique_dates(gym_recent),
        "gym_volume": gym_volume,
    }


def _calculate_training_score(metrics: dict) -> dict:
    """
    Simple 100-point weekly training score.
    It is not a scientific performance model. It is a practical consistency score.
    """
    breakdown = []
    score = 0

    score += _score_target(
        value=metrics["active_days"],
        target=WEEKLY_TARGETS["active_days"],
        points=15,
        label="Active days",
        breakdown=breakdown,
    )

    score += _score_target(
        value=metrics["weight_logs"],
        target=WEEKLY_TARGETS["weight_logs"],
        points=10,
        label="Weight logging",
        breakdown=breakdown,
    )

    score += _score_target(
        value=metrics["boxing_sessions"],
        target=WEEKLY_TARGETS["boxing_sessions"],
        points=25,
        label="Boxing sessions",
        breakdown=breakdown,
    )

    score += _score_target(
        value=metrics["sparring_rounds"],
        target=WEEKLY_TARGETS["sparring_rounds"],
        points=15,
        label="Sparring rounds",
        breakdown=breakdown,
    )

    score += _score_target(
        value=metrics["runs"],
        target=WEEKLY_TARGETS["runs"],
        points=15,
        label="Running sessions",
        breakdown=breakdown,
    )

    score += _score_target(
        value=metrics["running_km"],
        target=WEEKLY_TARGETS["running_km"],
        points=10,
        label="Running distance",
        breakdown=breakdown,
    )

    score += _score_target(
        value=metrics["gym_days"],
        target=WEEKLY_TARGETS["gym_sessions"],
        points=10,
        label="Gym sessions",
        breakdown=breakdown,
    )

    score = int(round(min(score, 100)))

    if score >= 85:
        rating = "Strong training week"
    elif score >= 70:
        rating = "Good training week"
    elif score >= 50:
        rating = "Moderate training week"
    else:
        rating = "Low training week"

    return {
        "score": score,
        "rating": rating,
        "breakdown": breakdown,
    }


def _score_target(
    value: float,
    target: float,
    points: int,
    label: str,
    breakdown: list[str],
) -> float:
    if target <= 0:
        earned = points
    else:
        earned = min(value / target, 1.0) * points

    breakdown.append(f"{label}: {value:g}/{target:g} target -> {earned:.1f}/{points} pts")

    return earned


def _build_coaching_flags(metrics: dict) -> list[str]:
    flags = []

    if metrics["boxing_sessions"] == 0:
        flags.append("No boxing sessions logged. This week does not move the main boxing goal much.")

    if metrics["boxing_sessions"] >= 3 and metrics["runs"] == 0:
        flags.append("Boxing volume is present, but no running was logged. Gas tank development may be limited.")

    if metrics["sparring_rounds"] == 0 and metrics["boxing_sessions"] >= 2:
        flags.append("Boxing was active, but no sparring rounds were logged. Sparring-specific progress is hard to evaluate.")

    if metrics["sparring_rounds"] >= 10 and metrics["gym_days"] >= 2:
        flags.append("High sparring plus gym load. Watch recovery, sleep, soreness, and sharpness.")

    if metrics["runs"] >= 3 and metrics["boxing_sessions"] >= 3 and metrics["gym_days"] >= 2:
        flags.append("High total workload. Good if recovery is strong, risky if sleep or energy is poor.")

    if metrics["active_days"] <= 2:
        flags.append("Low active-day count. Consistency is the main limiter this period.")

    if metrics["running_km"] > 0 and metrics["average_pace"] is not None and metrics["average_pace"] > 8.0:
        flags.append("Running pace is slow. That can be fine for easy aerobic work, but add structured intervals later if gas tank is the goal.")

    if metrics["gym_volume"] > 0 and metrics["boxing_sessions"] == 0:
        flags.append("Gym work was logged, but no boxing. Strength work should support boxing, not replace it.")

    return flags


# ============================================================
# SUMMARY HELPERS
# ============================================================

def _get_latest_date(dataframes: list[pd.DataFrame]) -> pd.Timestamp | None:
    latest_dates = []

    for df in dataframes:
        if df.empty or "date" not in df.columns:
            continue

        dates = pd.to_datetime(df["date"], errors="coerce").dropna()

        if not dates.empty:
            latest_dates.append(dates.max())

    if not latest_dates:
        return None

    return max(latest_dates)


def _filter_recent(df: pd.DataFrame, start_date: pd.Timestamp | None) -> pd.DataFrame:
    if df.empty or "date" not in df.columns or start_date is None:
        return df.copy()

    result = df.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result = result.dropna(subset=["date"])
    result = result[result["date"] >= start_date]
    result = result.sort_values("date").reset_index(drop=True)

    return result


def _count_unique_dates(df: pd.DataFrame) -> int:
    if df.empty or "date" not in df.columns:
        return 0

    dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date

    return len(set(dates.tolist()))


def _get_active_days(
    weight_recent: pd.DataFrame,
    runs_recent: pd.DataFrame,
    boxing_recent: pd.DataFrame,
    gym_recent: pd.DataFrame,
) -> int:
    dates = []

    for df in [weight_recent, runs_recent, boxing_recent, gym_recent]:
        if df.empty or "date" not in df.columns:
            continue

        parsed_dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date.tolist()
        dates.extend(parsed_dates)

    return len(set(dates))


def _get_running_totals(runs_df: pd.DataFrame) -> tuple[float, float, float | None]:
    if runs_df.empty:
        return 0.0, 0.0, None

    if "distance_km" not in runs_df.columns or "duration_min" not in runs_df.columns:
        return 0.0, 0.0, None

    df = runs_df.copy()
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce").fillna(0)
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(0)

    total_distance = float(df["distance_km"].sum())
    total_duration = float(df["duration_min"].sum())

    if total_distance <= 0:
        return total_distance, total_duration, None

    average_pace = total_duration / total_distance

    return total_distance, total_duration, average_pace


def _is_sparring_row(row: pd.Series) -> bool:
    session_type = str(row.get("session_type", "")).lower()
    activities = str(row.get("activities", "")).lower()
    sparring = str(row.get("sparring", "")).lower()

    return (
        "sparring" in session_type
        or "sparring" in activities
        or sparring in ["yes", "true", "1"]
    )


def _get_sparring_totals(boxing_df: pd.DataFrame) -> tuple[int, int, float]:
    if boxing_df.empty:
        return 0, 0, 0.0

    df = boxing_df.copy()

    for column in ["rounds", "round_length_min"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    sparring_df = df[df.apply(_is_sparring_row, axis=1)]

    if sparring_df.empty:
        return 0, 0, 0.0

    sparring_sessions = len(sparring_df)

    if "rounds" not in sparring_df.columns:
        return sparring_sessions, 0, 0.0

    sparring_rounds = int(sparring_df["rounds"].sum())

    if "round_length_min" in sparring_df.columns:
        sparring_minutes = float(
            (sparring_df["rounds"] * sparring_df["round_length_min"]).sum()
        )
    else:
        sparring_minutes = 0.0

    return sparring_sessions, sparring_rounds, sparring_minutes


def _get_gym_volume(gym_df: pd.DataFrame) -> float:
    required_columns = ["sets", "reps", "weight_kg"]

    if gym_df.empty or not all(column in gym_df.columns for column in required_columns):
        return 0.0

    df = gym_df.copy()

    for column in required_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return float((df["sets"] * df["reps"] * df["weight_kg"]).sum())


def _format_pace(pace_min_per_km: float | None) -> str:
    if pace_min_per_km is None or pd.isna(pace_min_per_km):
        return "-"

    minutes = int(pace_min_per_km)
    seconds = int(round((pace_min_per_km - minutes) * 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d} min/km"


def _format_change(value: float) -> str:
    return f"{value:+.1f}"


# ============================================================
# SECTION SUMMARIES
# ============================================================

def _summarize_weight(df: pd.DataFrame) -> str:
    if df.empty or "weight_kg" not in df.columns:
        return "No weight data in this period."

    result = df.copy()
    result["weight_kg"] = pd.to_numeric(result["weight_kg"], errors="coerce")
    result = result.dropna(subset=["weight_kg"])

    if result.empty:
        return "No valid weight entries in this period."

    start_weight = float(result.iloc[0]["weight_kg"])
    end_weight = float(result.iloc[-1]["weight_kg"])
    change = end_weight - start_weight

    lines = [
        f"Entries: {len(result)}",
        f"Start of period: {start_weight:.1f} kg",
        f"Latest: {end_weight:.1f} kg",
        f"Change this period: {_format_change(change)} kg",
    ]

    if change < -0.8:
        lines.append("Note: Weight dropped quickly this period. Check energy, recovery, and training quality.")
    elif change > 0.8:
        lines.append("Note: Weight increased this period. Could be food, water, creatine, or lower activity.")
    else:
        lines.append("Note: Weight movement is moderate.")

    return "\n".join(lines)


def _summarize_running(df: pd.DataFrame) -> str:
    if df.empty:
        return "No running data in this period."

    if "distance_km" not in df.columns or "duration_min" not in df.columns:
        return "Running file exists, but expected columns are missing."

    result = df.copy()
    result["distance_km"] = pd.to_numeric(result["distance_km"], errors="coerce")
    result["duration_min"] = pd.to_numeric(result["duration_min"], errors="coerce")
    result = result.dropna(subset=["distance_km", "duration_min"])

    if result.empty:
        return "No valid running entries in this period."

    total_distance = float(result["distance_km"].sum())
    total_duration = float(result["duration_min"].sum())
    average_pace = total_duration / total_distance if total_distance > 0 else None
    longest_run = float(result["distance_km"].max()) if not result.empty else 0.0

    lines = [
        f"Runs: {len(result)}",
        f"Total distance: {total_distance:.2f} km",
        f"Total duration: {total_duration:.1f} min",
        f"Average pace: {_format_pace(average_pace)}",
        f"Longest run: {longest_run:.2f} km",
    ]

    if len(result) >= 2:
        lines.append("Boxing gas tank note: Running frequency is useful this period.")
    elif len(result) == 1:
        lines.append("Boxing gas tank note: One run helps, but two sessions per week is a better base.")
    else:
        lines.append("Boxing gas tank note: No roadwork logged.")

    return "\n".join(lines)


def _summarize_boxing(df: pd.DataFrame) -> str:
    if df.empty:
        return "No boxing data in this period."

    result = df.copy()

    for column in ["duration_min", "rounds", "round_length_min", "intensity", "feeling_score"]:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0)

    total_sessions = len(result)

    total_duration = 0.0
    if "duration_min" in result.columns:
        total_duration = float(result["duration_min"].sum())

    sparring_sessions, sparring_rounds, sparring_minutes = _get_sparring_totals(result)

    avg_intensity = None
    if "intensity" in result.columns:
        intensity_values = result["intensity"].replace(0, pd.NA).dropna()
        if not intensity_values.empty:
            avg_intensity = float(intensity_values.mean())

    avg_feeling = None
    if "feeling_score" in result.columns:
        feeling_values = result["feeling_score"].replace(0, pd.NA).dropna()
        if not feeling_values.empty:
            avg_feeling = float(feeling_values.mean())

    lines = [
        f"Boxing sessions: {total_sessions}",
        f"Total boxing duration: {total_duration:.1f} min",
        f"Sparring sessions: {sparring_sessions}",
        f"Sparring rounds: {sparring_rounds}",
        f"Sparring minutes: {sparring_minutes:.1f} min",
    ]

    if avg_intensity is not None:
        lines.append(f"Average intensity: {avg_intensity:.1f}/10")

    if avg_feeling is not None:
        lines.append(f"Average feeling: {avg_feeling:.1f}/10")

    if sparring_rounds >= 6:
        lines.append("Sparring note: Good sparring exposure this period.")
    elif sparring_rounds > 0:
        lines.append("Sparring note: Sparring logged, but volume is still low.")
    else:
        lines.append("Sparring note: No sparring rounds logged.")

    if "focus" in result.columns:
        focus_values = result["focus"].dropna().astype(str)
        focus_values = [focus for focus in focus_values if focus.strip()]
        if focus_values:
            lines.append("")
            lines.append("Focus themes:")
            for focus in focus_values[-5:]:
                lines.append(f"- {focus}")

    return "\n".join(lines)


def _summarize_gym(df: pd.DataFrame) -> str:
    if df.empty:
        return "No gym data in this period."

    required_columns = ["sets", "reps", "weight_kg"]

    if not all(column in df.columns for column in required_columns):
        return "Gym file exists, but expected columns are missing."

    result = df.copy()

    for column in required_columns + ["intensity", "feeling_score"]:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0)

    result["volume_kg"] = result["sets"] * result["reps"] * result["weight_kg"]

    total_volume = float(result["volume_kg"].sum())
    gym_days = _count_unique_dates(result)

    lines = [
        f"Gym entries: {len(result)}",
        f"Gym training days: {gym_days}",
        f"Total lifted volume: {total_volume:.0f} kg",
    ]

    if "exercise" in result.columns:
        exercise_volume = (
            result.groupby("exercise")["volume_kg"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )

        if not exercise_volume.empty:
            lines.append("")
            lines.append("Top exercises by volume:")
            for exercise, volume in exercise_volume.items():
                lines.append(f"- {exercise}: {volume:.0f} kg")

    if "workout_type" in result.columns:
        workout_counts = result["workout_type"].dropna().astype(str).value_counts()

        if not workout_counts.empty:
            lines.append("")
            lines.append("Workout types:")
            for workout_type, count in workout_counts.items():
                lines.append(f"- {workout_type}: {count}")

    if "intensity" in result.columns:
        avg_intensity = result["intensity"].replace(0, pd.NA).dropna().mean()
        if not pd.isna(avg_intensity):
            lines.append(f"\nAverage intensity: {float(avg_intensity):.1f}/10")

    if "feeling_score" in result.columns:
        avg_feeling = result["feeling_score"].replace(0, pd.NA).dropna().mean()
        if not pd.isna(avg_feeling):
            lines.append(f"Average feeling: {float(avg_feeling):.1f}/10")

    return "\n".join(lines)


def _collect_recent_comments(
    runs_recent: pd.DataFrame,
    boxing_recent: pd.DataFrame,
    gym_recent: pd.DataFrame,
) -> str:
    lines = []

    _append_comments(
        lines=lines,
        title="Running comments",
        df=runs_recent,
        comment_column="comment",
        max_items=5,
    )

    _append_comments(
        lines=lines,
        title="Boxing comments",
        df=boxing_recent,
        comment_column="comment",
        max_items=8,
    )

    _append_comments(
        lines=lines,
        title="Gym comments",
        df=gym_recent,
        comment_column="comment",
        max_items=5,
    )

    if not lines:
        return "No comments logged this period."

    return "\n".join(lines)


def _append_comments(
    lines: list[str],
    title: str,
    df: pd.DataFrame,
    comment_column: str,
    max_items: int,
) -> None:
    if df.empty or comment_column not in df.columns:
        return

    comments = df[comment_column].dropna().astype(str)
    comments = [comment.strip() for comment in comments if comment.strip()]

    if not comments:
        return

    if lines:
        lines.append("")

    lines.append(title + ":")

    for comment in comments[-max_items:]:
        lines.append(f"- {comment}")