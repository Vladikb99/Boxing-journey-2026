import streamlit as st
from utils.data_loader import load_weight_data, get_latest_weight
from utils.calculations import calculate_weight_change

st.set_page_config(
    page_title="Boxing Journey 2026",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://api.fontshare.com/v2/css?f[]=switzer@400,500,600,700&display=swap');

html, body, [class*="css"], * {
    font-family: 'Switzer', sans-serif !important;
}

.hero-title {
    font-family: 'Switzer', sans-serif !important;
    font-size: 44px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #F5F5F5;
    margin-bottom: 0px;
    line-height: 1.1;
}

.hero-title span {
    color: #C9A227;
}

.hero-subtitle {
    font-family: 'Switzer', sans-serif !important;
    font-size: 16px;
    color: #A0A0A0;
    margin-bottom: 28px;
}

div[data-testid="stMetric"] {
    background-color: #111111;
    border: 1px solid rgba(201, 162, 39, 0.35);
    border-radius: 14px;
    padding: 18px;
}
            
 .quote-card {
    padding: 10px 4px;
}

.quote-text {
    font-size: 24px;
    font-weight: 500;
    font-style: italic;
    color: #F5F5F5;
    margin-bottom: 10px;
}

.quote-author {
    font-size: 14px;
    color: #C9A227;
}           
</style>
""", unsafe_allow_html=True)

weight_df = load_weight_data()

weight = f"{get_latest_weight()} kg"
weight_change = calculate_weight_change(weight_df)

GOAL_WEIGHT = 75
START_WEIGHT = 86.7

current_weight = get_latest_weight()
progress = (START_WEIGHT - current_weight) / (START_WEIGHT - GOAL_WEIGHT)
progress = max(0.0, min(progress, 1.0))

last_run = "4 km"
last_pace = "5:27/km"

boxing_sessions = "0 this week"
boxing_note = "No session logged"

gym_sessions = "0 this week"
gym_note = "No session logged"


def metric_card(label, value, delta, delta_color="normal"):
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


st.markdown("""
<div class="hero-title">
    BOXING JOURNEY <span>2026</span>
</div>
<div class="hero-subtitle">
    Welcome back, Vladik.
</div>
""", unsafe_allow_html=True)


col1, col2 = st.columns(2)

with col1:
    metric_card(
        label="Weight",
        value=weight,
        delta=weight_change,
        delta_color="inverse"
    )

with col2:
    metric_card(
        label="Last Run",
        value=last_run,
        delta=last_pace,
        delta_color="inverse"
    )

col3, col4 = st.columns(2)

with col3:
    metric_card("Boxing", boxing_sessions, boxing_note)

with col4:
    metric_card("Gym", gym_sessions, gym_note)


with st.container(border=True):
    st.write("### Goal Progress")
    st.caption(f"{current_weight:.1f} kg → {GOAL_WEIGHT:.1f} kg")
    st.progress(progress)
    st.caption(f"{progress * 100:.0f}% completed • {current_weight - GOAL_WEIGHT:.1f} kg remaining")

with st.container(border=True):
    st.markdown("""
    <div class="quote-card">
        <div class="quote-text">"Discipline beats motivation."</div>
        <div class="quote-author">— Unknown</div>
    </div>
    """, unsafe_allow_html=True)