import base64

import streamlit as st

from config import (
    APP_NAME,
    APP_YEAR,
    GOAL_WEIGHT,
    START_WEIGHT,
    DEFAULT_LAST_RUN,
    DEFAULT_LAST_PACE,
    DEFAULT_BOXING_SESSIONS,
    DEFAULT_BOXING_NOTE,
    DEFAULT_GYM_SESSIONS,
    DEFAULT_GYM_NOTE,
)
from utils.calculations import calculate_weight_change
from utils.data_loader import load_weight_data, get_latest_weight
from utils.quote_loader import get_quote_of_the_day
from utils.style_loader import load_css


st.set_page_config(
    page_title="Boxing Journey 2026",
    layout="wide"
)

load_css("assets/styles.css")

st.markdown('<div class="dashboard-wrapper">', unsafe_allow_html=True)

weight_df = load_weight_data()

current_weight = get_latest_weight()
weight = f"{current_weight:.1f} kg"
weight_change = calculate_weight_change(weight_df)

quote, author = get_quote_of_the_day()

with open("assets/logos/boxing_logo_premium.png", "rb") as image:
    logo_base64 = base64.b64encode(image.read()).decode()

st.markdown(f"""
<div class="quote-splash">
    <div class="quote-splash-content">
        <div class="quote-splash-text">
            ❝ {quote} ❞
        </div>
        <div class="quote-splash-author">
            — {author}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

progress = (START_WEIGHT - current_weight) / (START_WEIGHT - GOAL_WEIGHT)
progress = max(0.0, min(progress, 1.0))


def metric_card(label, value, delta, delta_color="normal"):
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


st.markdown(
    f"""
<div class="hero-container">
<img class="hero-logo" src="data:image/png;base64,{logo_base64}" alt="Boxing Journey logo">
<div>
<div class="hero-title">{APP_NAME} <span>{APP_YEAR}</span></div>
<div class="hero-subtitle">Welcome back, Vladik.</div>
</div>
</div>
""",
    unsafe_allow_html=True
)

st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)


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
        value=DEFAULT_LAST_RUN,
        delta=DEFAULT_LAST_PACE,
        delta_color="inverse"
    )


col3, col4 = st.columns(2)

with col3:
    metric_card(
        label="Boxing",
        value=DEFAULT_BOXING_SESSIONS,
        delta=DEFAULT_BOXING_NOTE
    )

with col4:
    metric_card(
        label="Gym",
        value=DEFAULT_GYM_SESSIONS,
        delta=DEFAULT_GYM_NOTE
    )


with st.container(border=True):
    st.write("### Goal Progress")
    st.caption(f"{current_weight:.1f} kg → {GOAL_WEIGHT:.1f} kg")
    st.progress(progress)
    st.caption(
        f"{progress * 100:.0f}% completed • "
        f"{current_weight - GOAL_WEIGHT:.1f} kg remaining"
    )


with st.container(border=True):
    st.markdown(f"""
    <div class="quote-card">
        <div class="quote-text">
            ❝ {quote} ❞
        </div>
        <div class="quote-author">
            — {author}
        </div>
    </div>
    """, unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)