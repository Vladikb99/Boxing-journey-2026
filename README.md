# Boxing Journey 2026

A personal Streamlit desktop app for tracking boxing training, weight, running, gym strength, statistics, backups, and achievements.

The app is built with a black/gold boxing theme and is currently made for local PC use.

## Features

* Main dashboard with weekly overview
* Weight tracking with goal progress
* Running log with distance, duration, pace, and comments
* Boxing log with normal training and sparring tracking
* Gym log with workout types, exercises, volume, and effective load
* Statistics page comparing current week with total progress
* Settings page with personal parameters
* Data health check
* Full backup export
* AI review export for weekly coaching feedback
* Safe restore/import system
* Achievement badges with locked/unlocked progress

## Project structure

```text
app.py
pages/
    1_weight.py
    2_running.py
    3_boxing.py
    4_gym.py
    5_statistics.py
    6_settings.py
components/
    achievements.py
    home_button.py
    level_bar.py
    metric_card.py
    page_header.py
    quote_card.py
    status_face.py
    streak_card.py
    weekly_overview.py
utils/
    achievements.py
    calculations.py
    data_loader.py
    export_tools.py
    restore_tools.py
    settings_loader.py
    style_loader.py
assets/
    styles.css
data/
    weight.csv
    runs.csv
    boxing.csv
    gym.csv
    settings.json
    quotes.txt
```

## Installation

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install requirements:

```powershell
pip install -r requirements.txt
```

Run the app:

```powershell
streamlit run app.py
```

## Data

Training data is stored locally in CSV files inside the `data/` folder.

The app currently uses:

```text
data/weight.csv
data/runs.csv
data/boxing.csv
data/gym.csv
data/settings.json
data/quotes.txt
```

## Backup and restore

The Settings page includes:

* Full backup export
* AI review export
* Data health check
* Safe restore/import from backup zip

Before restoring data, the app automatically creates a safety backup.

## Current goal

The main training goal is to improve boxing performance, especially sparring gas tank, while reducing bodyweight toward the target weight.

## Status

This project is under active development.
