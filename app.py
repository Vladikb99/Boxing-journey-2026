import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from components.metric_card import metric_card
from components.quote_card import quote_card
from components.weekly_overview import weekly_overview
from config import APP_NAME, APP_YEAR
from utils.calculations import (
    calculate_weight_change,
    calculate_last_7_day_weight_change,
    calculate_weekly_run_distance,
    calculate_weekly_boxing_sessions,
    calculate_weekly_gym_sessions,
    get_latest_run_summary,
)
from utils.data_loader import (
    get_latest_weight,
    load_boxing_data,
    load_gym_data,
    load_runs_data,
    load_weight_data,
)
from utils.date_utils import get_greeting, get_today_label
from utils.quote_loader import get_quote_of_the_day
from utils.settings_loader import load_settings
from utils.style_loader import load_css


st.set_page_config(
    page_title="Boxing Journey 2026",
    layout="wide",
)


def image_to_base64(image_path: str) -> str:
    path = Path(image_path)

    if not path.exists():
        return ""

    return base64.b64encode(path.read_bytes()).decode()


def calculate_goal_progress(start_weight: float, current_weight: float, goal_weight: float) -> float:
    if start_weight == goal_weight:
        return 1.0 if current_weight <= goal_weight else 0.0

    progress = (start_weight - current_weight) / (start_weight - goal_weight)

    return max(0.0, min(progress, 1.0))


def calculate_next_milestone(current_weight: float, goal_weight: float) -> tuple[float, float]:
    if current_weight <= goal_weight:
        return goal_weight, 0.0

    next_milestone = float(int(current_weight))

    if next_milestone >= current_weight:
        next_milestone -= 1

    next_milestone = max(next_milestone, goal_weight)
    milestone_remaining = current_weight - next_milestone

    return next_milestone, milestone_remaining


load_css("assets/styles.css")


# DATA

settings = load_settings()

user_name = settings["user_name"]
goal_weight = float(settings["goal_weight"])
start_weight = float(settings["start_weight"])

weight_df = load_weight_data()
runs_df = load_runs_data()
boxing_df = load_boxing_data()
gym_df = load_gym_data()

current_weight = get_latest_weight()
weight_value = f"{current_weight:.1f} kg"

weight_change = calculate_weight_change(weight_df)
last_7_day_weight_change = calculate_last_7_day_weight_change(weight_df)

last_7_day_run_distance = calculate_weekly_run_distance(runs_df)
last_7_day_boxing_sessions = calculate_weekly_boxing_sessions(boxing_df)
last_7_day_gym_sessions = calculate_weekly_gym_sessions(gym_df)

last_run_value, last_run_delta = get_latest_run_summary(runs_df)

boxing_count = int(last_7_day_boxing_sessions)
gym_count = int(last_7_day_gym_sessions)

boxing_card_value = (
    f"{boxing_count} session"
    if boxing_count == 1
    else f"{boxing_count} sessions"
)

gym_card_value = (
    f"{gym_count} workout"
    if gym_count == 1
    else f"{gym_count} workouts"
)

boxing_card_note = (
    "Last 7 days"
    if boxing_count > 0
    else "No session logged"
)

gym_card_note = (
    "Last 7 days"
    if gym_count > 0
    else "No session logged"
)

quote, author = get_quote_of_the_day()
greeting = get_greeting(user_name)
today_label = get_today_label()

logo_base64 = image_to_base64("assets/logos/boxing_logo_premium.png")

progress = calculate_goal_progress(
    start_weight=start_weight,
    current_weight=current_weight,
    goal_weight=goal_weight,
)

progress_percent = progress * 100
remaining_kg = max(current_weight - goal_weight, 0.0)
next_milestone, milestone_remaining = calculate_next_milestone(
    current_weight=current_weight,
    goal_weight=goal_weight,
)


# QUOTE SPLASH

skip_splash = st.query_params.get("skip_splash") == "true"

if skip_splash:
    st.session_state.quote_splash_seen = True

if "quote_splash_seen" not in st.session_state:
    st.session_state.quote_splash_seen = False

show_quote_splash = not st.session_state.quote_splash_seen

if show_quote_splash:
    st.markdown(
        f"""
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
""",
        unsafe_allow_html=True,
    )

    st.session_state.quote_splash_seen = True

card_wait_class = ""
logo_wait_class = "splash-wait" if show_quote_splash else ""

# PAGE

st.markdown('<div class="dashboard-wrapper">', unsafe_allow_html=True)


# HERO
logo_trace_delay = "3.85s" if show_quote_splash else "0.15s"
countup_delay_ms = 4200 if show_quote_splash else 500

glove_trace_path = """
M 103.6 28.5
L 93.4 33.8
L 86.4 45.5
L 83.1 62.7
L 84.9 79.9
L 80.8 88.8
L 78.9 99.1
L 81.8 102.6
L 112.4 110.6
L 118.0 105.0
L 121.6 94.0
L 121.2 90.4
L 132.5 81.1
L 138.9 73.2
L 142.7 64.5
L 143.4 56.7
L 141.4 52.1
L 135.8 49.1
L 135.5 40.4
L 131.1 35.1
L 114.4 29.4
Z
"""
st.markdown(
    f"""
<div class="hero-container">
<div class="hero-logo-wrap {logo_wait_class}">
<img class="hero-logo" src="data:image/png;base64,{logo_base64}" alt="Boxing Journey logo">

<svg class="hero-logo-trace" viewBox="0 0 220 147" aria-hidden="true">
    <path
        class="hero-trace-path"
        d="{glove_trace_path}"
        pathLength="100"
    />
</svg>
</div>

<div>
<div class="hero-title">{APP_NAME} <span>{APP_YEAR}</span></div>
<div class="hero-subtitle">{greeting}</div>
<div class="hero-date">{today_label}</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="hero-divider"></div>', unsafe_allow_html=True)


# SETTINGS BUTTON

st.markdown(
    """
<a class="settings-button" href="/settings" target="_self" title="Settings">
⚙
</a>
""",
    unsafe_allow_html=True,
)


# LAST 7 DAYS OVERVIEW

weekly_overview(
    last_7_day_weight_change,
    last_7_day_run_distance,
    last_7_day_boxing_sessions,
    last_7_day_gym_sessions,
    animation_class=f"fade-in fade-delay-1 {card_wait_class}",
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# MAIN CARDS

col1, spacer1, col2 = st.columns([1, 0.06, 1])

with col1:
    metric_card(
    title="Weight",
    value=weight_value,
    delta=weight_change,
    page_url="/weight",
    animation_class=f"fade-in fade-delay-2 {card_wait_class}",
)

with col2:
    metric_card(
    title="Run",
    value=last_run_value,
    delta=last_run_delta,
    page_url="/running",
    animation_class=f"fade-in fade-delay-2 {card_wait_class}",
)

st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

col3, spacer2, col4 = st.columns([1, 0.06, 1])

with col3:
    metric_card(
    title="Boxing",
    value=boxing_card_value,
    delta=boxing_card_note,
    page_url="/boxing",
    animation_class=f"fade-in fade-delay-3 {card_wait_class}",
)

with col4:
    metric_card(
    title="Gym",
    value=gym_card_value,
    delta=gym_card_note,
    page_url="/gym",
    animation_class=f"fade-in fade-delay-3 {card_wait_class}",
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# GOAL CARD

st.markdown(
    f"""
<div class="home-goal-card fade-in fade-delay-4 {card_wait_class}">
<div class="home-goal-eyebrow">GOAL PROGRESS</div>

<div class="home-goal-grid">
<div>
<div class="home-goal-label">Current</div>
<div class="home-goal-value">{current_weight:.1f} kg</div>
</div>

<div>
<div class="home-goal-label">Goal</div>
<div class="home-goal-value">{goal_weight:.1f} kg</div>
</div>

<div>
<div class="home-goal-label">Remaining</div>
<div class="home-goal-value">{remaining_kg:.1f} kg</div>
</div>

<div>
<div class="home-goal-label">Next milestone</div>
<div class="home-goal-value">{next_milestone:.1f} kg</div>
<div class="home-goal-muted">{milestone_remaining:.1f} kg away</div>
</div>
</div>

<div class="home-goal-progress-top">
<span>{progress_percent:.0f}% completed</span>
<span>{current_weight:.1f} kg → {goal_weight:.1f} kg</span>
</div>

<div class="home-goal-progress-track">
<div class="home-goal-progress-fill" style="width: {progress_percent:.0f}%;"></div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)


# QUOTE

quote_card(
    quote,
    author,
    animation_class=f"fade-in fade-delay-5 {card_wait_class}",
)

components.html(
    f"""
<script>
(function () {{
    function parseValue(text) {{
        const match = text.match(/-?\\d+(?:[.,]\\d+)?/);

        if (!match) {{
            return null;
        }}

        const numberText = match[0].replace(",", ".");
        const finalValue = parseFloat(numberText);

        if (Number.isNaN(finalValue)) {{
            return null;
        }}

        const decimals = numberText.includes(".")
            ? numberText.split(".")[1].length
            : 0;

        return {{
            finalValue: finalValue,
            decimals: decimals,
            prefix: text.slice(0, match.index),
            suffix: text.slice(match.index + match[0].length)
        }};
    }}

    function animateNumber(element) {{
        if (element.dataset.counted === "true") {{
            return;
        }}

        const originalText = element.dataset.final || element.textContent.trim();
        const parsed = parseValue(originalText);

        if (!parsed) {{
            return;
        }}

        element.dataset.counted = "true";

        const duration = 900;
        const startTime = performance.now();

        function easeOutCubic(t) {{
            return 1 - Math.pow(1 - t, 3);
        }}

        function frame(now) {{
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = easeOutCubic(progress);

            const currentValue = parsed.finalValue * easedProgress;
            const formattedValue = currentValue.toFixed(parsed.decimals);

            element.textContent = parsed.prefix + formattedValue + parsed.suffix;

            if (progress < 1) {{
                requestAnimationFrame(frame);
            }} else {{
                element.textContent = originalText;
            }}
        }}

        element.textContent =
            parsed.prefix +
            (0).toFixed(parsed.decimals) +
            parsed.suffix;

        requestAnimationFrame(frame);
    }}

    function runCountUp() {{
        const parentDocument = window.parent.document;
        const numbers = parentDocument.querySelectorAll(".count-up-number");
        numbers.forEach(animateNumber);
    }}

    setTimeout(runCountUp, {countup_delay_ms});
}})();
</script>
""",
    height=0,
)

st.markdown("</div>", unsafe_allow_html=True)