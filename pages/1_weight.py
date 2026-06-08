import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.home_button import home_button
from components.page_header import page_header
from utils.settings_loader import load_settings
from utils.data_loader import load_weight_data, save_weight, delete_latest_weight
from utils.style_loader import load_css


load_css("assets/styles.css")

page_header(title="Weight")
home_button()

st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)

weight_df = load_weight_data()

settings = load_settings()

GOAL_WEIGHT = settings["goal_weight"]
START_WEIGHT = settings["start_weight"]
HEIGHT_M = settings["height_m"]

if weight_df.empty:
    st.warning("No weight data found yet.")

    with st.expander("➕ Add today's weight", expanded=True):
        new_weight = st.number_input(
            "Weight (kg)",
            min_value=30.0,
            max_value=200.0,
            value=85.0,
            step=0.1,
        )

        if st.button("Save"):
            save_weight(new_weight)
            st.success("Weight saved!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


current_weight = float(weight_df["weight_kg"].iloc[-1])
start_weight = float(weight_df["weight_kg"].iloc[0])

if len(weight_df) >= 2:
    previous_weight = float(weight_df["weight_kg"].iloc[-2])
    weight_change = current_weight - previous_weight
    weight_change_text = f"{weight_change:+.1f} kg"
else:
    weight_change = 0.0
    weight_change_text = "No previous data"

remaining_kg = current_weight - GOAL_WEIGHT
bmi = current_weight / (HEIGHT_M ** 2)

progress = (START_WEIGHT - current_weight) / (START_WEIGHT - GOAL_WEIGHT)
progress = max(0.0, min(progress, 1.0))

total_change = current_weight - start_weight

first_date = weight_df["date"].iloc[0].date()
latest_date_raw = weight_df["date"].iloc[-1].date()
days_between = max((latest_date_raw - first_date).days, 1)
average_daily_change = total_change / days_between

days_logged = len(weight_df)

progress_percent = progress * 100


# PREMIUM STATUS CARD

st.markdown(
    f"""
<div class="weight-status-card">
<div class="weight-status-eyebrow">CURRENT STATUS</div>

<div class="weight-status-grid">
<div>
<div class="status-label">Current weight</div>
<div class="status-value">{current_weight:.1f} kg</div>
<div class="status-pill">{weight_change_text}</div>
</div>

<div>
<div class="status-label">Goal weight</div>
<div class="status-value">{GOAL_WEIGHT:.0f} kg</div>
<div class="status-muted">Target weight</div>
</div>

<div>
<div class="status-label">BMI</div>
<div class="status-value">{bmi:.1f}</div>
<div class="status-muted">Based on {HEIGHT_M:.2f} m</div>
</div>

<div>
<div class="status-label">Remaining</div>
<div class="status-value">{remaining_kg:.1f} kg</div>
<div class="status-muted">Until goal</div>
</div>
</div>

<div class="status-progress-section">
<div class="status-progress-top">
<span>Goal Progress</span>
<span>{progress_percent:.0f}%</span>
</div>

<div class="status-progress-track">
<div class="status-progress-fill" style="width: {progress_percent:.0f}%;"></div>
</div>

<div class="status-progress-bottom">
{current_weight:.1f} kg → {GOAL_WEIGHT:.1f} kg
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
<div class="insight-label">Days logged</div>
<div class="insight-value">{days_logged}</div>
</div>

<div class="insight-card">
<div class="insight-label">Total change</div>
<div class="insight-value">{total_change:+.1f} kg</div>
</div>

<div class="insight-card">
<div class="insight-label">Average / day</div>
<div class="insight-value">{average_daily_change:+.2f} kg</div>
</div>

<div class="insight-card">
<div class="insight-label">Remaining</div>
<div class="insight-value">{remaining_kg:.1f} kg</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)


# CHART

chart_data = weight_df.copy()
chart_data["date_label"] = chart_data["date"].dt.strftime("%Y-%m-%d")

x_values = chart_data["date_label"].tolist()
y_values = [float(value) for value in chart_data["weight_kg"].tolist()]

start_date = x_values[0]
latest_date = x_values[-1]
latest_weight = y_values[-1]

y_min = min(y_values) - 0.4
y_max = max(y_values) + 0.4

hover_data = []

for index, weight_value in enumerate(y_values):
    remaining = weight_value - GOAL_WEIGHT

    if index == 0:
        change_text = "Start"
    else:
        change = weight_value - y_values[index - 1]
        change_text = f"{change:+.1f} kg from previous"

    hover_data.append(
        [
            change_text,
            f"{remaining:.1f} kg remaining",
        ]
    )


st.markdown(
    f"""
<div class="chart-header">
<div class="chart-eyebrow">WEIGHT TREND</div>
<div class="chart-summary">{start_weight:.1f} kg → {latest_weight:.1f} kg</div>
<div class="chart-detail">{total_change:+.1f} kg since start</div>
</div>
""",
    unsafe_allow_html=True,
)


fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x_values,
        y=y_values,
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
        customdata=hover_data,
        hovertemplate=(
            "%{x}<br>"
            "%{y:.1f} kg<br>"
            "%{customdata[0]}<br>"
            "%{customdata[1]}"
            "<extra></extra>"
        ),
    )
)

fig.add_trace(
    go.Scatter(
        x=[start_date],
        y=[start_weight],
        mode="markers",
        marker=dict(
            color="#0B0B0B",
            size=12,
            line=dict(
                color="#C9A227",
                width=2,
            ),
        ),
        hovertemplate=(
            "Start<br>"
            f"{start_date}<br>"
            f"{start_weight:.1f} kg"
            "<extra></extra>"
        ),
    )
)

fig.add_trace(
    go.Scatter(
        x=[latest_date],
        y=[latest_weight],
        mode="markers",
        marker=dict(
            color="#C9A227",
            size=14,
            line=dict(
                color="#F5F5F5",
                width=2,
            ),
        ),
        hovertemplate=(
            "Latest<br>"
            f"{latest_date}<br>"
            f"{latest_weight:.1f} kg"
            "<extra></extra>"
        ),
    )
)

fig.add_annotation(
    x=latest_date,
    y=latest_weight,
    text=f"{latest_weight:.1f} kg",
    showarrow=True,
    arrowhead=2,
    arrowcolor="#C9A227",
    arrowwidth=1.4,
    ax=34,
    ay=-30,
    font=dict(
        color="#F5F5F5",
        size=13,
    ),
    bgcolor="rgba(11, 11, 11, 0.92)",
    bordercolor="rgba(201, 162, 39, 0.55)",
    borderwidth=1,
    borderpad=5,
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
        type="category",
        showgrid=False,
        tickangle=0,
        tickfont=dict(
            size=12,
            color="rgba(245, 245, 245, 0.85)",
        ),
    ),
    yaxis=dict(
        title=None,
        range=[y_min, y_max],
        gridcolor="rgba(245,245,245,0.07)",
        zeroline=False,
        tickfont=dict(
            size=12,
            color="rgba(245, 245, 245, 0.85)",
        ),
    ),
    margin=dict(l=55, r=35, t=35, b=55),
    height=430,
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
    fig,
    use_container_width=True,
    config={"displayModeBar": False},
)


# CHECK-IN

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(
        """
<div class="form-section-title">TODAY'S CHECK-IN</div>
<div class="form-section-subtitle">Log your morning weight.</div>
""",
        unsafe_allow_html=True,
    )

    with st.form("weight_checkin_form"):
        col_input, col_button = st.columns([0.72, 0.28])

        with col_input:
            new_weight = st.number_input(
                "Weight (kg)",
                min_value=30.0,
                max_value=200.0,
                value=float(current_weight),
                step=0.1,
            )

        with col_button:
            st.write("")
            st.write("")
            submitted = st.form_submit_button(
                "Save weight",
                use_container_width=True,
            )

        if submitted:
            save_weight(new_weight)
            st.success("Weight saved!")
            st.rerun()


# RECENT ENTRIES

history_data = weight_df.copy()
history_data["date_label"] = history_data["date"].dt.strftime("%Y-%m-%d")
history_data["change"] = history_data["weight_kg"].diff()
history_data = history_data.sort_values("date", ascending=False).head(8)

history_rows = ""

for _, row in history_data.iterrows():
    change_value = row["change"]

    if pd.isna(change_value):
        change_text = "Start"
        change_class = "neutral"
    else:
        change_text = f"{change_value:+.1f} kg"

        if change_value < 0:
            change_class = "loss"
        elif change_value > 0:
            change_class = "gain"
        else:
            change_class = "neutral"

    history_rows += f"""
<div class="history-row">
<div class="history-date">{row["date_label"]}</div>
<div class="history-weight">{row["weight_kg"]:.1f} kg</div>
<div class="history-change {change_class}">{change_text}</div>
</div>
"""


st.markdown(
    f"""
<div class="history-card">
<div class="history-header">
<div>
<div class="history-eyebrow">RECENT ENTRIES</div>
<div class="history-title">Weight history</div>
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
    raw_df = weight_df.copy()
    raw_df["date"] = raw_df["date"].dt.strftime("%Y-%m-%d")
    raw_df = raw_df.sort_values("date", ascending=False)

    st.dataframe(
        raw_df,
        use_container_width=True,
        hide_index=True,
    )


st.markdown("</div>", unsafe_allow_html=True)