import json
from json import JSONDecodeError
from pathlib import Path


SETTINGS_PATH = Path("data/settings.json")

DEFAULT_SETTINGS = {
    "user_name": "Vladik",
    "height_m": 1.84,
    "start_weight": 86.7,
    "goal_weight": 75.0,
}


def load_settings() -> dict:
    if not SETTINGS_PATH.exists() or SETTINGS_PATH.stat().st_size == 0:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
            settings = json.load(file)

    except JSONDecodeError:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value

    return settings


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)