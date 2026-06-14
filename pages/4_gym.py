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
    delete_gym_entry,
    load_gym_data,
    save_gym_entry,
    update_gym_entry,
)
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Gym", eyebrow="STRENGTH TRACKING")
home_button()

WORKOUT_TYPES = [
    "Upper body",
    "Lower body",
    "Full body",
    "Boxing strength",
    "Explosive strength",
    "Conditioning",
    "Other",
]

EXERCISES_BY_WORKOUT_TYPE = {
    "Upper body": [
        "Bench press",
        "Incline bench press",
        "Military press",
        "Pull-ups",
        "Dips",
        "Lat pulldown",
        "Cable row",
        "Preacher curl",
        "Skull crushers",
        "Core",
        "Other",
    ],
    "Lower body": [
        "Squat",
        "Deadlift",
        "Romanian deadlift",
        "Leg press",
        "Lunges",
        "Calf raises",
        "Core",
        "Other",
    ],
    "Full body": [
        "Bench press",
        "Squat",
        "Deadlift",
        "Romanian deadlift",
        "Military press",
        "Pull-ups",
        "Dips",
        "Lat pulldown",
        "Cable row",
        "Leg press",
        "Core",
        "Other",
    ],
    "Boxing strength": [
        "Pull-ups",
        "Dips",
        "Military press",
        "Squat",
        "Romanian deadlift",
        "Cable row",
        "Core",
        "Farmer carry",
        "Medicine ball throws",
        "Other",
    ],
    "Explosive strength": [
        "Jump squats",
        "Box jumps",
        "Medicine ball throws",
        "Kettlebell swings",
        "Landmine press",
        "Power cleans",
        "Push press",
        "Other",
    ],
    "Conditioning": [
        "Circuit training",
        "Sled push",
        "Battle ropes",
        "Burpees",
        "Farmer carry",
        "Core",
        "Other",
    ],
    "Other": [
        "Bench press",
        "Incline bench press",
        "Military press",
        "Squat",
        "Deadlift",
        "Romanian deadlift",
        "Pull-ups",
        "Dips",
        "Lat pulldown",
        "Cable row",
        "Leg press",
        "Preacher curl",
        "Skull crushers",
        "Core",
        "Other",
    ],
}

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

if "gym_form_version" not in st.session_state:
    st.session_state.gym_form_version = 0

if "open_gym_manager" not in st.session_state:
    st.session_state.open_gym_manager = False

if st.query_params.get("manage_gym") == "true":
    st.session_state.open_gym_manager = True
    st.query_params.clear()
    st.rerun()

st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)


def show_save_feedback() -> None:
    feedback_message = st.session_state.pop("save_feedback_message", None)

    if not feedback_message:
        return

    st.markdown(
        f"""
<div class="save-feedback-toast">
<span class="save-feedback-icon">✓</span>
<span>{feedback_message}</span>
</div>
""",
        unsafe_allow_html=True,
    )


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
        "load_adjustment_kg",
        "bodyweight_kg",
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
    df["load_adjustment_kg"] = pd.to_numeric(
        df["load_adjustment_kg"],
        errors="coerce",
    ).fillna(0)
    df["bodyweight_kg"] = pd.to_numeric(
        df["bodyweight_kg"],
        errors="coerce",
    ).fillna(0)
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


def format_volume(volume: float) -> str:
    volume = float(volume)

    if volume >= 1000:
        return f"{volume / 1000:.1f} t"

    return f"{volume:.0f} kg"


def format_weight(weight: float) -> str:
    return f"{float(weight):.1f} kg"


def format_load_display(row: pd.Series) -> str:
    weight = float(row["weight_kg"])
    return f"{weight:.1f} kg"


def get_gym_status(weekly_sessions: int) -> tuple[str, str, str]:
    if weekly_sessions >= 2:
        return "happy", "Good", "2+ gym sessions in the last 7 days"

    if weekly_sessions == 1:
        return "medium", "Medium", "1 gym session in the last 7 days"

    return "sad", "Bad", "No gym sessions in the last 7 days"


def format_gym_option(index: int, df: pd.DataFrame) -> str:
    row = df.loc[index]
    date_label = row["date"].strftime("%Y-%m-%d")
    exercise = str(row["exercise"]).strip() or "Exercise"
    sets = int(row["sets"])
    reps = int(row["reps"])
    weight = float(row["weight_kg"])

    return f"{date_label} — {exercise} — {sets}x{reps} @ {weight:.1f} kg"


def make_main_lift_chart(lift_df: pd.DataFrame, selected_lift: str) -> go.Figure:
    chart_df = lift_df.copy()
    chart_df = chart_df.sort_values("date")
    chart_df["date_label"] = chart_df["date"].dt.strftime("%Y-%m-%d")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["date_label"],
            y=chart_df["estimated_1rm"],
            mode="lines+markers",
            name="Estimated 1RM",
            line=dict(
                color="#C9A227",
                width=3,
                shape="spline",
            ),
            marker=dict(
                color="#C9A227",
                size=8,
            ),
            hovertemplate="%{x}<br>%{y:.1f} kg estimated 1RM<extra></extra>",
        )
    )

    fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(
            color="#F5F5F5",
            family="Switzer, sans-serif",
        ),
        xaxis=dict(
            title=None,
            showgrid=False,
        ),
        yaxis=dict(
            title=None,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
        ),
        margin=dict(l=55, r=35, t=35, b=55),
        height=390,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(color="#F5F5F5"),
        ),
        title=dict(
            text=f"{selected_lift} estimated 1RM progress",
            font=dict(size=16, color="rgba(245,245,245,0.86)"),
        ),
    )

    return fig


def make_volume_chart(session_df: pd.DataFrame) -> go.Figure:
    chart_df = session_df.copy()
    chart_df = chart_df.sort_values("date")
    chart_df["date_label"] = chart_df["date"].dt.strftime("%Y-%m-%d")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["date_label"],
            y=chart_df["volume_kg"],
            mode="lines+markers",
            name="Volume",
            line=dict(
                color="#C9A227",
                width=3,
                shape="spline",
            ),
            marker=dict(
                color="#C9A227",
                size=8,
            ),
            hovertemplate="%{x}<br>%{y:.0f} kg lifted<extra></extra>",
        )
    )

    fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(
            color="#F5F5F5",
            family="Switzer, sans-serif",
        ),
        xaxis=dict(
            title=None,
            showgrid=False,
        ),
        yaxis=dict(
            title=None,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
        ),
        margin=dict(l=55, r=35, t=35, b=55),
        height=390,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(color="#F5F5F5"),
        ),
    )

    return fig


def make_top_exercises_chart(exercise_df: pd.DataFrame) -> go.Figure:
    chart_df = exercise_df.copy()
    chart_df = chart_df.sort_values("volume_kg", ascending=True)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=chart_df["volume_kg"],
            y=chart_df["exercise"],
            orientation="h",
            marker=dict(
                color="#C9A227",
                opacity=0.85,
            ),
            hovertemplate="%{y}<br>%{x:.0f} kg total volume<extra></extra>",
        )
    )

    fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(
            color="#F5F5F5",
            family="Switzer, sans-serif",
        ),
        xaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
        ),
        margin=dict(l=120, r=35, t=35, b=55),
        height=360,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(color="#F5F5F5"),
        ),
    )

    return fig


@st.dialog("Manage gym entries", width="large")
def gym_manager_dialog() -> None:
    manage_df = clean_gym_data(load_gym_data()).reset_index(drop=True)

    if manage_df.empty:
        st.warning("No gym entries available.")

        if st.button("Close", use_container_width=True):
            st.session_state.open_gym_manager = False
            st.query_params.clear()
            st.rerun()

        return

    st.markdown(
        """
<div class="form-section-title">MANAGE GYM ENTRIES</div>
<div class="form-section-subtitle">Edit or delete logged strength exercises.</div>
""",
        unsafe_allow_html=True,
    )

    entry_options = list(manage_df.index[::-1])

    selected_index = st.selectbox(
        "Select entry",
        options=entry_options,
        format_func=lambda index: format_gym_option(index, manage_df),
    )

    selected_row = manage_df.loc[selected_index]
    selected_date = selected_row["date"].date()
    selected_workout_type = str(selected_row["workout_type"]).strip() or "Upper body"
    selected_exercise = str(selected_row["exercise"]).strip()
    selected_sets = int(selected_row["sets"])
    selected_reps = int(selected_row["reps"])
    selected_weight = float(selected_row["weight_kg"])
    selected_intensity = int(selected_row["intensity"])
    selected_feeling = int(selected_row["feeling_score"])
    selected_comment = str(selected_row["comment"]).strip()

    if selected_workout_type not in WORKOUT_TYPES:
        selected_workout_type = "Other"

    st.markdown(
        f"""
<div class="selected-entry-card">
<div class="selected-entry-label">SELECTED GYM ENTRY</div>
<div class="selected-entry-value">{selected_date} — {escape(selected_exercise or "Exercise")}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form(f"edit_gym_entry_{selected_index}"):
        edited_date = st.date_input(
            "Date",
            value=selected_date,
        )

        edited_workout_type = st.selectbox(
            "Workout type",
            WORKOUT_TYPES,
            index=WORKOUT_TYPES.index(selected_workout_type),
        )

        edited_exercise = st.text_input(
            "Exercise",
            value=selected_exercise,
        )

        col_sets, col_reps, col_weight = st.columns(3)

        with col_sets:
            edited_sets = st.number_input(
                "Sets",
                min_value=1,
                max_value=20,
                value=max(1, selected_sets),
                step=1,
            )

        with col_reps:
            edited_reps = st.number_input(
                "Reps",
                min_value=1,
                max_value=100,
                value=max(1, selected_reps),
                step=1,
            )

        with col_weight:
            edited_weight = st.number_input(
                "Weight / effective load (kg)",
                min_value=0.0,
                max_value=500.0,
                value=selected_weight,
                step=0.5,
            )

        edited_volume = edited_sets * edited_reps * edited_weight
        edited_estimated_1rm = edited_weight * (1 + edited_reps / 30)

        st.markdown(
            f"""
<div class="running-pace-preview">
<span>Exercise volume</span>
<strong>{format_volume(edited_volume)}</strong>
</div>
<div class="running-pace-preview">
<span>Estimated 1RM</span>
<strong>{format_weight(edited_estimated_1rm)}</strong>
</div>
""",
            unsafe_allow_html=True,
        )

        col_intensity, col_feeling = st.columns(2)

        with col_intensity:
            edited_intensity = st.slider(
                "Intensity",
                min_value=1,
                max_value=10,
                value=max(1, min(selected_intensity, 10)),
            )

        with col_feeling:
            edited_feeling = st.slider(
                "Feeling score",
                min_value=1,
                max_value=10,
                value=max(1, min(selected_feeling, 10)),
            )

        edited_comment = st.text_area(
            "Comment",
            value=selected_comment,
            height=90,
        )

        col_save, col_delete = st.columns(2)

        with col_save:
            save_changes = st.form_submit_button(
                "Save changes",
                use_container_width=True,
            )

        with col_delete:
            delete_entry = st.form_submit_button(
                "Delete entry",
                use_container_width=True,
            )

    if save_changes:
        update_gym_entry(
            row_index=selected_index,
            new_date=edited_date,
            new_workout_type=edited_workout_type,
            new_exercise=edited_exercise,
            new_sets=edited_sets,
            new_reps=edited_reps,
            new_weight_kg=edited_weight,
            new_load_adjustment_kg=0.0,
            new_bodyweight_kg=0.0,
            new_intensity=edited_intensity,
            new_feeling_score=edited_feeling,
            new_comment=edited_comment,
        )

        st.session_state.open_gym_manager = False
        st.session_state.save_feedback_message = "Gym entry updated"
        st.query_params.clear()
        st.rerun()

    if delete_entry:
        delete_gym_entry(selected_index)

        st.session_state.open_gym_manager = False
        st.session_state.save_feedback_message = "Gym entry deleted"
        st.query_params.clear()
        st.rerun()

    if st.button("Close", use_container_width=True):
        st.session_state.open_gym_manager = False
        st.query_params.clear()
        st.rerun()


show_save_feedback()

st.markdown(
    """
<a class="weight-manage-button" href="/gym?manage_gym=true" target="_self" title="Manage gym entries">
✎
</a>
""",
    unsafe_allow_html=True,
)

gym_df = clean_gym_data(load_gym_data())

today = date.today()
week_start = pd.Timestamp(today - timedelta(days=6))
week_end = pd.Timestamp(today)

if gym_df.empty:
    week_df = gym_df.copy()
else:
    week_df = gym_df[
        (gym_df["date"] >= week_start) &
        (gym_df["date"] <= week_end)
    ].copy()

weekly_sessions = week_df["date"].dt.date.nunique() if not week_df.empty else 0
weekly_volume = float(week_df["volume_kg"].sum()) if not week_df.empty else 0.0

total_sessions = gym_df["date"].dt.date.nunique() if not gym_df.empty else 0
total_exercises = len(gym_df)
total_volume = float(gym_df["volume_kg"].sum()) if not gym_df.empty else 0.0
average_feeling = float(gym_df["feeling_score"].mean()) if not gym_df.empty else 0.0

if gym_df.empty:
    latest_volume = 0.0
    latest_workout_type = "No workout"
else:
    latest_date = gym_df["date"].max()
    latest_df = gym_df[gym_df["date"] == latest_date]
    latest_volume = float(latest_df["volume_kg"].sum())
    latest_workout_type = str(latest_df["workout_type"].iloc[-1]).strip() or "Gym"

gym_status_face, gym_status_label, gym_status_detail = get_gym_status(
    weekly_sessions=weekly_sessions,
)

weekly_level_percentage = min((weekly_sessions / 2) * 100, 100)

st.markdown(
    f"""
<div class="weight-status-card">
<div class="weight-status-eyebrow">LAST 7 DAYS</div>

<div class="weight-status-grid">
<div>
<div class="status-label">Gym consistency</div>
<div class="status-value">{status_face_html(gym_status_face)}</div>
<div class="status-muted">{gym_status_label}</div>
</div>

<div>
<div class="status-label">Sessions</div>
<div class="status-value">{weekly_sessions}/2</div>
<div class="status-muted">Weekly strength goal</div>
</div>

<div>
<div class="status-label">Weekly volume</div>
<div class="status-value">{format_volume(weekly_volume)}</div>
<div class="status-muted">Total lifted</div>
</div>

<div>
<div class="status-label">Latest workout</div>
<div class="status-value">{format_volume(latest_volume)}</div>
<div class="status-muted">{escape(latest_workout_type)}</div>
</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="insight-grid">
<div class="insight-card">
<div class="insight-label">Total sessions</div>
<div class="insight-value">{total_sessions}</div>
</div>

<div class="insight-card">
<div class="insight-label">Total exercises</div>
<div class="insight-value">{total_exercises}</div>
</div>

<div class="insight-card">
<div class="insight-label">Total volume</div>
<div class="insight-value">{format_volume(total_volume)}</div>
</div>

<div class="insight-card">
<div class="insight-label">Average feeling</div>
<div class="insight-value">{average_feeling:.1f}/10</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    level_bar_html(
        eyebrow="GYM LEVEL",
        title="Weekly strength level",
        percentage=weekly_level_percentage,
        label=f"{weekly_sessions}/2 gym sessions completed",
        detail="Based on gym sessions logged in the last 7 days.",
    ),
    unsafe_allow_html=True,
)

if not gym_df.empty:
    main_lift_df = gym_df[gym_df["exercise"].isin(MAIN_LIFTS)].copy()

    if not main_lift_df.empty:
        available_lifts = [
            lift for lift in MAIN_LIFTS
            if lift in main_lift_df["exercise"].unique()
        ]

        st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

        st.markdown(
            """
<div class="chart-header">
<div class="chart-eyebrow">MAIN LIFT PROGRESS</div>
<div class="chart-summary">Estimated 1RM over time</div>
<div class="chart-detail">Uses estimated 1RM: weight × (1 + reps / 30). For pull-ups, enter the effective load you actually moved.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        selected_lift = st.selectbox(
            "Select main lift",
            available_lifts,
            key="gym_main_lift_selector",
        )

        selected_lift_df = main_lift_df[
            main_lift_df["exercise"] == selected_lift
        ].copy()

        selected_lift_df = (
            selected_lift_df.groupby("date", as_index=False)
            .agg(
                estimated_1rm=("estimated_1rm", "max"),
                volume_kg=("volume_kg", "sum"),
            )
            .sort_values("date")
        )

        st.plotly_chart(
            make_main_lift_chart(selected_lift_df, selected_lift),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    session_volume_df = (
        gym_df.groupby("date", as_index=False)
        .agg(
            volume_kg=("volume_kg", "sum"),
            exercises=("exercise", "count"),
            feeling_score=("feeling_score", "mean"),
        )
        .sort_values("date")
    )

    st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

    st.markdown(
        """
<div class="chart-header">
<div class="chart-eyebrow">STRENGTH VOLUME</div>
<div class="chart-summary">Total kg lifted per workout</div>
<div class="chart-detail">This combines sets × reps × effective weight for every exercise logged that day.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        make_volume_chart(session_volume_df),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    top_exercises_df = (
        gym_df.groupby("exercise", as_index=False)
        .agg(volume_kg=("volume_kg", "sum"))
        .sort_values("volume_kg", ascending=False)
        .head(6)
    )

    if not top_exercises_df.empty:
        st.markdown(
            """
<div class="chart-header">
<div class="chart-eyebrow">TOP EXERCISES</div>
<div class="chart-summary">Highest total lifted volume</div>
<div class="chart-detail">Useful for seeing where most gym work is going.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.plotly_chart(
            make_top_exercises_chart(top_exercises_df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
else:
    st.info("No gym exercises logged yet. Add your first exercise below.")

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        """
<div class="form-section-title">LOG STRENGTH EXERCISE</div>
<div class="form-section-subtitle">Choose workout type first. Exercise options update immediately.</div>
""",
        unsafe_allow_html=True,
    )

    form_version = st.session_state.gym_form_version

    workout_type = st.selectbox(
        "Workout type",
        WORKOUT_TYPES,
        key=f"gym_workout_type_{form_version}",
    )

    exercise_options = EXERCISES_BY_WORKOUT_TYPE.get(
        workout_type,
        EXERCISES_BY_WORKOUT_TYPE["Other"],
    )

    with st.form(f"gym_entry_form_{form_version}"):
        workout_date = st.date_input(
            "Date",
            value=today,
            key=f"gym_date_{form_version}",
        )

        exercise_choice = st.selectbox(
            "Exercise",
            exercise_options,
            key=f"gym_exercise_choice_{form_version}_{workout_type}",
        )

        if exercise_choice == "Other":
            exercise = st.text_input(
                "Custom exercise",
                placeholder="Example: Landmine press",
                key=f"gym_custom_exercise_{form_version}_{workout_type}",
            )
        else:
            exercise = exercise_choice

        col_sets, col_reps, col_weight = st.columns(3)

        with col_sets:
            sets = st.number_input(
                "Sets",
                min_value=1,
                max_value=20,
                value=3,
                step=1,
                key=f"gym_sets_{form_version}",
            )

        with col_reps:
            reps = st.number_input(
                "Reps",
                min_value=1,
                max_value=100,
                value=8,
                step=1,
                key=f"gym_reps_{form_version}",
            )

        with col_weight:
            weight_kg = st.number_input(
                "Weight / effective load (kg)",
                min_value=0.0,
                max_value=500.0,
                value=60.0,
                step=0.5,
                help=(
                    "For assisted pull-ups: enter effective load. "
                    "Example: 80 kg bodyweight with 10 kg assistance = 70 kg."
                ),
                key=f"gym_weight_{form_version}",
            )

        effective_weight = weight_kg
        exercise_volume = sets * reps * effective_weight
        estimated_1rm = effective_weight * (1 + reps / 30)

        st.markdown(
            f"""
<div class="running-pace-preview">
<span>Effective load</span>
<strong>{format_weight(effective_weight)}</strong>
</div>
<div class="running-pace-preview">
<span>Exercise volume</span>
<strong>{format_volume(exercise_volume)}</strong>
</div>
<div class="running-pace-preview">
<span>Estimated 1RM</span>
<strong>{format_weight(estimated_1rm)}</strong>
</div>
""",
            unsafe_allow_html=True,
        )

        col_intensity, col_feeling = st.columns(2)

        with col_intensity:
            intensity = st.slider(
                "Intensity",
                min_value=1,
                max_value=10,
                value=7,
                key=f"gym_intensity_{form_version}",
            )

        with col_feeling:
            feeling_score = st.slider(
                "Feeling score",
                min_value=1,
                max_value=10,
                value=7,
                key=f"gym_feeling_{form_version}",
            )

        comment = st.text_area(
            "Comment",
            placeholder="Example: Felt strong. Bench moved fast but shoulders felt tight.",
            height=90,
            key=f"gym_comment_{form_version}",
        )

        submitted = st.form_submit_button(
            "Save gym exercise",
            use_container_width=True,
        )

    if submitted:
        if not str(exercise).strip():
            st.warning("Enter an exercise before saving.")
        else:
            save_gym_entry(
                workout_date=workout_date,
                workout_type=workout_type,
                exercise=exercise,
                sets=sets,
                reps=reps,
                weight_kg=effective_weight,
                load_adjustment_kg=0.0,
                bodyweight_kg=0.0,
                intensity=intensity,
                feeling_score=feeling_score,
                comment=comment,
            )

            st.session_state.gym_form_version += 1
            st.session_state.save_feedback_message = "Gym exercise saved"
            st.rerun()

if not gym_df.empty:
    history_data = gym_df.copy()
    history_data["date_label"] = history_data["date"].dt.strftime("%Y-%m-%d")
    history_data = history_data.sort_values("date", ascending=False).head(12)

    history_rows = """
<div class="run-history-row run-history-head">
<div>Date</div>
<div>Exercise</div>
<div>Sets x reps</div>
<div>Load</div>
<div>Volume</div>
</div>
"""

    for _, row in history_data.iterrows():
        date_label = escape(str(row["date_label"]))
        exercise_text = escape(str(row["exercise"]).strip() or "Exercise")
        sets_reps_text = f'{int(row["sets"])} x {int(row["reps"])}'
        load_text = escape(format_load_display(row))
        volume_text = format_volume(float(row["volume_kg"]))

        history_rows += f"""
<div class="run-history-row">
<div class="run-history-value">{date_label}</div>
<div class="run-history-value">{exercise_text}</div>
<div class="run-history-value">{sets_reps_text}</div>
<div class="run-history-value">{load_text}</div>
<div class="run-history-comment">{volume_text}</div>
</div>
"""

    st.markdown(
        f"""
<div class="history-card">
<div class="history-header">
<div>
<div class="history-eyebrow">RECENT GYM</div>
<div class="history-title">Exercise history</div>
</div>
</div>

<div class="history-list">
{history_rows}
</div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("Raw CSV table"):
        raw_df = gym_df.copy()
        raw_df["date"] = raw_df["date"].dt.strftime("%Y-%m-%d")
        raw_df = raw_df.sort_values("date", ascending=False)

        st.dataframe(
            raw_df[
                [
                    "date",
                    "workout_type",
                    "exercise",
                    "sets",
                    "reps",
                    "weight_kg",
                    "load_adjustment_kg",
                    "bodyweight_kg",
                    "volume_kg",
                    "estimated_1rm",
                    "intensity",
                    "feeling_score",
                    "comment",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

if st.session_state.open_gym_manager:
    gym_manager_dialog()

st.markdown("</div>", unsafe_allow_html=True)