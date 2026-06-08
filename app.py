import base64

import streamlit as st

from components.metric_card import metric_card
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
from utils.calculations import (
    calculate_weight_change,
    calculate_weekly_run_distance,
    calculate_weekly_boxing_sessions,
    calculate_weekly_gym_sessions,
)
from utils.data_loader import (
    load_weight_data,
    get_latest_weight,
    load_runs_data,
    load_boxing_data,
    load_gym_data,
)
from utils.quote_loader import get_quote_of_the_day
from utils.style_loader import load_css
from utils.date_utils import get_greeting, get_today_label
from components.weekly_overview import weekly_overview
from components.quote_card import quote_card


st.set_page_config(
    page_title="Boxing Journey 2026",
    layout="wide"
)

load_css("assets/styles.css")

st.markdown('<div class="dashboard-wrapper">', unsafe_allow_html=True)

weight_df = load_weight_data()
runs_df = load_runs_data()
boxing_df = load_boxing_data()
gym_df = load_gym_data()

current_weight = get_latest_weight()
weight = f"{current_weight:.1f} kg"
weight_change = calculate_weight_change(weight_df)

weekly_run_distance = calculate_weekly_run_distance(runs_df)
weekly_boxing_sessions = calculate_weekly_boxing_sessions(boxing_df)
weekly_gym_sessions = calculate_weekly_gym_sessions(gym_df)

boxing_card_value = f"{weekly_boxing_sessions} this week"
gym_card_value = f"{weekly_gym_sessions} this week"

boxing_card_note = (
    "Session logged"
    if int(weekly_boxing_sessions) > 0
    else "No session logged"
)

gym_card_note = (
    "Session logged"
    if int(weekly_gym_sessions) > 0
    else "No session logged"
)

quote, author = get_quote_of_the_day()
greeting = get_greeting()
today_label = get_today_label()

with open("assets/logos/boxing_logo_premium.png", "rb") as image:
    logo_base64 = base64.b64encode(image.read()).decode()

skip_splash = st.query_params.get("skip_splash") == "true"

if skip_splash:
    st.session_state.quote_splash_seen = True

if "quote_splash_seen" not in st.session_state:
    st.session_state.quote_splash_seen = False

if not st.session_state.quote_splash_seen:
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

    st.session_state.quote_splash_seen = True

    st.session_state.quote_splash_seen = True

progress = (START_WEIGHT - current_weight) / (START_WEIGHT - GOAL_WEIGHT)
progress = max(0.0, min(progress, 1.0))


st.markdown(
    f"""
<div class="hero-container">
<img class="hero-logo" src="data:image/png;base64,{logo_base64}" alt="Boxing Journey logo">
<div>
<div class="hero-title">{APP_NAME} <span>{APP_YEAR}</span></div>
<div class="hero-subtitle">{greeting}</div>
<div class="hero-date">{today_label}</div>
</div>
</div>
""",
    unsafe_allow_html=True
)

st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)

weekly_overview(
    weight_change,
    weekly_run_distance,
    weekly_boxing_sessions,
    weekly_gym_sessions,
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


col1, spacer1, col2 = st.columns([1, 0.06, 1])

with col1:
    metric_card(
        title="Weight",
        value=weight,
        delta=weight_change,
        icon_path="assets/logos/weight_logo_premium.png",
        page_url="/weight",
    )

with col2:
    metric_card(
        title="Last Run",
        value=DEFAULT_LAST_RUN,
        delta=DEFAULT_LAST_PACE,
        icon_path="assets/logos/running_logo_premium.png",
        page_url="/running",
    )


st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)


col3, spacer2, col4 = st.columns([1, 0.06, 1])

with col3:
    metric_card(
        title="Boxing",
        value=boxing_card_value,
        delta=boxing_card_note,
        icon_path="assets/logos/boxing_logo_premium.png",
        page_url="/boxing",
    )

with col4:
    metric_card(
        title="Gym",
        value=gym_card_value,
        delta=gym_card_note,
        icon_path="assets/logos/gym_logo_premium.png",
        page_url="/gym",
    )


st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


with st.container(border=True):

    st.markdown("### Goal Progress")

    st.caption(
        f"{current_weight:.1f} kg → {GOAL_WEIGHT:.1f} kg"
    )

    st.progress(progress)

    st.markdown(
        f"""
<div class="goal-remaining">
{current_weight - GOAL_WEIGHT:.1f} kg remaining
</div>

<div class="goal-percent">
{progress * 100:.0f}% completed
</div>
""",
        unsafe_allow_html=True,
    )

quote_card(quote, author)


st.markdown('</div>', unsafe_allow_html=True)