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

    lines.extend(
        [
            "",
            "Missing files:",
        ]
    )

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
    Creates a weekly AI review export.

    This zip includes:
    - all data files
    - one readable AI summary text file
    - one data health report

    You can send this zip to ChatGPT later for weekly comments.
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
    Creates a simple text summary from the latest training data.
    This is meant for weekly check-ins with AI.
    """
    data_dir = _data_dir()

    weight_df = _read_csv_safe(data_dir / "weight.csv")
    runs_df = _read_csv_safe(data_dir / "runs.csv")
    boxing_df = _read_csv_safe(data_dir / "boxing.csv")
    gym_df = _read_csv_safe(data_dir / "gym.csv")

    latest_date = _get_latest_date([weight_df, runs_df, boxing_df, gym_df])

    if latest_date is None:
        period_text = "No valid dates found."
        start_date = None
    else:
        start_date = latest_date - pd.Timedelta(days=days - 1)
        period_text = f"{start_date.date()} to {latest_date.date()}"

    weight_recent = _filter_recent(weight_df, start_date)
    runs_recent = _filter_recent(runs_df, start_date)
    boxing_recent = _filter_recent(boxing_df, start_date)
    gym_recent = _filter_recent(gym_df, start_date)

    lines = [
        "Boxing Journey 2026 - AI Review Export",
        "",
        f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Review period: {period_text}",
        "",
        "Use this summary together with the CSV files to review training progress.",
        "",
        "====================",
        "DATA HEALTH",
        "====================",
        create_data_health_report_text(),
        "",
        "====================",
        "WEIGHT",
        "====================",
        _summarize_weight(weight_recent),
        "",
        "====================",
        "RUNNING",
        "====================",
        _summarize_running(runs_recent),
        "",
        "====================",
        "BOXING",
        "====================",
        _summarize_boxing(boxing_recent),
        "",
        "====================",
        "GYM",
        "====================",
        _summarize_gym(gym_recent),
        "",
        "====================",
        "AI COACHING QUESTIONS",
        "====================",
        "- What should I focus on next week?",
        "- Is my sparring volume improving?",
        "- Is my running helping my boxing gas tank?",
        "- Am I balancing boxing, gym, running, and recovery well?",
        "- What should I change based on this data?",
    ]

    return "\n".join(lines)


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

    return (
        f"Entries: {len(result)}\n"
        f"Start weight: {start_weight:.1f} kg\n"
        f"Latest weight: {end_weight:.1f} kg\n"
        f"Change: {change:+.1f} kg"
    )


def _summarize_running(df: pd.DataFrame) -> str:
    if df.empty:
        return "No running data in this period."

    result = df.copy()

    if "distance_km" not in result.columns or "duration_min" not in result.columns:
        return "Running file exists, but expected columns are missing."

    result["distance_km"] = pd.to_numeric(result["distance_km"], errors="coerce")
    result["duration_min"] = pd.to_numeric(result["duration_min"], errors="coerce")
    result = result.dropna(subset=["distance_km", "duration_min"])

    if result.empty:
        return "No valid running entries in this period."

    total_distance = float(result["distance_km"].sum())
    total_duration = float(result["duration_min"].sum())

    avg_pace = None
    if total_distance > 0:
        avg_pace = total_duration / total_distance

    lines = [
        f"Runs: {len(result)}",
        f"Total distance: {total_distance:.2f} km",
        f"Total duration: {total_duration:.1f} min",
    ]

    if avg_pace is not None:
        lines.append(f"Average pace: {avg_pace:.2f} min/km")

    if "comment" in result.columns:
        comments = result["comment"].dropna().astype(str)
        comments = [comment for comment in comments if comment.strip()]
        if comments:
            lines.append("")
            lines.append("Run comments:")
            for comment in comments[-5:]:
                lines.append(f"- {comment}")

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

    sparring_df = pd.DataFrame()

    if "sparring" in result.columns:
        sparring_df = result[result["sparring"].astype(str).str.lower().isin(["yes", "true", "1"])]
    elif "activities" in result.columns:
        sparring_df = result[result["activities"].astype(str).str.contains("sparring", case=False, na=False)]

    total_sparring_rounds = 0
    total_sparring_minutes = 0.0

    if not sparring_df.empty and "rounds" in sparring_df.columns:
        total_sparring_rounds = int(sparring_df["rounds"].sum())

        if "round_length_min" in sparring_df.columns:
            total_sparring_minutes = float(
                (sparring_df["rounds"] * sparring_df["round_length_min"]).sum()
            )

    avg_intensity = None
    if "intensity" in result.columns and not result["intensity"].empty:
        avg_intensity = float(result["intensity"].replace(0, pd.NA).dropna().mean())

    avg_feeling = None
    if "feeling_score" in result.columns and not result["feeling_score"].empty:
        avg_feeling = float(result["feeling_score"].replace(0, pd.NA).dropna().mean())

    lines = [
        f"Boxing entries: {total_sessions}",
        f"Total boxing duration: {total_duration:.1f} min",
        f"Sparring entries: {len(sparring_df)}",
        f"Sparring rounds: {total_sparring_rounds}",
        f"Sparring minutes: {total_sparring_minutes:.1f} min",
    ]

    if avg_intensity is not None and not pd.isna(avg_intensity):
        lines.append(f"Average intensity: {avg_intensity:.1f}/10")

    if avg_feeling is not None and not pd.isna(avg_feeling):
        lines.append(f"Average feeling: {avg_feeling:.1f}/10")

    if "comment" in result.columns:
        comments = result["comment"].dropna().astype(str)
        comments = [comment for comment in comments if comment.strip()]
        if comments:
            lines.append("")
            lines.append("Boxing comments:")
            for comment in comments[-5:]:
                lines.append(f"- {comment}")

    return "\n".join(lines)


def _summarize_gym(df: pd.DataFrame) -> str:
    if df.empty:
        return "No gym data in this period."

    result = df.copy()

    required_columns = ["sets", "reps", "weight_kg"]

    for column in required_columns + ["intensity", "feeling_score"]:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0)

    if not all(column in result.columns for column in required_columns):
        return "Gym file exists, but expected columns are missing."

    result["volume_kg"] = result["sets"] * result["reps"] * result["weight_kg"]

    total_volume = float(result["volume_kg"].sum())

    lines = [
        f"Gym entries: {len(result)}",
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

    if "comment" in result.columns:
        comments = result["comment"].dropna().astype(str)
        comments = [comment for comment in comments if comment.strip()]
        if comments:
            lines.append("")
            lines.append("Gym comments:")
            for comment in comments[-5:]:
                lines.append(f"- {comment}")

    return "\n".join(lines)