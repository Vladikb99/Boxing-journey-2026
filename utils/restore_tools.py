from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import pandas as pd

from utils.export_tools import create_full_backup_zip


RESTORABLE_FILES = [
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
    return Path.cwd()


def _data_dir() -> Path:
    return _project_root() / "data"


def _safety_backup_dir() -> Path:
    return _data_dir() / "restore_safety_backups"


def inspect_restore_zip(zip_bytes: bytes) -> pd.DataFrame:
    """
    Inspects an uploaded backup zip and checks which files can be restored.

    Returns a dataframe that can be displayed in Streamlit.
    """
    rows = []

    try:
        with ZipFile(BytesIO(zip_bytes), "r") as zip_file:
            zip_names = zip_file.namelist()

            for file_name in RESTORABLE_FILES:
                zip_path = _find_file_in_zip(zip_names, file_name)

                if zip_path is None:
                    rows.append(
                        {
                            "file": file_name,
                            "status": "Missing",
                            "rows": 0,
                            "zip_path": "-",
                            "size_kb": 0.0,
                            "restore_allowed": False,
                            "notes": "File was not found inside the backup zip.",
                        }
                    )
                    continue

                info = zip_file.getinfo(zip_path)
                file_bytes = zip_file.read(zip_path)

                validation = _validate_file(file_name, file_bytes)

                rows.append(
                    {
                        "file": file_name,
                        "status": validation["status"],
                        "rows": validation["rows"],
                        "zip_path": zip_path,
                        "size_kb": round(info.file_size / 1024, 2),
                        "restore_allowed": validation["restore_allowed"],
                        "notes": validation["notes"],
                    }
                )

    except BadZipFile:
        rows.append(
            {
                "file": "backup.zip",
                "status": "Error",
                "rows": 0,
                "zip_path": "-",
                "size_kb": 0.0,
                "restore_allowed": False,
                "notes": "Uploaded file is not a valid zip file.",
            }
        )
    except Exception as error:
        rows.append(
            {
                "file": "backup.zip",
                "status": "Error",
                "rows": 0,
                "zip_path": "-",
                "size_kb": 0.0,
                "restore_allowed": False,
                "notes": f"Could not inspect zip file: {error}",
            }
        )

    return pd.DataFrame(rows)


def restore_selected_files_from_zip(
    zip_bytes: bytes,
    selected_files: list[str],
) -> tuple[bool, str]:
    """
    Restores selected files from a backup zip.

    Safety behavior:
    1. Creates a full backup of the current data first.
    2. Stores that backup in data/restore_safety_backups.
    3. Restores only allowed files from the uploaded zip.
    """
    if not selected_files:
        return False, "No files selected for restore."

    preview_df = inspect_restore_zip(zip_bytes)

    if preview_df.empty:
        return False, "Could not inspect backup zip."

    allowed_rows = preview_df[preview_df["restore_allowed"] == True].copy()
    allowed_files = set(allowed_rows["file"].astype(str).tolist())

    invalid_files = [file_name for file_name in selected_files if file_name not in allowed_files]

    if invalid_files:
        return (
            False,
            "Some selected files are not safe to restore: "
            + ", ".join(invalid_files),
        )

    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    safety_backup_path = _create_restore_safety_backup()

    try:
        with ZipFile(BytesIO(zip_bytes), "r") as zip_file:
            for file_name in selected_files:
                matching_row = allowed_rows[allowed_rows["file"] == file_name]

                if matching_row.empty:
                    continue

                zip_path = str(matching_row.iloc[0]["zip_path"])
                file_bytes = zip_file.read(zip_path)

                target_path = data_dir / file_name
                target_path.write_bytes(file_bytes)

    except Exception as error:
        return (
            False,
            f"Restore failed. Safety backup was created at: {safety_backup_path}. Error: {error}",
        )

    restored_text = ", ".join(selected_files)

    return (
        True,
        f"Restore complete. Restored: {restored_text}. Safety backup saved at: {safety_backup_path}",
    )


def _create_restore_safety_backup() -> Path:
    """
    Creates a backup of current data before restore.
    """
    safety_dir = _safety_backup_dir()
    safety_dir.mkdir(parents=True, exist_ok=True)

    backup_filename, backup_bytes = create_full_backup_zip()
    safety_path = safety_dir / backup_filename

    safety_path.write_bytes(backup_bytes)

    return safety_path


def _find_file_in_zip(zip_names: list[str], file_name: str) -> str | None:
    """
    Supports both:
    - data/weight.csv
    - weight.csv

    This makes restore tolerant if backup structure changes later.
    """
    exact_paths = [
        f"data/{file_name}",
        file_name,
    ]

    for path in exact_paths:
        if path in zip_names:
            return path

    normalized_target = f"/{file_name}"

    for path in zip_names:
        normalized_path = path.replace("\\", "/")

        if normalized_path.endswith(normalized_target):
            return path

    return None


def _validate_file(file_name: str, file_bytes: bytes) -> dict:
    suffix = Path(file_name).suffix.lower()

    if suffix == ".csv":
        return _validate_csv_file(file_name, file_bytes)

    if suffix == ".json":
        return _validate_json_file(file_bytes)

    if suffix == ".txt":
        return _validate_text_file(file_bytes)

    return {
        "status": "Warning",
        "rows": 0,
        "restore_allowed": False,
        "notes": "Unsupported file type.",
    }


def _validate_csv_file(file_name: str, file_bytes: bytes) -> dict:
    if len(file_bytes) == 0:
        return {
            "status": "Error",
            "rows": 0,
            "restore_allowed": False,
            "notes": "CSV file is empty.",
        }

    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except Exception as error:
        return {
            "status": "Error",
            "rows": 0,
            "restore_allowed": False,
            "notes": f"Could not read CSV file: {error}",
        }

    expected_columns = EXPECTED_CSV_COLUMNS.get(file_name, [])
    missing_columns = [column for column in expected_columns if column not in df.columns]

    if missing_columns:
        return {
            "status": "Warning",
            "rows": len(df),
            "restore_allowed": True,
            "notes": "Readable CSV, but missing columns: " + ", ".join(missing_columns),
        }

    return {
        "status": "Ready",
        "rows": len(df),
        "restore_allowed": True,
        "notes": "Ready to restore.",
    }


def _validate_json_file(file_bytes: bytes) -> dict:
    if len(file_bytes) == 0:
        return {
            "status": "Error",
            "rows": 0,
            "restore_allowed": False,
            "notes": "JSON file is empty.",
        }

    try:
        data = json.loads(file_bytes.decode("utf-8"))
    except Exception as error:
        return {
            "status": "Error",
            "rows": 0,
            "restore_allowed": False,
            "notes": f"Could not read JSON file: {error}",
        }

    if isinstance(data, dict):
        rows = len(data)
    elif isinstance(data, list):
        rows = len(data)
    else:
        rows = 1

    return {
        "status": "Ready",
        "rows": rows,
        "restore_allowed": True,
        "notes": "Ready to restore.",
    }


def _validate_text_file(file_bytes: bytes) -> dict:
    if len(file_bytes) == 0:
        return {
            "status": "Error",
            "rows": 0,
            "restore_allowed": False,
            "notes": "Text file is empty.",
        }

    try:
        text = file_bytes.decode("utf-8")
    except Exception as error:
        return {
            "status": "Error",
            "rows": 0,
            "restore_allowed": False,
            "notes": f"Could not read text file: {error}",
        }

    rows = len([line for line in text.splitlines() if line.strip()])

    return {
        "status": "Ready",
        "rows": rows,
        "restore_allowed": True,
        "notes": "Ready to restore.",
    }