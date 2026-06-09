from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.home_button import home_button
from components.page_header import page_header
from utils.calculations import format_pace
from utils.data_loader import (
    delete_run_entry,
    load_runs_data,
    save_run,
    update_run_entry,
)
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Running", eyebrow="ROADWORK TRACKING")
home_button()

if "open_run_manager" not in st.session_state:
    st.session_state.open_run_manager = False

if "run_form_version" not in st.session_state:
    st.session_state.run_form_version = 0

if st.query_params.get("manage_run") == "true":
    st.session_state.open_run_manager = True
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


def format_duration(duration_min: float) -> str:
    minutes = int(duration_min)
    seconds = int(round((duration_min - minutes) * 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}"


def pace_from_row(row: pd.Series) -> float:
    distance = float(row["distance_km"])
    duration = float(row["duration_min"])

    if distance <= 0:
        return 0.0

    return duration / distance


def format_run_option(index: int, df: pd.DataFrame) -> str:
    row = df.loc[index]
    distance = float(row["distance_km"])
    duration = float(row["duration_min"])
    pace = duration / distance if distance > 0 else 0.0

    return (
        f"{row['date'].strftime('%Y-%m-%d')} — "
        f"{distance:.1f} km — "
        f"{format_pace(pace)}"
    )


@st.dialog("Manage run entries", width="large")
def run_manager_dialog() -> None:
    manage_df = load_runs_data().reset_index(drop=True)

    if manage_df.empty:
        st.warning("No run entries available.")

        if st.button("Close", use_container_width=True):
            st.session_state.open_run_manager = False
            st.query_params.clear()
            st.rerun()

        return

    st.markdown(
        """
<div class="form-section-title">MANAGE RUN ENTRIES</div>
<div class="form-section-subtitle">Edit or delete logged roadwork sessions.</div>
""",
        unsafe_allow_html=True,
    )

    entry_options = list(manage_df.index[::-1])

    selected_index = st.selectbox(
        "Select entry",
        options=entry_options,
        format_func=lambda index: format_run_option(index, manage_df),
    )

    selected_row = manage_df.loc[selected_index]
    selected_date = selected_row["date"].date()
    selected_distance = float(selected_row["distance_km"])
    selected_duration = float(selected_row["duration_min"])
    selected_comment = str(selected_row["comment"]).strip()

    selected_pace = (
        selected_duration / selected_distance
        if selected_distance > 0
        else 0.0
    )

    st.markdown(
        f"""
<div class="selected-entry-card">
<div class="selected-entry-label">SELECTED RUN</div>
<div class="selected-entry-value">{selected_date} — {selected_distance:.1f} km — {format_pace(selected_pace)}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form(f"edit_run_entry_{selected_index}"):
        edited_date = st.date_input(
            "Date",
            value=selected_date,
        )

        col_distance, col_duration = st.columns(2)

        with col_distance:
            edited_distance = st.number_input(
                "Distance (km)",
                min_value=0.1,
                max_value=100.0,
                value=selected_distance,
                step=0.1,
            )

        with col_duration:
            edited_duration = st.number_input(
                "Duration (minutes)",
                min_value=1.0,
                max_value=600.0,
                value=selected_duration,
                step=0.1,
            )

        edited_pace = (
            edited_duration / edited_distance
            if edited_distance > 0
            else 0.0
        )

        st.markdown(
            f"""
<div class="running-pace-preview">
<span>Calculated pace</span>
<strong>{format_pace(edited_pace)}</strong>
</div>
""",
            unsafe_allow_html=True,
        )

        edited_comment = st.text_area(
            "Comment",
            value=selected_comment,
            height=90,
        )

        save_changes = st.form_submit_button(
            "Save changes",
            use_container_width=True,
        )

        if save_changes:
            updated = update_run_entry(
                row_index=selected_index,
                new_date=edited_date,
                new_distance_km=edited_distance,
                new_duration_min=edited_duration,
                new_comment=edited_comment,
            )

            if updated:
                st.session_state.open_run_manager = False
                st.query_params.clear()
                st.session_state.save_feedback_message = "Run entry updated"
                st.rerun()
            else:
                st.warning("Could not update entry.")

    st.divider()

    st.warning("Deleting a run is permanent.")

    confirm_delete = st.checkbox("Confirm delete selected run")

    if st.button(
        "Delete selected run",
        use_container_width=True,
        disabled=not confirm_delete,
    ):
        deleted = delete_run_entry(selected_index)

        if deleted:
            st.session_state.open_run_manager = False
            st.query_params.clear()
            st.session_state.save_feedback_message = "Run entry deleted"
            st.rerun()
        else:
            st.warning("Could not delete entry.")

    if st.button("Close", use_container_width=True):
        st.session_state.open_run_manager = False
        st.query_params.clear()
        st.rerun()


if st.session_state.open_run_manager:
    run_manager_dialog()


show_save_feedback()

st.markdown(
    """
<a class="weight-manage-button" href="/running?manage_run=true" target="_self" title="Manage run entries">
✎
</a>
""",
    unsafe_allow_html=True,
)

runs_df = load_runs_data()

if not runs_df.empty:
    runs_df = runs_df.copy()
    runs_df["pace_min_per_km"] = runs_df.apply(pace_from_row, axis=1)
    runs_df = runs_df[runs_df["distance_km"] > 0].reset_index(drop=True)


today = date.today()
week_start = pd.Timestamp(today - timedelta(days=6))
week_end = pd.Timestamp(today)

if runs_df.empty:
    week_df = runs_df.copy()
else:
    week_df = runs_df[
        (runs_df["date"] >= week_start) &
        (runs_df["date"] <= week_end)
    ]

weekly_distance = float(week_df["distance_km"].sum()) if not week_df.empty else 0.0
total_distance = float(runs_df["distance_km"].sum()) if not runs_df.empty else 0.0
total_runs = len(runs_df)
longest_run = float(runs_df["distance_km"].max()) if not runs_df.empty else 0.0

if not runs_df.empty:
    latest_run = runs_df.iloc[-1]
    latest_distance = float(latest_run["distance_km"])
    latest_duration = float(latest_run["duration_min"])
    latest_pace = latest_duration / latest_distance if latest_distance > 0 else 0.0

    average_pace = (
        float(runs_df["duration_min"].sum()) / total_distance
        if total_distance > 0
        else 0.0
    )

    best_pace = float(runs_df["pace_min_per_km"].min())
else:
    latest_distance = 0.0
    latest_duration = 0.0
    latest_pace = 0.0
    average_pace = 0.0
    best_pace = 0.0

latest_pace_text = format_pace(latest_pace) if latest_pace > 0 else "No run"
average_pace_text = format_pace(average_pace) if average_pace > 0 else "No data"
best_pace_text = format_pace(best_pace) if best_pace > 0 else "No data"


# STATUS CARD

st.markdown(
    f"""
<div class="weight-status-card">
<div class="weight-status-eyebrow">CURRENT CONDITIONING</div>

<div class="weight-status-grid">
<div>
<div class="status-label">This week</div>
<div class="status-value">{weekly_distance:.1f} km</div>
<div class="status-muted">Last 7 days</div>
</div>

<div>
<div class="status-label">Latest run</div>
<div class="status-value">{latest_distance:.1f} km</div>
<div class="status-muted">{format_duration(latest_duration) if latest_duration > 0 else "No duration"}</div>
</div>

<div>
<div class="status-label">Latest pace</div>
<div class="status-value">{latest_pace_text}</div>
<div class="status-muted">min/km</div>
</div>

<div>
<div class="status-label">Total runs</div>
<div class="status-value">{total_runs}</div>
<div class="status-muted">Logged sessions</div>
</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# INSIGHTS ROW

st.markdown(
    f"""
<div class="insight-grid">
<div class="insight-card">
<div class="insight-label">Total distance</div>
<div class="insight-value">{total_distance:.1f} km</div>
</div>

<div class="insight-card">
<div class="insight-label">Average pace</div>
<div class="insight-value">{average_pace_text}</div>
</div>

<div class="insight-card">
<div class="insight-label">Best pace</div>
<div class="insight-value">{best_pace_text}</div>
</div>

<div class="insight-card">
<div class="insight-label">Longest run</div>
<div class="insight-value">{longest_run:.1f} km</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# CHARTS

if runs_df.empty:
    st.info("No runs logged yet. Add your first run below.")
else:
    chart_data = runs_df.copy()
    chart_data["date_label"] = chart_data["date"].dt.strftime("%Y-%m-%d")

    x_values = chart_data["date_label"].tolist()
    distance_values = [float(value) for value in chart_data["distance_km"].tolist()]
    pace_values = [float(value) for value in chart_data["pace_min_per_km"].tolist()]

    st.markdown(
        f"""
<div class="chart-header">
<div class="chart-eyebrow">DISTANCE TREND</div>
<div class="chart-summary">{total_distance:.1f} km logged</div>
<div class="chart-detail">Weekly volume builds the engine for boxing.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    distance_fig = go.Figure()

    distance_fig.add_trace(
        go.Scatter(
            x=x_values,
            y=distance_values,
            mode="lines+markers",
            line=dict(
                color="#C9A227",
                width=3,
                shape="spline",
                smoothing=0.7,
            ),
            marker=dict(
                color="#C9A227",
                size=7,
                opacity=0.85,
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{y:.1f} km"
                "<extra></extra>"
            ),
        )
    )

    distance_fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(
            color="#F5F5F5",
            family="Switzer, sans-serif",
        ),
        xaxis=dict(
            title=None,
            type="category",
            showgrid=False,
            tickfont=dict(
                size=12,
                color="rgba(245, 245, 245, 0.85)",
            ),
        ),
        yaxis=dict(
            title=None,
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
            tickfont=dict(
                size=12,
                color="rgba(245, 245, 245, 0.85)",
            ),
        ),
        margin=dict(l=55, r=35, t=35, b=55),
        height=390,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(
                color="#F5F5F5",
                family="Switzer, sans-serif",
            ),
        ),
    )

    st.plotly_chart(
        distance_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.markdown(
        f"""
<div class="chart-header">
<div class="chart-eyebrow">PACE TREND</div>
<div class="chart-summary">Latest pace: {latest_pace_text}</div>
<div class="chart-detail">Lower pace means faster running.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    pace_fig = go.Figure()

    pace_fig.add_trace(
        go.Scatter(
            x=x_values,
            y=pace_values,
            mode="lines+markers",
            line=dict(
                color="#C9A227",
                width=3,
                shape="spline",
                smoothing=0.7,
            ),
            marker=dict(
                color="#C9A227",
                size=7,
                opacity=0.85,
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{y:.2f} min/km"
                "<extra></extra>"
            ),
        )
    )

    pace_y_min = min(pace_values) - 0.25
    pace_y_max = max(pace_values) + 0.25

    pace_fig.update_layout(
        plot_bgcolor="#0B0B0B",
        paper_bgcolor="#0B0B0B",
        font=dict(
            color="#F5F5F5",
            family="Switzer, sans-serif",
        ),
        xaxis=dict(
            title=None,
            type="category",
            showgrid=False,
            tickfont=dict(
                size=12,
                color="rgba(245, 245, 245, 0.85)",
            ),
        ),
        yaxis=dict(
            title=None,
            range=[pace_y_min, pace_y_max],
            gridcolor="rgba(245,245,245,0.07)",
            zeroline=False,
            tickfont=dict(
                size=12,
                color="rgba(245, 245, 245, 0.85)",
            ),
        ),
        margin=dict(l=55, r=35, t=35, b=55),
        height=390,
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#111111",
            bordercolor="#C9A227",
            font=dict(
                color="#F5F5F5",
                family="Switzer, sans-serif",
            ),
        ),
    )

    st.plotly_chart(
        pace_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )


# LOG NEW RUN

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        """
<div class="form-section-title">LOG ROADWORK</div>
<div class="form-section-subtitle">Add a run and let the app calculate your pace.</div>
""",
        unsafe_allow_html=True,
    )

    form_version = st.session_state.run_form_version
    distance_default = latest_distance if latest_distance > 0 else 4.0

    with st.form(f"running_checkin_form_{form_version}"):
        col_date, col_distance, col_duration = st.columns(3)

        with col_date:
            run_date = st.date_input(
                "Date",
                value=today,
                key=f"run_date_{form_version}",
            )

        with col_distance:
            distance_km = st.number_input(
                "Distance (km)",
                min_value=0.1,
                max_value=100.0,
                value=float(distance_default),
                step=0.1,
                key="run_distance_km",
            )

        with col_duration:
            duration_min = st.number_input(
                "Duration (minutes)",
                min_value=1.0,
                max_value=600.0,
                value=None,
                step=0.1,
                placeholder="Enter duration",
                key=f"run_duration_min_{form_version}",
            )

        duration_ready = duration_min is not None and duration_min > 0

        if duration_ready:
            calculated_pace = duration_min / distance_km if distance_km > 0 else 0.0
            pace_preview = format_pace(calculated_pace)
        else:
            pace_preview = "Enter duration"

        st.markdown(
            f"""
<div class="running-pace-preview">
<span>Calculated pace</span>
<strong>{pace_preview}</strong>
</div>
""",
            unsafe_allow_html=True,
        )

        comment = st.text_area(
            "Comment",
            value="",
            placeholder="Example: Felt good. Last kilometer was hard but maintained pace.",
            height=90,
            key=f"run_comment_{form_version}",
        )

        submitted = st.form_submit_button(
    "Save run",
    use_container_width=True,
)

if submitted:
    if duration_min is None or duration_min <= 0:
        st.warning("Enter duration before saving the run.")
    else:
        save_run(
            run_date=run_date,
            distance_km=distance_km,
            duration_min=duration_min,
            comment=comment,
        )
        st.session_state.run_form_version += 1
        st.session_state.save_feedback_message = "Run saved"
        st.rerun()


# RECENT RUNS

if not runs_df.empty:
    history_data = runs_df.copy()
    history_data["date_label"] = history_data["date"].dt.strftime("%Y-%m-%d")
    history_data = history_data.sort_values("date", ascending=False).head(8)

    history_rows = """
<div class="run-history-row run-history-head">
<div>Date</div>
<div>Distance</div>
<div>Duration</div>
<div>Pace</div>
<div>Comment</div>
</div>
"""

    for _, row in history_data.iterrows():
        distance = float(row["distance_km"])
        duration = float(row["duration_min"])
        pace = duration / distance if distance > 0 else 0.0
        comment_text = escape(str(row["comment"]).strip()) or "—"

        history_rows += f"""
<div class="run-history-row">
<div class="run-history-value">{row["date_label"]}</div>
<div class="run-history-value">{distance:.1f} km</div>
<div class="run-history-value">{format_duration(duration)}</div>
<div class="run-history-value">{format_pace(pace)}</div>
<div class="run-history-comment">{comment_text}</div>
</div>
"""

    st.markdown(
        f"""
<div class="history-card">
<div class="history-header">
<div>
<div class="history-eyebrow">RECENT RUNS</div>
<div class="history-title">Roadwork history</div>
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
        raw_df = runs_df.copy()
        raw_df["date"] = raw_df["date"].dt.strftime("%Y-%m-%d")
        raw_df["pace"] = raw_df.apply(
            lambda row: format_pace(row["duration_min"] / row["distance_km"]),
            axis=1,
        )
        raw_df = raw_df.sort_values("date", ascending=False)

        st.dataframe(
            raw_df[["date", "distance_km", "duration_min", "pace", "comment"]],
            use_container_width=True,
            hide_index=True,
        )

st.markdown("</div>", unsafe_allow_html=True)