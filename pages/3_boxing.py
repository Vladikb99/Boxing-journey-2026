from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.home_button import home_button
from components.page_header import page_header
from utils.data_loader import (
    delete_boxing_entry,
    load_boxing_data,
    save_boxing_session,
    update_boxing_entry,
)
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Boxing", eyebrow="FIGHT TRAINING LOG")
home_button()

SESSION_TYPES = [
    "Boxing training",
    "Sparring",
    "Solo training",
    "Strength & conditioning",
    "Other",
]

ACTIVITY_OPTIONS = [
    "Pad work",
    "Bag work",
    "Sparring",
    "Technique",
    "Footwork",
    "Defense",
    "Speed",
    "Strength",
    "Conditioning",
    "Combinations",
    "Shadowboxing",
]

NORMAL_SESSION_MINUTES = 90.0

if "open_boxing_manager" not in st.session_state:
    st.session_state.open_boxing_manager = False

if "boxing_form_version" not in st.session_state:
    st.session_state.boxing_form_version = 0

if st.query_params.get("manage_boxing") == "true":
    st.session_state.open_boxing_manager = True
    st.query_params.clear()
    st.rerun()

st.markdown(
    """
<style>
.consistency-face-wrap {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    height: 64px;
}

.consistency-face {
    width: 58px;
    height: 58px;
    border: 1.5px solid rgba(201, 162, 39, 0.78);
    border-radius: 999px;
    position: relative;
    background:
        radial-gradient(circle at 35% 28%, rgba(255, 221, 95, 0.14), transparent 30%),
        linear-gradient(145deg, rgba(201, 162, 39, 0.09), rgba(255, 255, 255, 0.02));
    box-shadow:
        0 0 20px rgba(201, 162, 39, 0.10),
        inset 0 0 16px rgba(201, 162, 39, 0.06);
}

.face-eye {
    position: absolute;
    top: 18px;
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: #C9A227;
    box-shadow: 0 0 8px rgba(201, 162, 39, 0.45);
}

.face-eye-left {
    left: 17px;
}

.face-eye-right {
    right: 17px;
}

.face-mouth {
    position: absolute;
    left: 16px;
    width: 26px;
}

.consistency-face-happy .face-mouth {
    top: 32px;
    height: 13px;
    border-bottom: 2px solid #C9A227;
    border-radius: 0 0 24px 24px;
}

.consistency-face-medium .face-mouth {
    top: 39px;
    height: 0;
    border-bottom: 2px solid #C9A227;
    border-radius: 999px;
}

.consistency-face-sad .face-mouth {
    top: 35px;
    height: 13px;
    border-top: 2px solid #C9A227;
    border-radius: 24px 24px 0 0;
}

.boxing-tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
}

.boxing-tag {
    border: 1px solid rgba(201, 162, 39, 0.25);
    background: rgba(201, 162, 39, 0.06);
    color: rgba(245, 245, 245, 0.82);
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 12px;
    letter-spacing: 0.2px;
}

.boxing-note-card {
    border: 1px solid rgba(255, 255, 255, 0.09);
    background: rgba(255, 255, 255, 0.035);
    border-radius: 16px;
    padding: 16px 18px;
    margin-top: 12px;
}

.boxing-note-label {
    color: rgba(201, 162, 39, 0.9);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 6px;
}

.boxing-note-text {
    color: rgba(245, 245, 245, 0.82);
    font-size: 14px;
    line-height: 1.45;
}
</style>
""",
    unsafe_allow_html=True,
)

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
    df["duration_min"] = pd.to_numeric(
        df["duration_min"],
        errors="coerce",
    ).fillna(NORMAL_SESSION_MINUTES)
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

    return df


def split_activities(value: str) -> list[str]:
    raw_value = str(value).strip()

    if not raw_value:
        return []

    return [item.strip() for item in raw_value.split(" | ") if item.strip()]


def join_activities(values: list[str]) -> str:
    return " | ".join(values)


def is_sparring_row(row: pd.Series) -> bool:
    session_type = str(row["session_type"]).lower()
    activities = str(row["activities"]).lower()
    sparring = str(row["sparring"]).lower()

    return (
        "sparring" in session_type
        or "sparring" in activities
        or sparring == "yes"
    )


def format_minutes(minutes: float) -> str:
    minutes = float(minutes)

    if minutes <= 0:
        return "0 min"

    if minutes >= 60:
        hours = int(minutes // 60)
        remainder = int(minutes % 60)

        if remainder:
            return f"{hours}h {remainder}m"

        return f"{hours}h"

    return f"{minutes:.0f} min"


def format_boxing_option(index: int, df: pd.DataFrame) -> str:
    row = df.loc[index]
    session_type = str(row["session_type"]).strip() or "Boxing"
    date_label = row["date"].strftime("%Y-%m-%d")
    activities = str(row["activities"]).strip()

    if activities:
        return f"{date_label} — {session_type} — {activities}"

    return f"{date_label} — {session_type}"


def get_consistency_status(weekly_sessions: int) -> tuple[str, str, str]:
    if weekly_sessions >= 4:
        return "happy", "Good", "4+ sessions in the last 7 days"

    if weekly_sessions >= 2:
        return "medium", "Medium", "2–3 sessions in the last 7 days"

    return "sad", "Bad", "0–1 sessions in the last 7 days"


def consistency_face_html(status: str) -> str:
    return f"""
<div class="consistency-face-wrap">
<div class="consistency-face consistency-face-{status}">
<div class="face-eye face-eye-left"></div>
<div class="face-eye face-eye-right"></div>
<div class="face-mouth"></div>
</div>
</div>
"""


def make_sparring_chart(sparring_df: pd.DataFrame) -> go.Figure:
    chart_df = sparring_df.copy()
    chart_df = chart_df.sort_values("date")
    chart_df["date_label"] = chart_df["date"].dt.strftime("%Y-%m-%d")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_df["date_label"],
            y=chart_df["rounds"],
            mode="lines+markers",
            name="Sparring rounds",
            line=dict(width=3, color="#C9A227"),
            marker=dict(size=8, color="#C9A227"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=chart_df["date_label"],
            y=chart_df["feeling_score"],
            mode="lines+markers",
            name="Feeling score",
            line=dict(width=2, color="rgba(245,245,245,0.55)"),
            marker=dict(size=7, color="rgba(245,245,245,0.75)"),
        )
    )

    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=35, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(245,245,245,0.78)"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            title="",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False,
            title="Rounds / score",
            rangemode="tozero",
        ),
    )

    return fig


@st.dialog("Manage boxing entries", width="large")
def boxing_manager_dialog() -> None:
    manage_df = clean_boxing_data(load_boxing_data()).reset_index(drop=True)

    if manage_df.empty:
        st.warning("No boxing entries available.")

        if st.button("Close", use_container_width=True):
            st.session_state.open_boxing_manager = False
            st.query_params.clear()
            st.rerun()

        return

    st.markdown(
        """
<div class="form-section-title">MANAGE BOXING ENTRIES</div>
<div class="form-section-subtitle">Edit or delete logged boxing sessions.</div>
""",
        unsafe_allow_html=True,
    )

    entry_options = list(manage_df.index[::-1])

    selected_index = st.selectbox(
        "Select entry",
        options=entry_options,
        format_func=lambda index: format_boxing_option(index, manage_df),
    )

    selected_row = manage_df.loc[selected_index]
    selected_date = selected_row["date"].date()
    selected_session_type = str(selected_row["session_type"]).strip() or "Boxing training"
    selected_activities = split_activities(selected_row["activities"])
    selected_duration = float(selected_row["duration_min"])
    selected_rounds = int(selected_row["rounds"])
    selected_round_length = float(selected_row["round_length_min"])
    selected_intensity = int(selected_row["intensity"])
    selected_feeling = int(selected_row["feeling_score"])
    selected_focus = str(selected_row["focus"]).strip()
    selected_sparring = str(selected_row["sparring"]).strip() or "No"
    selected_comment = str(selected_row["comment"]).strip()

    if selected_session_type not in SESSION_TYPES:
        selected_session_type = "Other"

    selected_activities = [
        activity for activity in selected_activities
        if activity in ACTIVITY_OPTIONS
    ]

    st.markdown(
        f"""
<div class="selected-entry-card">
<div class="selected-entry-label">SELECTED BOXING ENTRY</div>
<div class="selected-entry-value">{selected_date} — {escape(selected_session_type)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form(f"edit_boxing_entry_{selected_index}"):
        edited_date = st.date_input("Date", value=selected_date)

        edited_session_type = st.selectbox(
            "Session type",
            SESSION_TYPES,
            index=SESSION_TYPES.index(selected_session_type),
        )

        edited_activities = st.multiselect(
            "Activities",
            ACTIVITY_OPTIONS,
            default=selected_activities,
        )

        edited_duration = st.number_input(
            "Duration (min)",
            min_value=0.0,
            max_value=240.0,
            value=selected_duration,
            step=5.0,
        )

        col_rounds, col_round_length = st.columns(2)

        with col_rounds:
            edited_rounds = st.number_input(
                "Sparring rounds",
                min_value=0,
                max_value=30,
                value=selected_rounds,
                step=1,
            )

        with col_round_length:
            edited_round_length = st.number_input(
                "Minutes per round",
                min_value=0.0,
                max_value=10.0,
                value=selected_round_length,
                step=0.5,
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

        edited_sparring = st.selectbox(
            "Sparring?",
            ["No", "Yes"],
            index=1 if selected_sparring == "Yes" else 0,
        )

        edited_focus = st.text_input(
            "Main focus",
            value=selected_focus,
        )

        edited_comment = st.text_area(
            "Comment",
            value=selected_comment,
            height=120,
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
        if edited_session_type == "Sparring" and "Sparring" not in edited_activities:
            edited_activities.append("Sparring")

        if "Sparring" in edited_activities:
            edited_sparring = "Yes"

        update_boxing_entry(
            row_index=selected_index,
            new_date=edited_date,
            new_session_type=edited_session_type,
            new_activities=join_activities(edited_activities),
            new_duration_min=edited_duration,
            new_rounds=edited_rounds,
            new_round_length_min=edited_round_length,
            new_intensity=edited_intensity,
            new_feeling_score=edited_feeling,
            new_focus=edited_focus,
            new_sparring=edited_sparring,
            new_comment=edited_comment,
        )

        st.session_state.open_boxing_manager = False
        st.session_state.save_feedback_message = "Boxing entry updated"
        st.query_params.clear()
        st.rerun()

    if delete_entry:
        delete_boxing_entry(selected_index)
        st.session_state.open_boxing_manager = False
        st.session_state.save_feedback_message = "Boxing entry deleted"
        st.query_params.clear()
        st.rerun()

    if st.button("Close", use_container_width=True):
        st.session_state.open_boxing_manager = False
        st.query_params.clear()
        st.rerun()


show_save_feedback()

st.markdown(
    """
<a class="weight-manage-button" href="/boxing?manage_boxing=true" target="_self" title="Manage boxing entries">
✎
</a>
""",
    unsafe_allow_html=True,
)

boxing_df = clean_boxing_data(load_boxing_data())

today = date.today()
week_start = pd.Timestamp(today - timedelta(days=6))
week_end = pd.Timestamp(today)

if boxing_df.empty:
    week_df = boxing_df.copy()
else:
    week_df = boxing_df[
        (boxing_df["date"] >= week_start) &
        (boxing_df["date"] <= week_end)
    ].copy()

weekly_sessions = len(week_df)
weekly_minutes = float(week_df["duration_min"].sum()) if not week_df.empty else 0.0

consistency_status, consistency_label, consistency_detail = get_consistency_status(
    weekly_sessions=weekly_sessions,
)

if week_df.empty:
    sparring_completed = False
else:
    sparring_completed = week_df.apply(is_sparring_row, axis=1).any()

weekly_sparring_df = (
    week_df[week_df.apply(is_sparring_row, axis=1)].copy()
    if not week_df.empty
    else week_df.copy()
)

weekly_sparring_rounds = (
    int(weekly_sparring_df["rounds"].sum())
    if not weekly_sparring_df.empty
    else 0
)

total_sessions = len(boxing_df)
total_minutes = float(boxing_df["duration_min"].sum()) if not boxing_df.empty else 0.0
average_feeling = float(boxing_df["feeling_score"].mean()) if not boxing_df.empty else 0.0

sparring_df = (
    boxing_df[boxing_df.apply(is_sparring_row, axis=1)].copy()
    if not boxing_df.empty
    else boxing_df.copy()
)

total_sparring_rounds = int(sparring_df["rounds"].sum()) if not sparring_df.empty else 0
sparring_text = "Done" if sparring_completed else "Not yet"

st.markdown(
    f"""
<div class="weight-status-card">
<div class="weight-status-eyebrow">LAST 7 DAYS</div>

<div class="weight-status-grid">
<div>
<div class="status-label">Consistency</div>
<div class="status-value">{consistency_face_html(consistency_status)}</div>
<div class="status-muted">{consistency_label}</div>
</div>

<div>
<div class="status-label">Sessions</div>
<div class="status-value">{weekly_sessions}/4</div>
<div class="status-muted">Last 7 days goal</div>
</div>

<div>
<div class="status-label">Training time</div>
<div class="status-value">{format_minutes(weekly_minutes)}</div>
<div class="status-muted">{consistency_detail}</div>
</div>

<div>
<div class="status-label">Sparring</div>
<div class="status-value">{sparring_text}</div>
<div class="status-muted">{weekly_sparring_rounds} rounds</div>
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
<div class="insight-label">Total training time</div>
<div class="insight-value">{format_minutes(total_minutes)}</div>
</div>

<div class="insight-card">
<div class="insight-label">Average feeling</div>
<div class="insight-value">{average_feeling:.1f}/10</div>
</div>

<div class="insight-card">
<div class="insight-label">Sparring rounds</div>
<div class="insight-value">{total_sparring_rounds}</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

if not boxing_df.empty:
    latest_session = boxing_df.iloc[-1]
    latest_type = str(latest_session["session_type"]).strip() or "Boxing"
    latest_activities = split_activities(latest_session["activities"])
    latest_focus = str(latest_session["focus"]).strip() or "No focus logged"
    latest_comment = str(latest_session["comment"]).strip() or "No comment logged"

    activity_tags = "".join(
        f'<span class="boxing-tag">{escape(activity)}</span>'
        for activity in latest_activities
    )

    st.markdown(
        f"""
<div class="history-card">
<div class="history-eyebrow">LATEST SESSION</div>
<div class="history-title">{escape(latest_type)}</div>
<div class="history-subtitle">{escape(latest_focus)}</div>
<div class="boxing-tag-row">{activity_tags}</div>
<div class="boxing-note-card">
<div class="boxing-note-label">Comment</div>
<div class="boxing-note-text">{escape(latest_comment)}</div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        """
<div class="form-section-title">LOG BOXING SESSION</div>
<div class="form-section-subtitle">Normal boxing days are saved as 90 minutes. Sparring rounds are tracked separately.</div>
""",
        unsafe_allow_html=True,
    )

    form_version = st.session_state.boxing_form_version

    with st.form(f"boxing_session_form_{form_version}"):
        col_date, col_type = st.columns(2)

        with col_date:
            session_date = st.date_input(
                "Date",
                value=today,
                key=f"boxing_date_{form_version}",
            )

        with col_type:
            session_type = st.selectbox(
                "Session type",
                SESSION_TYPES,
                key=f"boxing_type_{form_version}",
            )

        activities = st.multiselect(
            "Activities",
            ACTIVITY_OPTIONS,
            default=["Sparring"] if session_type == "Sparring" else [],
            key=f"boxing_activities_{form_version}",
        )

        st.markdown(
            f"""
<div class="running-pace-preview">
<span>Session duration</span>
<strong>{NORMAL_SESSION_MINUTES:.0f} min</strong>
</div>
""",
            unsafe_allow_html=True,
        )

        col_rounds, col_round_length = st.columns(2)

        with col_rounds:
            rounds = st.number_input(
                "Sparring rounds",
                min_value=0,
                max_value=30,
                value=0,
                step=1,
                help="Use this mainly for Saturday sparring. Leave it at 0 for normal training.",
                key=f"boxing_rounds_{form_version}",
            )

        with col_round_length:
            round_length_min = st.number_input(
                "Minutes per round",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="Use this mainly for sparring rounds.",
                key=f"boxing_round_length_{form_version}",
            )

        col_intensity, col_feeling = st.columns(2)

        with col_intensity:
            intensity = st.slider(
                "Intensity",
                min_value=1,
                max_value=10,
                value=7,
                help="How hard the session was physically.",
                key=f"boxing_intensity_{form_version}",
            )

        with col_feeling:
            feeling_score = st.slider(
                "Feeling score",
                min_value=1,
                max_value=10,
                value=7,
                help="How good you felt technically/mentally/physically.",
                key=f"boxing_feeling_{form_version}",
            )

        focus = st.text_input(
            "Main focus",
            placeholder="Example: jab, defense, footwork, pressure, breathing",
            key=f"boxing_focus_{form_version}",
        )

        comment = st.text_area(
            "What did you do and how did it feel?",
            placeholder=(
                "Example: Mostly pad work and speed drills. Felt sharp early, "
                "but breathing got bad near the end."
            ),
            height=120,
            key=f"boxing_comment_{form_version}",
        )

        submitted = st.form_submit_button(
            "Save boxing session",
            use_container_width=True,
        )

    if submitted:
        if session_type == "Sparring" and "Sparring" not in activities:
            activities.append("Sparring")

        sparring = "Yes" if session_type == "Sparring" or "Sparring" in activities else "No"

        save_boxing_session(
            session_date=session_date,
            session_type=session_type,
            activities=join_activities(activities),
            duration_min=NORMAL_SESSION_MINUTES,
            rounds=rounds,
            round_length_min=round_length_min if rounds > 0 else 0.0,
            intensity=intensity,
            feeling_score=feeling_score,
            focus=focus,
            sparring=sparring,
            comment=comment,
        )

        st.session_state.boxing_form_version += 1
        st.session_state.save_feedback_message = "Boxing session saved"
        st.rerun()

if not sparring_df.empty:
    st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

    st.markdown(
        """
<div class="history-card">
<div class="history-eyebrow">SPARRING PROGRESS</div>
<div class="history-title">Saturday sparring trend</div>
<div class="history-subtitle">Only sparring entries appear here. Use Saturday sparring logs to build the trend.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        make_sparring_chart(sparring_df),
        use_container_width=True,
        key=f"sparring_chart_{len(sparring_df)}_{total_sparring_rounds}",
    )

if not boxing_df.empty:
    history_data = boxing_df.copy()
    history_data["date_label"] = history_data["date"].dt.strftime("%Y-%m-%d")
    history_data = history_data.sort_values("date", ascending=False).head(8)

    history_rows = """
<div class="run-history-row run-history-head">
<div>Date</div>
<div>Type</div>
<div>Activities</div>
<div>Feeling</div>
<div>Comment</div>
</div>
"""

    for _, row in history_data.iterrows():
        date_label = escape(str(row["date_label"]))
        session_type_text = escape(str(row["session_type"]).strip() or "Boxing")
        activities_text = escape(str(row["activities"]).strip() or "—")
        feeling_text = f'{int(row["feeling_score"])}/10'
        comment_text = str(row["comment"]).strip()

        if not comment_text:
            comment_text = "—"

        history_rows += f"""
<div class="run-history-row">
<div class="run-history-value">{date_label}</div>
<div class="run-history-value">{session_type_text}</div>
<div class="run-history-value">{activities_text}</div>
<div class="run-history-value">{feeling_text}</div>
<div class="run-history-comment">{escape(comment_text)}</div>
</div>
"""

    st.markdown(
        f"""
<div class="history-card">
<div class="history-header">
<div>
<div class="history-eyebrow">RECENT BOXING</div>
<div class="history-title">Session history</div>
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
        raw_df = boxing_df.copy()
        raw_df["date"] = raw_df["date"].dt.strftime("%Y-%m-%d")
        raw_df = raw_df.sort_values("date", ascending=False)

        st.dataframe(
            raw_df[
                [
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
            ],
            use_container_width=True,
            hide_index=True,
        )
else:
    st.info("No boxing sessions logged yet. Add your first session above.")

if st.session_state.open_boxing_manager:
    boxing_manager_dialog()

st.markdown("</div>", unsafe_allow_html=True)