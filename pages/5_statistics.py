from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.home_button import home_button
from components.level_bar import level_bar_html
from components.page_header import page_header
from components.status_face import status_face_html
from utils.data_loader import (
    load_boxing_data,
    load_gym_data,
    load_runs_data,
    load_weight_data,
)
from utils.settings_loader import load_settings
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Statistics", eyebrow="PROGRESS DASHBOARD")
home_button()

st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)

settings = load_settings()
GOAL_WEIGHT_KG = float(settings.get("goal_weight", 75.0))

MAIN_LIFTS = [
    "Bench press",
    "Squat",
    "Deadlift",
    "Romanian deadlift",
    "Military press",
    "Pull-ups",
    "Dips",
    "Lat pulldown",
    "Cable row",
]


# -------------------------
# CLEANING
# -------------------------

def clean_weight_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "date" not in df.columns:
        df["date"] = ""

    if "weight_kg" not in df.columns and "weight" in df.columns:
        df = df.rename(columns={"weight": "weight_kg"})

    if "weight_kg" not in df.columns:
        df["weight_kg"] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")

    df = df.dropna(subset=["date", "weight_kg"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def clean_runs_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    required_columns = ["date", "distance_km", "duration_min", "comment"]

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date", "distance_km", "duration_min"])
    df = df.sort_values("date").reset_index(drop=True)

    df["pace_min_per_km"] = df.apply(
        lambda row: row["duration_min"] / row["distance_km"]
        if row["distance_km"] > 0
        else 0,
        axis=1,
    )

    return df


def clean_boxing_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    required_columns = [
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

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["session_type"] = df["session_type"].fillna("")
    df["activities"] = df["activities"].fillna("")
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(0)
    df["rounds"] = pd.to_numeric(df["rounds"], errors="coerce").fillna(0)
    df["round_length_min"] = pd.to_numeric(
        df["round_length_min"],
        errors="coerce",
    ).fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(
        df["feeling_score"],
        errors="coerce",
    ).fillna(0)
    df["focus"] = df["focus"].fillna("")
    df["sparring"] = df["sparring"].fillna("No")
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["is_sparring"] = (
        df["sparring"].astype(str).str.lower().eq("yes")
        | df["session_type"].astype(str).str.lower().str.contains("sparring")
        | df["activities"].astype(str).str.lower().str.contains("sparring")
        | (df["rounds"] > 0)
    )

    df["sparring_minutes"] = df["rounds"] * df["round_length_min"]

    return df


def clean_gym_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    required_columns = [
        "date",
        "workout_type",
        "exercise",
        "sets",
        "reps",
        "weight_kg",
        "intensity",
        "feeling_score",
        "comment",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["workout_type"] = df["workout_type"].fillna("")
    df["exercise"] = df["exercise"].fillna("")
    df["sets"] = pd.to_numeric(df["sets"], errors="coerce").fillna(0)
    df["reps"] = pd.to_numeric(df["reps"], errors="coerce").fillna(0)
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce").fillna(0)
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce").fillna(0)
    df["feeling_score"] = pd.to_numeric(
        df["feeling_score"],
        errors="coerce",
    ).fillna(0)
    df["comment"] = df["comment"].fillna("")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["volume_kg"] = df["sets"] * df["reps"] * df["weight_kg"]
    df["estimated_1rm"] = df["weight_kg"] * (1 + (df["reps"] / 30))

    return df


# -------------------------
# FORMATTERS
# -------------------------

def safe_mean(values: pd.Series) -> float:
    if values.empty:
        return 0.0

    values = pd.to_numeric(values, errors="coerce").dropna()
    values = values[values > 0]

    if values.empty:
        return 0.0

    return float(values.mean())


def format_volume(volume: float) -> str:
    volume = float(volume)

    if volume >= 1000:
        return f"{volume / 1000:.1f} t"

    return f"{volume:.0f} kg"


def format_weight(weight: float) -> str:
    return f"{float(weight):.1f} kg"


def format_distance(distance: float) -> str:
    return f"{float(distance):.1f} km"


def format_minutes(minutes: float) -> str:
    return f"{float(minutes):.0f} min"


def format_pace(pace: float) -> str:
    pace = float(pace)

    if pace <= 0:
        return "-"

    minutes = int(pace)
    seconds = int(round((pace - minutes) * 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}/km"


def insight_card(label: str, value: str, sublabel: str = "") -> str:
    sublabel_html = ""

    if sublabel:
        sublabel_html = f'<div class="status-muted">{escape(sublabel)}</div>'

    return f"""
<div class="insight-card">
<div class="insight-label">{escape(label)}</div>
<div class="insight-value">{escape(value)}</div>
{sublabel_html}
</div>
"""


# -------------------------
# DATE HELPERS
# -------------------------

def filter_last_7_days(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df.copy()

    today = pd.Timestamp(date.today())
    week_start = pd.Timestamp(date.today() - timedelta(days=6))

    return df[
        (df["date"] >= week_start)
        & (df["date"] <= today)
    ].copy()


def get_unique_training_days(
    boxing_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    gym_df: pd.DataFrame,
) -> int:
    training_days = set()

    if not boxing_df.empty:
        training_days.update(boxing_df["date"].dt.date.tolist())

    if not runs_df.empty:
        training_days.update(runs_df["date"].dt.date.tolist())

    if not gym_df.empty:
        training_days.update(gym_df["date"].dt.date.tolist())

    return len(training_days)


def get_week_start(series: pd.Series) -> pd.Series:
    return series.dt.normalize() - pd.to_timedelta(series.dt.weekday, unit="D")


# -------------------------
# SCORE LOGIC
# -------------------------

def calculate_weight_score(weight_df: pd.DataFrame) -> float:
    if weight_df.empty:
        return 0.0

    latest_weight = float(weight_df.iloc[-1]["weight_kg"])
    start_weight = float(weight_df.iloc[0]["weight_kg"])

    if latest_weight <= GOAL_WEIGHT_KG:
        return 10.0

    if start_weight <= GOAL_WEIGHT_KG:
        return 5.0

    total_needed = start_weight - GOAL_WEIGHT_KG
    progress = start_weight - latest_weight

    if total_needed <= 0:
        return 5.0

    return max(0.0, min((progress / total_needed) * 10, 10.0))


def calculate_boxer_score(
    training_days: int,
    weekly_boxing_sessions: int,
    weekly_sparring_rounds: int,
    weekly_runs: int,
    weekly_gym_sessions: int,
    weight_score: float,
    weekly_average_feeling: float,
) -> int:
    consistency_part = min(training_days / 5, 1) * 30
    boxing_part = min(weekly_boxing_sessions / 3, 1) * 15
    sparring_part = 10 if weekly_sparring_rounds > 0 else 0
    running_part = min(weekly_runs / 2, 1) * 15
    gym_part = min(weekly_gym_sessions / 2, 1) * 15
    feeling_part = min(max(weekly_average_feeling, 0), 10) / 10 * 5

    total_score = (
        consistency_part
        + boxing_part
        + sparring_part
        + running_part
        + gym_part
        + weight_score
        + feeling_part
    )

    return int(round(max(0, min(total_score, 100))))


def get_score_status(score: int) -> tuple[str, str, str]:
    if score >= 75:
        return "happy", "Strong week", "Training balance is good."

    if score >= 50:
        return "medium", "Decent week", "Good base, but one area needs work."

    return "sad", "Weak week", "Not enough total training logged yet."


def build_ai_style_comment(
    score: int,
    weekly_boxing_sessions: int,
    weekly_sparring_rounds: int,
    weekly_runs: int,
    weekly_gym_sessions: int,
    training_days: int,
) -> str:
    if score >= 75:
        return (
            "Strong week. Keep the structure: boxing first, sparring as the main test, "
            "running for gas tank, and gym for strength without overloading recovery."
        )

    missing = []

    if weekly_boxing_sessions < 3:
        missing.append("boxing sessions")

    if weekly_sparring_rounds <= 0:
        missing.append("sparring rounds")

    if weekly_runs < 2:
        missing.append("running")

    if weekly_gym_sessions < 2:
        missing.append("gym work")

    if training_days < 4:
        missing.append("overall consistency")

    if not missing:
        return "Decent week. The structure is there, but the score is held back by low feeling or low volume."

    return "Main limiter this week: " + ", ".join(missing[:3]) + "."


# -------------------------
# CHARTS
# -------------------------

def build_weekly_training_summary(
    boxing_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    gym_df: pd.DataFrame,
) -> pd.DataFrame:
    today_ts = pd.Timestamp(date.today())
    current_week_start = today_ts.normalize() - pd.Timedelta(days=today_ts.weekday())

    week_starts = [
        current_week_start - pd.Timedelta(weeks=i)
        for i in range(7, -1, -1)
    ]

    summary_df = pd.DataFrame({"week_start": week_starts})
    summary_df["week_label"] = summary_df["week_start"].dt.strftime("%d %b")
    summary_df["boxing"] = 0
    summary_df["running"] = 0
    summary_df["gym"] = 0

    if not boxing_df.empty:
        temp = boxing_df.copy()
        temp["week_start"] = get_week_start(temp["date"])
        counts = temp.groupby("week_start").size()
        summary_df["boxing"] = summary_df["week_start"].map(counts).fillna(0).astype(int)

    if not runs_df.empty:
        temp = runs_df.copy()
        temp["week_start"] = get_week_start(temp["date"])
        counts = temp.groupby("week_start").size()
        summary_df["running"] = summary_df["week_start"].map(counts).fillna(0).astype(int)

    if not gym_df.empty:
        temp = gym_df.copy()
        temp["week_start"] = get_week_start(temp["date"])
        counts = temp.groupby("week_start")["date"].apply(
            lambda values: values.dt.date.nunique()
        )
        summary_df["gym"] = summary_df["week_start"].map(counts).fillna(0).astype(int)

    return summary_df


def make_weekly_training_chart(summary_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=summary_df["week_label"],
            y=summary_df["boxing"],
            name="Boxing",
            marker=dict(color="#C9A227"),
            hovertemplate="%{x}<br>Boxing: %{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=summary_df["week_label"],
            y=summary_df["running"],
            name="Running",
            marker=dict(color="rgba(245,245,245,0.72)"),
            hovertemplate="%{x}<br>Running: %{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=summary_df["week_label"],
            y=summary_df["gym"],
            name="Gym",
            marker=dict(color="rgba(201,162,39,0.45)"),
            hovertemplate="%{x}<br>Gym: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        barmode="group",
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(color="#F5F5F5", family="Switzer, sans-serif"),
        xaxis=dict(title=None, showgrid=False, type="category"),
        yaxis=dict(
            title=None,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
            dtick=1,
        ),
        margin=dict(l=45, r=35, t=35, b=55),
        height=390,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(color="#F5F5F5"),
        ),
    )

    return fig


def make_sparring_chart(boxing_df: pd.DataFrame) -> go.Figure:
    sparring_df = boxing_df[boxing_df["is_sparring"]].copy()

    sparring_df = (
        sparring_df.groupby("date", as_index=False)
        .agg(
            rounds=("rounds", "sum"),
            sparring_minutes=("sparring_minutes", "sum"),
            feeling_score=("feeling_score", "mean"),
        )
        .sort_values("date")
    )

    sparring_df["date_label"] = sparring_df["date"].dt.strftime("%d %b")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sparring_df["date_label"],
            y=sparring_df["rounds"],
            mode="lines+markers",
            name="Sparring rounds",
            line=dict(color="#C9A227", width=3, shape="spline"),
            marker=dict(color="#C9A227", size=8),
            hovertemplate="%{x}<br>%{y:.0f} rounds<extra></extra>",
        )
    )

    fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(color="#F5F5F5", family="Switzer, sans-serif"),
        xaxis=dict(title=None, showgrid=False, type="category"),
        yaxis=dict(
            title=None,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
            dtick=1,
        ),
        margin=dict(l=45, r=35, t=35, b=55),
        height=390,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(color="#F5F5F5"),
        ),
    )

    return fig


def make_weight_chart(weight_df: pd.DataFrame) -> go.Figure:
    chart_df = weight_df.copy()
    chart_df["date_label"] = chart_df["date"].dt.strftime("%d %b")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["date_label"],
            y=chart_df["weight_kg"],
            mode="lines+markers",
            name="Weight",
            line=dict(color="#C9A227", width=3, shape="spline"),
            marker=dict(color="#C9A227", size=8),
            hovertemplate="%{x}<br>%{y:.1f} kg<extra></extra>",
        )
    )

    fig.add_hline(
        y=GOAL_WEIGHT_KG,
        line_dash="dash",
        line_color="rgba(255,80,80,0.75)",
        annotation_text=f"{GOAL_WEIGHT_KG:.0f} kg goal",
        annotation_position="bottom right",
    )

    fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(color="#F5F5F5", family="Switzer, sans-serif"),
        xaxis=dict(title=None, showgrid=False, type="category"),
        yaxis=dict(
            title=None,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
        ),
        margin=dict(l=45, r=35, t=35, b=55),
        height=390,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(color="#F5F5F5"),
        ),
    )

    return fig


# -------------------------
# LOAD DATA
# -------------------------

weight_df = clean_weight_data(load_weight_data())
runs_df = clean_runs_data(load_runs_data())
boxing_df = clean_boxing_data(load_boxing_data())
gym_df = clean_gym_data(load_gym_data())

boxing_week_df = filter_last_7_days(boxing_df)
runs_week_df = filter_last_7_days(runs_df)
gym_week_df = filter_last_7_days(gym_df)


# -------------------------
# THIS WEEK METRICS
# -------------------------

weekly_boxing_sessions = len(boxing_week_df)
weekly_sparring_df = (
    boxing_week_df[boxing_week_df["is_sparring"]]
    if not boxing_week_df.empty
    else boxing_week_df
)
weekly_sparring_rounds = int(weekly_sparring_df["rounds"].sum()) if not weekly_sparring_df.empty else 0
weekly_sparring_minutes = float(weekly_sparring_df["sparring_minutes"].sum()) if not weekly_sparring_df.empty else 0.0

weekly_runs = len(runs_week_df)
weekly_running_distance = float(runs_week_df["distance_km"].sum()) if not runs_week_df.empty else 0.0
weekly_average_pace = safe_mean(runs_week_df["pace_min_per_km"]) if not runs_week_df.empty else 0.0

weekly_gym_sessions = gym_week_df["date"].dt.date.nunique() if not gym_week_df.empty else 0
weekly_gym_volume = float(gym_week_df["volume_kg"].sum()) if not gym_week_df.empty else 0.0

weekly_training_days = get_unique_training_days(
    boxing_df=boxing_week_df,
    runs_df=runs_week_df,
    gym_df=gym_week_df,
)

weekly_average_feeling_values = []

if not boxing_week_df.empty:
    weekly_average_feeling_values.extend(
        boxing_week_df[boxing_week_df["feeling_score"] > 0]["feeling_score"].tolist()
    )

if not gym_week_df.empty:
    weekly_average_feeling_values.extend(
        gym_week_df[gym_week_df["feeling_score"] > 0]["feeling_score"].tolist()
    )

weekly_average_feeling = (
    float(sum(weekly_average_feeling_values) / len(weekly_average_feeling_values))
    if weekly_average_feeling_values
    else 0.0
)


# -------------------------
# FROM START METRICS
# -------------------------

total_boxing_sessions = len(boxing_df)
total_sparring_df = boxing_df[boxing_df["is_sparring"]] if not boxing_df.empty else boxing_df
total_sparring_rounds = int(total_sparring_df["rounds"].sum()) if not total_sparring_df.empty else 0
total_sparring_minutes = float(total_sparring_df["sparring_minutes"].sum()) if not total_sparring_df.empty else 0.0
total_boxing_time = float(boxing_df["duration_min"].sum()) if not boxing_df.empty else 0.0
total_boxing_feeling = safe_mean(boxing_df["feeling_score"]) if not boxing_df.empty else 0.0

total_runs = len(runs_df)
total_running_distance = float(runs_df["distance_km"].sum()) if not runs_df.empty else 0.0
total_running_minutes = float(runs_df["duration_min"].sum()) if not runs_df.empty else 0.0
total_average_pace = safe_mean(runs_df["pace_min_per_km"]) if not runs_df.empty else 0.0

total_gym_sessions = gym_df["date"].dt.date.nunique() if not gym_df.empty else 0
total_gym_volume = float(gym_df["volume_kg"].sum()) if not gym_df.empty else 0.0
total_gym_feeling = safe_mean(gym_df["feeling_score"]) if not gym_df.empty else 0.0

total_training_days = get_unique_training_days(
    boxing_df=boxing_df,
    runs_df=runs_df,
    gym_df=gym_df,
)

weight_score = calculate_weight_score(weight_df)

boxer_score = calculate_boxer_score(
    training_days=weekly_training_days,
    weekly_boxing_sessions=weekly_boxing_sessions,
    weekly_sparring_rounds=weekly_sparring_rounds,
    weekly_runs=weekly_runs,
    weekly_gym_sessions=weekly_gym_sessions,
    weight_score=weight_score,
    weekly_average_feeling=weekly_average_feeling,
)

score_face, score_label, score_detail = get_score_status(boxer_score)

comment_text = build_ai_style_comment(
    score=boxer_score,
    weekly_boxing_sessions=weekly_boxing_sessions,
    weekly_sparring_rounds=weekly_sparring_rounds,
    weekly_runs=weekly_runs,
    weekly_gym_sessions=weekly_gym_sessions,
    training_days=weekly_training_days,
)


# -------------------------
# TOP STATUS
# -------------------------

st.markdown(
    f"""
<div class="weight-status-card">
<div class="weight-status-eyebrow">THIS WEEK</div>

<div class="weight-status-grid">
<div>
<div class="status-label">Boxer score</div>
<div class="status-value">{boxer_score}/100</div>
<div class="status-muted">{escape(score_label)}</div>
</div>

<div>
<div class="status-label">Status</div>
<div class="status-value">{status_face_html(score_face)}</div>
<div class="status-muted">{escape(score_detail)}</div>
</div>

<div>
<div class="status-label">Training days</div>
<div class="status-value">{weekly_training_days}</div>
<div class="status-muted">{total_training_days} from start</div>
</div>

<div>
<div class="status-label">Sparring</div>
<div class="status-value">{weekly_sparring_rounds}</div>
<div class="status-muted">{total_sparring_rounds} rounds from start</div>
</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    level_bar_html(
        eyebrow="THIS WEEK",
        title="Weekly boxer score",
        percentage=boxer_score,
        label=f"{boxer_score}/100",
        detail=comment_text,
    ),
    unsafe_allow_html=True,
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# -------------------------
# THIS WEEK VS FROM START
# -------------------------

st.markdown(
    """
<div class="chart-header">
<div class="chart-eyebrow">THIS WEEK VS FROM START</div>
<div class="chart-summary">Current training compared with total progress</div>
<div class="chart-detail">Every card shows short-term work first, then total progress from the first log.</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="insight-grid">
{insight_card("Boxing sessions", str(weekly_boxing_sessions), f"{total_boxing_sessions} from start")}
{insight_card("Sparring rounds", str(weekly_sparring_rounds), f"{total_sparring_rounds} from start")}
{insight_card("Running distance", format_distance(weekly_running_distance), f"{format_distance(total_running_distance)} from start")}
{insight_card("Gym volume", format_volume(weekly_gym_volume), f"{format_volume(total_gym_volume)} from start")}
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------
# BOXING PRIORITY
# -------------------------

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

st.markdown(
    """
<div class="chart-header">
<div class="chart-eyebrow">BOXING PRIORITY</div>
<div class="chart-summary">Sparring and boxing workload</div>
<div class="chart-detail">Sparring rounds are treated as the most important boxing progress metric.</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="insight-grid">
{insight_card("Sparring rounds", str(weekly_sparring_rounds), f"{total_sparring_rounds} from start")}
{insight_card("Sparring minutes", format_minutes(weekly_sparring_minutes), f"{format_minutes(total_sparring_minutes)} from start")}
{insight_card("Boxing time", format_minutes(float(boxing_week_df["duration_min"].sum()) if not boxing_week_df.empty else 0), f"{format_minutes(total_boxing_time)} from start")}
{insight_card("Boxing feeling", f"{safe_mean(boxing_week_df['feeling_score']) if not boxing_week_df.empty else 0:.1f}/10", f"{total_boxing_feeling:.1f}/10 from start")}
</div>
""",
    unsafe_allow_html=True,
)

if not boxing_df.empty and boxing_df["is_sparring"].any():
    st.plotly_chart(
        make_sparring_chart(boxing_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )
else:
    st.info("No sparring data yet. After Saturday sparring, this graph becomes important.")


# -------------------------
# TRAINING BALANCE
# -------------------------

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

weekly_summary_df = build_weekly_training_summary(
    boxing_df=boxing_df,
    runs_df=runs_df,
    gym_df=gym_df,
)

st.markdown(
    """
<div class="chart-header">
<div class="chart-eyebrow">TRAINING BALANCE</div>
<div class="chart-summary">Boxing, running, and gym sessions by week</div>
<div class="chart-detail">Useful for checking if training is balanced enough for boxing progress.</div>
</div>
""",
    unsafe_allow_html=True,
)

st.plotly_chart(
    make_weekly_training_chart(weekly_summary_df),
    use_container_width=True,
    config={"displayModeBar": False},
)


# -------------------------
# BODY PROGRESS
# -------------------------

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

if not weight_df.empty:
    latest_weight = float(weight_df.iloc[-1]["weight_kg"])
    start_weight = float(weight_df.iloc[0]["weight_kg"])
    weight_change_from_start = latest_weight - start_weight
    distance_to_goal = latest_weight - GOAL_WEIGHT_KG

    st.markdown(
        f"""
<div class="chart-header">
<div class="chart-eyebrow">BODY PROGRESS</div>
<div class="chart-summary">Weight trend from start toward {GOAL_WEIGHT_KG:.0f} kg</div>
<div class="chart-detail">Current distance to goal: {distance_to_goal:.1f} kg.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="insight-grid">
{insight_card("Start weight", format_weight(start_weight))}
{insight_card("Current weight", format_weight(latest_weight))}
{insight_card("Change from start", f"{weight_change_from_start:+.1f} kg")}
{insight_card("Goal weight", format_weight(GOAL_WEIGHT_KG), f"{distance_to_goal:.1f} kg away")}
</div>
""",
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        make_weight_chart(weight_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )
else:
    st.info("No weight data yet.")


# -------------------------
# RUNNING
# -------------------------

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="chart-header">
<div class="chart-eyebrow">GAS TANK</div>
<div class="chart-summary">Running progress from start</div>
<div class="chart-detail">Running supports boxing endurance and recovery between rounds.</div>
</div>

<div class="insight-grid">
{insight_card("Runs", str(weekly_runs), f"{total_runs} from start")}
{insight_card("Distance", format_distance(weekly_running_distance), f"{format_distance(total_running_distance)} from start")}
{insight_card("Average pace", format_pace(weekly_average_pace), f"{format_pace(total_average_pace)} from start")}
{insight_card("Running time", format_minutes(float(runs_week_df["duration_min"].sum()) if not runs_week_df.empty else 0), f"{format_minutes(total_running_minutes)} from start")}
</div>
""",
    unsafe_allow_html=True,
)


# -------------------------
# STRENGTH
# -------------------------

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="chart-header">
<div class="chart-eyebrow">STRENGTH</div>
<div class="chart-summary">Gym strength and volume from start</div>
<div class="chart-detail">Strength should support boxing without taking too much recovery.</div>
</div>

<div class="insight-grid">
{insight_card("Gym sessions", str(weekly_gym_sessions), f"{total_gym_sessions} from start")}
{insight_card("Gym volume", format_volume(weekly_gym_volume), f"{format_volume(total_gym_volume)} from start")}
{insight_card("Gym feeling", f"{safe_mean(gym_week_df['feeling_score']) if not gym_week_df.empty else 0:.1f}/10", f"{total_gym_feeling:.1f}/10 from start")}
{insight_card("Total training days", str(weekly_training_days), f"{total_training_days} from start")}
</div>
""",
    unsafe_allow_html=True,
)

if not gym_df.empty:
    lift_df = gym_df[gym_df["exercise"].isin(MAIN_LIFTS)].copy()

    if not lift_df.empty:
        best_lifts_df = (
            lift_df.groupby("exercise", as_index=False)
            .agg(best_estimated_1rm=("estimated_1rm", "max"))
            .sort_values("best_estimated_1rm", ascending=False)
        )

        best_lifts_df["best_estimated_1rm"] = best_lifts_df["best_estimated_1rm"].map(
            lambda value: f"{value:.1f} kg"
        )

        st.dataframe(
            best_lifts_df.rename(
                columns={
                    "exercise": "Exercise",
                    "best_estimated_1rm": "Best estimated 1RM from start",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No main lift data yet.")
else:
    st.info("No gym data yet.")

st.markdown("</div>", unsafe_allow_html=True)