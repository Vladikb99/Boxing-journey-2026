import streamlit as st
import plotly.express as px

from utils.data_loader import load_weight_data, save_weight

st.title("⚖️ Weight")

st.markdown(
    """
    <style>
    .block-container {
        max-width: 950px;
        padding-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

weight_df = load_weight_data()
GOAL_WEIGHT = 75

current_weight = weight_df["weight"].iloc[-1]
previous_weight = weight_df["weight"].iloc[-2]
weight_change = current_weight - previous_weight
remaining_kg = current_weight - GOAL_WEIGHT
height_m = 1.84
bmi = current_weight / (height_m ** 2)
START_WEIGHT = 86.7

progress = (START_WEIGHT - current_weight) / (START_WEIGHT - GOAL_WEIGHT)
progress = max(0.0, min(progress, 1.0))

with st.container(border=True):

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Current weight",
        f"{current_weight:.1f} kg",
        delta=f"{weight_change:+.1f} kg",
        delta_color="inverse"
    )
    col2.metric("Goal weight", f"{GOAL_WEIGHT:.0f} kg")
    col3.metric("BMI", f"{bmi:.1f}")
    col4.metric("Remaining", f"{remaining_kg:.1f} kg")

    st.write("### Goal Progress")
    st.progress(progress)
    st.caption(f"{progress * 100:.0f}% completed")




chart_data = weight_df.copy()
chart_data["date"] = chart_data["date"].astype(str)
chart_data = chart_data.sort_values("date")

fig = px.line(
    chart_data,
    x="date",
    y="weight",
    markers=True,
    title=""
)

fig.update_traces(
    line_color="#C9A227",
    marker_color="#C9A227",
    line_width=3,
    marker_size=8
)

fig.add_hline(
    y=GOAL_WEIGHT,
    line_color="#FF3B30",
    line_width=2,
    line_dash="dash",
    annotation_text="Goal (75 kg)",
    annotation_position="top left"
)

fig.update_layout(
    title_text="",
    plot_bgcolor="#0B0B0B",
    paper_bgcolor="#0B0B0B",
    font_color="#F5F5F5",
    xaxis_title="Date",
    yaxis_title="Weight (kg)",
    xaxis_type="category",
    margin=dict(l=20, r=20, t=10, b=20)
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

st.divider()


with st.expander("➕ Add today's weight"):

    new_weight = st.number_input(
        "Weight (kg)",
        min_value=30.0,
        max_value=200.0,
        value=float(current_weight),
        step=0.1
    )

    if st.button("Save"):
        save_weight(new_weight)
        st.success("Weight saved!")
        st.rerun()
with st.expander("📋 Weight History"):

    history_df = weight_df.sort_values(
        "date",
        ascending=False
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )